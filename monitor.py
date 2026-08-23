import os
import sys
import csv
import json
import signal
import time as _time
import asyncio
import argparse
import subprocess
import threading
import atexit

import numpy as np
import pandas as pd

from pysnmp.hlapi.v3arch.asyncio import (
    get_cmd, SnmpEngine, CommunityData, UdpTransportTarget,
    ContextData, ObjectType, ObjectIdentity
)

# --- CLI (parsed early so --headless can gate the matplotlib import below) ---

parser = argparse.ArgumentParser(description='MikroTik wAP 60G link stability monitor')
parser.add_argument('--duration', type=int, default=0,
                    help='Test duration in minutes (0 = run indefinitely)')
parser.add_argument('--headless', action='store_true',
                    help='Run without the matplotlib GUI — poll/log/iperf3 only, status printed to console')
args = parser.parse_args()

if not args.headless:
    import matplotlib
    matplotlib.use('TkAgg')   # explicit backend — change to Qt5Agg or GTK3Agg if TkAgg missing
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    import matplotlib.dates as mdates
    from matplotlib.animation import FuncAnimation
    from matplotlib.widgets import RadioButtons

# --- CONFIGURATION ---
# All overridable via environment variables so the same checkout can run on
# multiple hosts (e.g. two R28S units) with per-host config supplied by systemd.
MASTER_IP      = os.environ.get('SNMP_MASTER_IP', '192.168.1.80')
SLAVE_IP       = os.environ.get('SNMP_SLAVE_IP', '192.168.1.81')
COMMUNITY      = os.environ.get('SNMP_COMMUNITY', 'public')
POLL_INTERVAL  = 2.5   # seconds

# iperf3 — set IPERF_TARGET to the far-end R28S's IP to enable periodic client tests.
# A local iperf3 server is always started so the far side can test against this box too.
# Dedicated test link, no live traffic to protect — long saturating runs are fine here;
# the gap between tests still gives an unloaded baseline to compare error rates against.
IPERF_TARGET            = os.environ.get('IPERF_TARGET') or None   # e.g. '192.168.1.82'
IPERF_SERVER_PORT       = 5201
IPERF_INTERVAL_SEC      = 3600   # gap between client tests (1 hour)
IPERF_RETRY_SEC         = 300    # faster retry cadence while the target is unreachable (5 min)
IPERF_TEST_DURATION_SEC = 1800   # length of each test — saturates the link while running (30 min)
IPERF_BIDIR             = True   # simultaneous both-directions saturation (`iperf3 --bidir`)

# Directory for CSV logs — defaults to cwd, override for a fixed deployment path.
LOG_DIR = os.environ.get('LOG_DIR', '.')

OIDS = {
    'm_rssi':    '.1.3.6.1.4.1.14988.1.1.1.8.1.12.3',
    'm_quality': '.1.3.6.1.4.1.14988.1.1.1.8.1.8.3',
    'm_mcs':     '.1.3.6.1.4.1.14988.1.1.1.8.1.7.3',
    'm_rx_err':  '.1.3.6.1.2.1.2.2.1.14.3',
    'm_tx_err':  '.1.3.6.1.2.1.2.2.1.20.3',
    'm_in_oct':  '.1.3.6.1.2.1.2.2.1.10.5',   # ifInOctets  — wlan60-station-1 (over-the-air RX)
    'm_out_oct': '.1.3.6.1.2.1.2.2.1.16.5',   # ifOutOctets — wlan60-station-1 (over-the-air TX)
    's_rssi':    '.1.3.6.1.4.1.14988.1.1.1.9.1.9.5',
    's_quality': '.1.3.6.1.4.1.14988.1.1.1.9.1.5.5',
    's_mcs':     '.1.3.6.1.4.1.14988.1.1.1.9.1.4.5',
    's_rx_err':  '.1.3.6.1.2.1.2.2.1.14.5',
    's_tx_err':  '.1.3.6.1.2.1.2.2.1.20.5',
    'distance':  '.1.3.6.1.4.1.14988.1.1.1.9.1.10.5',
    'phy_rate':  '.1.3.6.1.4.1.14988.1.1.1.9.1.8.5',
}

# --- SNMP ---

