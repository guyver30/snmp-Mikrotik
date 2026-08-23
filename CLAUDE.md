# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

A real-time SNMP monitoring tool for a MikroTik wAP 60G (RBwAPG-60ad) point-to-point 60GHz wireless link. It polls both ends of the link via SNMP every 2.5 seconds, logs metrics to CSV, and renders a live 3-panel matplotlib chart.

- **Master** (AP mode): `192.168.1.80`, interface index 3 (`wlan60-1`)
- **Slave** (station mode): `192.168.1.81`, interface index 5 (`wlan60-station-1`)
- **All OIDs are polled from the master** — the AP exposes both its own stats (`mtxrWl60GTable`) and the connected station's stats (`mtxrWl60GStaTable`, ifTable index 5) in a single SNMP agent. Only a host with SNMP (UDP/161) reachability to the master needs to run the poller; a peer host only needs `iperf3 -s`.
- **SNMP community**: `public` (read-only)
- **Log files**, all written to `LOG_DIR` (default: cwd):
  - `link_log_<run-timestamp>.csv` / `iperf_log_<run-timestamp>.csv` — fresh files on every process start, not appended across restarts. `link_log` includes an `snmp_ok` column (bool) so a poll failure reads as unambiguous, distinct from a genuine 0 reading.
  - `events.csv` — single append-only file across restarts: `monitor_start`/`monitor_stop` and `snmp_down`/`snmp_recovered`/`iperf3_unreachable`/`iperf3_recovered` transition events, for explaining gaps/anomalies in the per-poll data on a dashboard.

## Running the monitor

```bash
# Normal monitoring with live matplotlib GUI (runs indefinitely)
uv run --extra gui monitor.py

# Headless — no GUI deps required, poll/log/iperf3 only, status on stdout
uv run monitor.py --headless

# Stability test — auto-stops after N minutes
uv run monitor.py --headless --duration 60
```

The monitor measures actual bidirectional throughput from SNMP octet counters (`ifInOctets`/`ifOutOctets` on interface 5), not from iperf3 output. iperf3 is used separately for saturating bidir throughput/retransmit tests — see `IPERF_TARGET` below and `deploy/` for the two-host systemd setup.

**iperf3 client console logging** (`_run_iperf_client` in `monitor.py`): each test prints a `[iperf3] starting test to ...` line, a `[iperf3] ... still running (Ns/1800s)...` line once a minute for the duration of the test (via a `Popen` + `communicate(timeout=60)` polling loop, not a single blocking `subprocess.run`), and finally either a `succeeded: fwd=...Mbps rev=...Mbps` line or a `failed: ...` line to stderr. On failure, the logged error includes iperf3's actual `stderr` text (e.g. "unable to connect to server"), not just the subprocess exit code — this is what makes `journalctl -u snmp-mikrotik` useful for diagnosing a bad test without needing to reproduce it manually.

### Environment variable overrides

`MASTER_IP`, `SLAVE_IP`, `COMMUNITY`, `IPERF_TARGET`, and `LOG_DIR` are Python constants at the top of `monitor.py`, each overridable via env var (`SNMP_MASTER_IP`, `SNMP_SLAVE_IP`, `SNMP_COMMUNITY`, `IPERF_TARGET`, `LOG_DIR`) so the same checkout can run unmodified on multiple hosts with per-host config supplied by systemd `EnvironmentFile`. See `deploy/snmp-mikrotik.env.example`.

## Dependencies

- `pysnmp` 7.x (uses `pysnmp.hlapi.v3arch` — the hybrid async API, not the old `pysnmp.hlapi` sync API)
- `pandas`, `numpy` — core, always installed
- `matplotlib` — optional (`gui` extra in `pyproject.toml`); only needed when running without `--headless`
- `iperf3` binary on PATH — the client side (`maybe_launch_iperf`) is invoked from this script; the server side is a separate systemd unit (`deploy/iperf3-server.service`), not started by `monitor.py`

## OID layout

All MikroTik-specific OIDs are under `.1.3.6.1.4.1.14988`. The two 60GHz tables used in `monitor.py`:

| Prefix in code | SNMP table | Interface index |
|---|---|---|
| `m_` | `mtxrWl60GTable` (`.1.3.6.1.4.1.14988.1.1.1.8`) | `.3` (AP) |
| `s_` | `mtxrWl60GStaTable` (`.1.3.6.1.4.1.14988.1.1.1.9`) | `.5` (station) |

Error counters (`rx_err`, `tx_err`) come from standard `ifTable` (`.1.3.6.1.2.1.2.2.1.14/20`). PHY rate (`phy_rate`) is `.1.3.6.1.4.1.14988.1.1.1.9.1.8.5` (Gauge32, Mbps).