async def _snmp_get(ip, oid):
    """Returns (value, ok) — ok=False on any timeout/error so callers can tell
    a genuine 0 reading apart from an unreachable/failed poll."""
    try:
        transport = await UdpTransportTarget.create((ip, 161), timeout=1, retries=0)
        error_indication, error_status, _, var_binds = await get_cmd(
            SnmpEngine(),
            CommunityData(COMMUNITY),
            transport,
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        if error_indication or error_status:
            return 0, False
        val = var_binds[0][1]
        return (int(val) if val else 0), True
    except Exception as e:
        print(f"[SNMP] {ip} {oid}: {type(e).__name__}: {e}", file=sys.stderr)
        return 0, False

async def _poll_all():
    tasks = [_snmp_get(MASTER_IP, oid) for oid in OIDS.values()]
    results = await asyncio.gather(*tasks)
    snmp = {k: v for k, (v, _ok) in zip(OIDS.keys(), results)}
    ok = all(_ok for _, _ok in results)
    return snmp, ok

def poll_all():
    """Returns (snmp_dict, ok) — ok is False if any OID failed this poll."""
    return asyncio.run(_poll_all())

_snmp_last_ok = None   # None = unknown (no poll yet)

def poll_all_and_track():
    """poll_all() plus an events.csv entry on snmp_down/snmp_recovered transitions."""
    global _snmp_last_ok
    snmp, ok = poll_all()
    if ok and _snmp_last_ok is False:
        log_event('snmp_recovered', f'{MASTER_IP} reachable again')
    elif not ok and _snmp_last_ok is not False:
        log_event('snmp_down', f'{MASTER_IP} unreachable or incomplete SNMP response')
    _snmp_last_ok = ok
    return snmp, ok

# --- DERIVED METRICS ---

_prev_snmp = {}
_prev_poll_ts = None

def compute_derived(snmp):
    global _prev_snmp, _prev_poll_ts
    now = _time.monotonic()
    if _prev_snmp:
        elapsed = now - _prev_poll_ts if _prev_poll_ts else POLL_INTERVAL

        def delta32(cur, prev):
            d = cur - prev
            return d + 2**32 if d < 0 else d

        tx_bytes = delta32(snmp['m_out_oct'], _prev_snmp['m_out_oct'])
        rx_bytes = delta32(snmp['m_in_oct'],  _prev_snmp['m_in_oct'])
        derived = {
            'tx_mbps':   round(tx_bytes * 8 / elapsed / 1e6, 2),
            'rx_mbps':   round(rx_bytes * 8 / elapsed / 1e6, 2),
            'dm_tx_err': int(snmp['m_tx_err'] - _prev_snmp['m_tx_err']),
            'dm_rx_err': int(snmp['m_rx_err'] - _prev_snmp['m_rx_err']),
            'ds_tx_err': int(snmp['s_tx_err'] - _prev_snmp['s_tx_err']),
            'ds_rx_err': int(snmp['s_rx_err'] - _prev_snmp['s_rx_err']),
        }
    else:
        derived = {'tx_mbps': 0, 'rx_mbps': 0,
                   'dm_tx_err': 0, 'dm_rx_err': 0,
                   'ds_tx_err': 0, 'ds_rx_err': 0}
    _prev_snmp = snmp.copy()
    _prev_poll_ts = now
    return derived

# --- IPERF3 ---
# The iperf3 *server* is no longer started by this script — it's run as its
# own systemd unit (deploy/iperf3-server.service, Restart=always) so it stays
# up independently of this process's crashes/restarts. Only the periodic
# client-side test schedule lives here.

_iperf_thread   = None
_last_iperf_run = 0.0
_iperf_lock     = threading.Lock()
_iperf_last_ok  = None   # None = unknown (no test run yet)

def _run_iperf_client():
    global _iperf_last_ok
    row = {'time': pd.Timestamp.now(), 'target': IPERF_TARGET,
           'duration_sec': IPERF_TEST_DURATION_SEC, 'bidir': IPERF_BIDIR,
           'fwd_mbps': '', 'fwd_retransmits': '',
           'rev_mbps': '', 'rev_retransmits': '', 'error': ''}
    cmd = ['iperf3', '-c', IPERF_TARGET, '-p', str(IPERF_SERVER_PORT),
           '-t', str(IPERF_TEST_DURATION_SEC), '-J']
    if IPERF_BIDIR:
        cmd.append('--bidir')
    ok = False
    print(f'[iperf3] starting test to {IPERF_TARGET} '
          f'({IPERF_TEST_DURATION_SEC}s, bidir={IPERF_BIDIR})...')
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=IPERF_TEST_DURATION_SEC + 15, check=True)
        data = json.loads(result.stdout)
        end  = data['end']
        # Forward = client -> server. sum_received is goodput measured at the
        # receiving end (excludes retransmit overhead); sum_sent carries the
        # sender-side retransmit count.
        row['fwd_mbps']        = round(end['sum_received']['bits_per_second'] / 1e6, 2)
        row['fwd_retransmits'] = end['sum_sent'].get('retransmits', 0)
        if IPERF_BIDIR:
            # Reverse = server -> client, reported under the *_bidir_reverse keys.
            row['rev_mbps']        = round(end['sum_received_bidir_reverse']['bits_per_second'] / 1e6, 2)
            row['rev_retransmits'] = end['sum_sent_bidir_reverse'].get('retransmits', 0)
        ok = True
        print(f'[iperf3] test to {IPERF_TARGET} succeeded: '
              f'fwd={row["fwd_mbps"]}Mbps rev={row["rev_mbps"]}Mbps')
    except subprocess.CalledProcessError as e:
        # e's default str() only shows the exit code — the actual reason
        # (e.g. "unable to connect to server") is in stderr, so surface it.
        row['error'] = f'{type(e).__name__}: exit {e.returncode}: {e.stderr.strip()}'
        print(f'[iperf3] test to {IPERF_TARGET} failed: {row["error"]}', file=sys.stderr)
    except Exception as e:
        row['error'] = f'{type(e).__name__}: {e}'
        print(f'[iperf3] test to {IPERF_TARGET} failed: {row["error"]}', file=sys.stderr)

    if ok and _iperf_last_ok is False:
        log_event('iperf3_recovered', f'test to {IPERF_TARGET} succeeded again')
    elif not ok and _iperf_last_ok is not False:
        log_event('iperf3_unreachable', f'test to {IPERF_TARGET} failed: {row["error"]}')
    _iperf_last_ok = ok

    with _iperf_lock, open(IPERF_LOG_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=IPERF_HEADER).writerow(row)

def maybe_launch_iperf():
    """Call once per poll tick. Fires a background client test at most every
    IPERF_INTERVAL_SEC normally, but retries at the shorter IPERF_RETRY_SEC
    cadence while the target is known unreachable, so a rebooted peer gets
    picked back up quickly instead of waiting up to an hour."""
    global _last_iperf_run, _iperf_thread
    if not IPERF_TARGET:
        return
    now = _time.monotonic()
    interval = IPERF_RETRY_SEC if _iperf_last_ok is False else IPERF_INTERVAL_SEC
    if now - _last_iperf_run < interval:
        return
    if _iperf_thread and _iperf_thread.is_alive():
        return
    _last_iperf_run = now
    _iperf_thread = threading.Thread(target=_run_iperf_client, daemon=True)
    _iperf_thread.start()

# --- DRAWING ---

def draw_gauge(ax, value, vmin, vmax, title, unit='', color='#00aaff'):
    ax.cla()
    ax.set_aspect('equal')
    ax.axis('off')

    frac = max(0.0, min(1.0, (value - vmin) / max(vmax - vmin, 1)))
    r_out, r_in = 1.0, 0.55
    theta_bg = np.linspace(np.pi, 0, 200)
    x_bg = np.concatenate([r_out * np.cos(theta_bg), r_in * np.cos(theta_bg[::-1])])
    y_bg = np.concatenate([r_out * np.sin(theta_bg), r_in * np.sin(theta_bg[::-1])])
    ax.fill(x_bg, y_bg, color='#2a2a2a', zorder=1)

    if frac > 0:
        theta_v = np.linspace(np.pi, np.pi * (1 - frac), max(2, int(200 * frac)))
        x_v = np.concatenate([r_out * np.cos(theta_v), r_in * np.cos(theta_v[::-1])])
        y_v = np.concatenate([r_out * np.sin(theta_v), r_in * np.sin(theta_v[::-1])])
        ax.fill(x_v, y_v, color=color, zorder=2, alpha=0.9)

    needle_angle = np.pi * (1 - frac)
    ax.plot([0, 0.72 * np.cos(needle_angle)], [0, 0.72 * np.sin(needle_angle)],
            color='white', linewidth=2.5, zorder=3, solid_capstyle='round')
    ax.plot(0, 0, 'o', color='white', markersize=7, zorder=4)

    ax.text(0, -0.18, f'{value:.0f} {unit}', ha='center', va='top',
            fontsize=13, fontweight='bold', color='white', zorder=5)
    ax.text(0, 0.28, title, ha='center', va='center',
            fontsize=9, color='#aaaaaa', zorder=5)
    ax.text(-1.1, 0.0, str(vmin), ha='center', fontsize=7, color='#777777')
    ax.text( 1.1, 0.0, str(vmax), ha='center', fontsize=7, color='#777777')
    ax.set_xlim(-1.35, 1.35)
    ax.set_ylim(-0.55, 1.25)