The full OID reference for both devices is in `SNMP_OID_Map_MikroTik_wAP60G.md`.

## Chart layout

3×8 GridSpec layout (`height_ratios=[1.1, 1.0, 1.0]`):

- **Row 0, cols 0-3** (`ax_rssi`): Master & Slave RSSI (dBm), autoscaled line chart
- **Row 0, cols 4-7** (`ax_qual`): Master & Slave Signal Quality (%), autoscaled line chart
- **Row 1, cols 0-7** (`ax_tput`): TX Mbps (master→slave) & RX Mbps (slave→master), derived from ifInOctets/ifOutOctets deltas
- **Row 2, cols 0-1** (`ax_mcs`): Semicircle gauge — MCS index (Master), range 0–9
- **Row 2, cols 2-3** (`ax_phy`): Semicircle gauge — PHY rate (Mbps), range 0–4620
- **Row 2, cols 4-5** (`ax_errs`): Text panel — cumulative error counters + delta per poll
- **Row 2, cols 6-7** (`ax_dist`): Semicircle gauge — Distance in metres (`raw/100`), range 3–240 m

## Deployment (two NanoPi R28S, headless)

`deploy/DEPLOY.md` is the concrete runbook (actual IPs/username) for the current two-board setup. `deploy/` also holds the systemd units themselves, generic/reusable:

- `iperf3-server.service` — bare `iperf3 -s`, `Restart=always`, independent of `monitor.py`'s lifecycle — install and enable on **both** boxes.
- `snmp-mikrotik.service` — runs `uv run monitor.py --headless`, `Restart=on-failure`, config via `EnvironmentFile=/etc/snmp-mikrotik/env`
- `snmp-mikrotik.env.example` — per-host env template (`LOG_DIR`, `IPERF_TARGET`, etc.)
- `snmp-mikrotik-cleanup.service` + `.timer` — daily deletion of `*.csv` (except `events.csv`) older than 14 days from `LOG_DIR`

Both boxes run the identical `snmp-mikrotik.service` and codebase; only their `/etc/snmp-mikrotik/env` differs. Set `IPERF_TARGET` on only one of the two boxes — both always run the `iperf3-server` unit, but only one should run the periodic saturating client tests to avoid two simultaneous bidir tests colliding.

### Networking (eth0 to MikroTik, eth1 to laptop)

Each board has two NICs on separate subnets: `eth0` (`192.168.1.0/24`) reaches the MikroTik devices and the other board; `eth1` (`192.168.2.0/24`) is for direct laptop access. `deploy/DEPLOY.md` has the concrete `nmcli` static IP config plus IP forwarding + NAT/masquerade setup (via `nftables`) so a laptop plugged into `eth1` can reach both MikroTik devices and the other board over `eth0` without any config changes on those devices.

### Resilience to a peer reboot

- **SNMP polling** is unaffected by the peer box rebooting — each box polls the MikroTik AP directly, not the peer. A poll failure (AP unreachable, or the peer box itself down if it were somehow the poll target) sets `snmp_ok=False` in that row and logs an `snmp_down` event; a following successful poll logs `snmp_recovered`.
- **iperf3 server**: `Restart=always` in its own unit means it comes back automatically whenever the box (re)boots or the process dies, independent of `monitor.py`.
- **iperf3 client** (the box with `IPERF_TARGET` set): a failed test against a rebooted/unreachable peer logs an `iperf3_unreachable` event and switches to a 5-minute retry cadence (`IPERF_RETRY_SEC`) instead of waiting the full hourly `IPERF_INTERVAL_SEC` — so it picks the peer back up shortly after it returns. The first successful test after a failure logs `iperf3_recovered` and resumes the normal hourly schedule.
- **The box's own process**: `Restart=on-failure` handles a `monitor.py` crash. A `SIGTERM` (from `systemctl stop` or a reboot) is caught and logs a `monitor_stop` event before exiting, so a deliberate stop is distinguishable in `events.csv` from a hard power loss — the latter just shows as a gap between the last per-poll row and the next `monitor_start`.

## pysnmp 7.x API note

This version uses the **async** API: `from pysnmp.hlapi.v3arch.asyncio import ...`. `UdpTransportTarget` must be constructed via `await UdpTransportTarget.create((ip, 161))`, and `get_cmd` must be `await`-ed. All 11 OIDs are fetched concurrently with `asyncio.gather` inside `poll_all()`, which is called from the synchronous matplotlib `update()` via `asyncio.run()`.