def draw_errors(ax, m_tx, m_rx, s_tx, s_rx, dm_tx, dm_rx, ds_tx, ds_rx):
    ax.cla()
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor('#1c1c1c')
    for spine in ax.spines.values():
        spine.set_color('#444444')

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(0.5, 0.95, 'Error Counters', ha='center', va='top', fontsize=9, color='#aaaaaa')

    entries = [
        ('M TX Err', m_tx, dm_tx, '#ff6666'),
        ('M RX Err', m_rx, dm_rx, '#ffaa66'),
        ('S TX Err', s_tx, ds_tx, '#66aaff'),
        ('S RX Err', s_rx, ds_rx, '#66ddff'),
    ]
    for i, (lbl, total, delta, color) in enumerate(entries):
        y = 0.74 - i * 0.19
        ax.text(0.05, y, lbl, fontsize=9, color='#888888', va='center')
        ax.text(0.95, y, f'{int(total)}  (+{int(delta)})', fontsize=10,
                fontweight='bold', color=color, va='center', ha='right')

# --- LOG FILE ---

os.makedirs(LOG_DIR, exist_ok=True)

# Shared, append-only across restarts (unlike the timestamped files below) —
# the narrative record of start/stop/disconnect/recover events for a dashboard
# to explain gaps or anomalies in the per-poll data.
EVENTS_LOG_FILE = os.path.join(LOG_DIR, 'events.csv')
EVENTS_HEADER   = ['time', 'event', 'detail']
_events_lock    = threading.Lock()

if not os.path.exists(EVENTS_LOG_FILE):
    with open(EVENTS_LOG_FILE, 'w', newline='') as f:
        csv.DictWriter(f, fieldnames=EVENTS_HEADER).writeheader()

def log_event(event, detail=''):
    with _events_lock, open(EVENTS_LOG_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=EVENTS_HEADER).writerow(
            {'time': pd.Timestamp.now(), 'event': event, 'detail': detail})
    print(f'[event] {event}: {detail}')

run_ts   = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
LOG_FILE = os.path.join(LOG_DIR, f'link_log_{run_ts}.csv')

SNMP_COLS    = list(OIDS.keys())
DERIVED_COLS = ['tx_mbps', 'rx_mbps', 'dm_tx_err', 'dm_rx_err', 'ds_tx_err', 'ds_rx_err']
HEADER       = ['time'] + SNMP_COLS + ['snmp_ok'] + DERIVED_COLS

with open(LOG_FILE, 'w', newline='') as f:
    csv.DictWriter(f, fieldnames=HEADER).writeheader()

IPERF_LOG_FILE = os.path.join(LOG_DIR, f'iperf_log_{run_ts}.csv')
IPERF_HEADER   = ['time', 'target', 'duration_sec', 'bidir',
                  'fwd_mbps', 'fwd_retransmits', 'rev_mbps', 'rev_retransmits', 'error']

with open(IPERF_LOG_FILE, 'w', newline='') as f:
    csv.DictWriter(f, fieldnames=IPERF_HEADER).writeheader()

print(f'Logging to {LOG_FILE}')
if args.duration:
    print(f'Test duration: {args.duration} min')

start_time = pd.Timestamp.now()

# SIGTERM has no default Python handler (unlike SIGINT), so without this,
# `systemctl stop` / reboot would kill the process without running atexit —
# no graceful monitor_stop event, and the dashboard would just see a silent gap.
signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))
atexit.register(lambda: log_event('monitor_stop', 'process exiting'))

log_event('monitor_start',
          f'headless={args.headless} iperf_target={IPERF_TARGET or "none"}')

if IPERF_TARGET:
    mode = 'bidir' if IPERF_BIDIR else 'one-way'
    print(f'[iperf3] {mode} client tests to {IPERF_TARGET} every {IPERF_INTERVAL_SEC}s '
          f'({IPERF_TEST_DURATION_SEC}s each, retry every {IPERF_RETRY_SEC}s while unreachable), '
          f'logged to {IPERF_LOG_FILE}')
else:
    print('[iperf3] IPERF_TARGET not set — client tests disabled '
          '(server is managed by the iperf3-server systemd unit, not this script)')

if args.headless:
    def run_headless():
        while True:
            if args.duration > 0:
                elapsed_min = (pd.Timestamp.now() - start_time).total_seconds() / 60
                if elapsed_min >= args.duration:
                    print(f'\nTest complete ({args.duration} min). Log saved to {LOG_FILE}')
                    break

            snmp, snmp_ok = poll_all_and_track()
            derived = compute_derived(snmp)
            row     = {'time': pd.Timestamp.now(), **snmp, 'snmp_ok': snmp_ok, **derived}
            with open(LOG_FILE, 'a', newline='') as f:
                csv.DictWriter(f, fieldnames=HEADER).writerow(row)

            print(f"{row['time']:%H:%M:%S}  "
                  f"RSSI m/s={snmp['m_rssi']}/{snmp['s_rssi']}dBm  "
                  f"Qual m/s={snmp['m_quality']}/{snmp['s_quality']}%  "
                  f"TX/RX={derived['tx_mbps']}/{derived['rx_mbps']}Mbps  "
                  f"Err m={derived['dm_tx_err']+derived['dm_rx_err']} "
                  f"s={derived['ds_tx_err']+derived['ds_rx_err']}")

            maybe_launch_iperf()
            _time.sleep(POLL_INTERVAL)

    run_headless()
    sys.exit(0)

# --- HISTORY WINDOW ---

HISTORY_OPTIONS = {'5m': 5, '10m': 10, '30m': 30, '1h': 60, '12h': 720, '24h': 1440}
history_minutes = 5

# --- LAYOUT ---

plt.style.use('dark_background')
fig = plt.figure(figsize=(15, 10))
fig.patch.set_facecolor('#111111')
fig.suptitle('MikroTik wAP 60G  |  Link Monitor', fontsize=13, color='#cccccc', y=0.99)

gs = gridspec.GridSpec(3, 8, figure=fig,
                       height_ratios=[1.1, 1.0, 1.0],
                       hspace=0.55, wspace=0.6,
                       left=0.06, right=0.88, top=0.94, bottom=0.06)

ax_rssi  = fig.add_subplot(gs[0, :4])
ax_qual  = fig.add_subplot(gs[0, 4:])
ax_tput       = fig.add_subplot(gs[1, :6])
ax_tput_stats = fig.add_subplot(gs[1, 6:])
ax_mcs   = fig.add_subplot(gs[2, :2])
ax_phy   = fig.add_subplot(gs[2, 2:4])
ax_errs  = fig.add_subplot(gs[2, 4:6])
ax_dist  = fig.add_subplot(gs[2, 6:])

ax_radio = fig.add_axes([0.895, 0.28, 0.09, 0.42], facecolor='#1c1c1c')
ax_radio.set_title('History', fontsize=8, color='#aaaaaa', pad=6)
radio = RadioButtons(ax_radio, list(HISTORY_OPTIONS.keys()), active=0,
                     label_props={'color': ['#cccccc'] * 6, 'fontsize': [9] * 6},
                     radio_props={'facecolor': ['#00aaff'] * 6})

def on_history_change(label):
    global history_minutes
    history_minutes = HISTORY_OPTIONS[label]

radio.on_clicked(on_history_change)

# --- UPDATE LOOP ---

def update(frame):
    # Auto-stop after --duration minutes
    if args.duration > 0:
        elapsed_min = (pd.Timestamp.now() - start_time).total_seconds() / 60
        if elapsed_min >= args.duration:
            print(f'\nTest complete ({args.duration} min). Log saved to {LOG_FILE}')
            ani.event_source.stop()
            plt.close()
            return

    snmp, snmp_ok = poll_all_and_track()
    derived = compute_derived(snmp)
    row     = {'time': pd.Timestamp.now(), **snmp, 'snmp_ok': snmp_ok, **derived}

    with open(LOG_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=HEADER).writerow(row)

    maybe_launch_iperf()

    df_full = pd.read_csv(LOG_FILE, parse_dates=['time'])
    cutoff = pd.Timestamp.now() - pd.Timedelta(minutes=history_minutes)
    df = df_full[df_full['time'] >= cutoff]
    if len(df) < 2:
        return

    t   = df['time']
    fmt = mdates.DateFormatter('%H:%M:%S')

    def style_chart(ax, title, ylabel):
        ax.set_facecolor('#1c1c1c')
        ax.set_title(title, fontsize=10, color='#aaaaaa', pad=4)
        ax.set_ylabel(ylabel, fontsize=8, color='#777777')
        ax.legend(fontsize=8, loc='upper left')
        ax.xaxis.set_major_formatter(fmt)
        ax.tick_params(axis='x', labelsize=7, rotation=20)
        ax.autoscale(axis='y')

    # RSSI
    ax_rssi.cla()
    ax_rssi.plot(t, df['m_rssi'], label='Master', color='#00dd88', linewidth=1.8)
    ax_rssi.plot(t, df['s_rssi'], label='Slave',  color='#00aaff', linewidth=1.8, linestyle='--')
    style_chart(ax_rssi, 'RSSI (dBm)', 'dBm')

    # Signal Quality
    ax_qual.cla()
    ax_qual.plot(t, df['m_quality'], label='Master', color='#ffaa00', linewidth=1.8)
    ax_qual.plot(t, df['s_quality'], label='Slave',  color='#ff6688', linewidth=1.8, linestyle='--')
    style_chart(ax_qual, 'Signal Quality (%)', '%')

    # Throughput TX / RX
    ax_tput.cla()
    ax_tput.plot(t, df['tx_mbps'], label='TX (master→slave)', color='#ff9900', linewidth=1.8)
    ax_tput.plot(t, df['rx_mbps'], label='RX (slave→master)', color='#cc44ff', linewidth=1.8, linestyle='--')
    style_chart(ax_tput, 'Throughput (Mbps)', 'Mbps')

    # Throughput stats panel
    valid = df_full[df_full['tx_mbps'] > 0]
    cutoff_10s = pd.Timestamp.now() - pd.Timedelta(seconds=10)
    df_10s = valid[valid['time'] >= cutoff_10s]

    cur_tx    = df['tx_mbps'].iloc[-1]
    cur_rx    = df['rx_mbps'].iloc[-1]
    avg10_tx  = df_10s['tx_mbps'].mean()  if len(df_10s) > 0 else 0.0
    avg10_rx  = df_10s['rx_mbps'].mean()  if len(df_10s) > 0 else 0.0
    avgtot_tx = valid['tx_mbps'].mean()   if len(valid)  > 0 else 0.0
    avgtot_rx = valid['rx_mbps'].mean()   if len(valid)  > 0 else 0.0

    ax_tput_stats.cla()
    ax_tput_stats.set_facecolor('#1c1c1c')
    ax_tput_stats.axis('off')
    ax_tput_stats.set_title('Stats', fontsize=10, color='#aaaaaa', pad=4)

    labels = ['Tx/Rx current :', 'Tx/Rx 10s avg :', 'Tx/Rx total avg :']
    values = [
        f'{cur_tx:.0f} / {cur_rx:.0f} Mbps',
        f'{avg10_tx:.0f} / {avg10_rx:.0f} Mbps',
        f'{avgtot_tx:.0f} / {avgtot_rx:.0f} Mbps',
    ]
    colors = ['#ff9900', '#ffcc66', '#aaaaaa']
    for i, (lbl, val, col) in enumerate(zip(labels, values, colors)):
        y = 0.72 - i * 0.28
        ax_tput_stats.text(0.05, y,        lbl, fontsize=9,  color='#777777',
                           transform=ax_tput_stats.transAxes, va='center')
        ax_tput_stats.text(0.05, y - 0.10, val, fontsize=10, color=col,
                           transform=ax_tput_stats.transAxes, va='center', fontweight='bold')

    # Gauges
    draw_gauge(ax_mcs,  int(df['m_mcs'].iloc[-1]),       0,    9, 'MCS Index',  '',    '#aa66ff')
    draw_gauge(ax_phy,  df['phy_rate'].iloc[-1],          0, 4620, 'PHY Rate',   'Mbps','#ff9900')
    draw_gauge(ax_dist, df['distance'].iloc[-1] / 100.0,  3,  240, 'Distance',   'm',   '#00ccff')

    # Error panel — cumulative total + delta per poll
    draw_errors(ax_errs,
                m_tx=df['m_tx_err'].iloc[-1], m_rx=df['m_rx_err'].iloc[-1],
                s_tx=df['s_tx_err'].iloc[-1], s_rx=df['s_rx_err'].iloc[-1],
                dm_tx=df['dm_tx_err'].iloc[-1], dm_rx=df['dm_rx_err'].iloc[-1],
                ds_tx=df['ds_tx_err'].iloc[-1], ds_rx=df['ds_rx_err'].iloc[-1])

ani = FuncAnimation(fig, update, interval=int(POLL_INTERVAL * 1000), cache_frame_data=False)
plt.show()
