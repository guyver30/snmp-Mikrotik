# Deployment: two NanoPi R28S (Debian trixie, ARM64)

Concrete runbook for this specific setup. Both boards run `monitor.py --headless`
(independent SNMP polling + their own CSV logs) plus an always-on iperf3 server;
only one board runs the periodic iperf3 client test schedule.

| Board  | IP            | User | Role                                    |
|--------|---------------|------|------------------------------------------|
| r28s-a | 192.168.1.90  | pi   | SNMP polling + iperf3 server + **iperf3 client schedule** (target: r28s-b) |
| r28s-b | 192.168.1.91  | pi   | SNMP polling + iperf3 server only        |

Both boards need SNMP (UDP/161) reachability to the MikroTik master AP at
`192.168.1.80`. Verify before trusting the systemd units:

```bash
snmpget -v2c -c public 192.168.1.80 .1.3.6.1.4.1.14988.1.1.1.8.1.12.3
```

Log retention: 14 days (`snmp-mikrotik-cleanup.timer`), ~5–7 MB/day/board —
trivial against the 28GB free on the SD card. See "Changing log retention" below
if you ever want to adjust it.

## r28s-a (192.168.1.90) — iperf3 client schedule

From your dev machine:

```bash
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  /home/kone/claude_projects/snmp-Mikrotik/ pi@192.168.1.90:~/snmp-mikrotik/
ssh pi@192.168.1.90
```

On the board:

```bash
sudo apt update && sudo apt install -y iperf3
cd ~/snmp-mikrotik && uv sync
timedatectl status | grep synchronized     # should say "yes"

sudo mkdir -p /var/log/snmp-mikrotik && sudo chown pi:pi /var/log/snmp-mikrotik
sudo mkdir -p /etc/snmp-mikrotik
sudo cp deploy/snmp-mikrotik.env.example /etc/snmp-mikrotik/env
sudo sed -i 's/^IPERF_TARGET=$/IPERF_TARGET=192.168.1.91/' /etc/snmp-mikrotik/env

sed -i "s/REPLACE_WITH_YOUR_USERNAME/pi/g; s#REPLACE_WITH_UV_ABS_PATH#$(command -v uv)#g" \
  deploy/snmp-mikrotik.service
sudo cp deploy/snmp-mikrotik.service /etc/systemd/system/
sudo cp deploy/iperf3-server.service /etc/systemd/system/
sudo cp deploy/snmp-mikrotik-cleanup.service deploy/snmp-mikrotik-cleanup.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now iperf3-server.service
sudo systemctl enable --now snmp-mikrotik.service
sudo systemctl enable --now snmp-mikrotik-cleanup.timer

sudo systemctl status snmp-mikrotik.service iperf3-server.service
journalctl -u snmp-mikrotik -f
```

## r28s-b (192.168.1.91) — server only, no client schedule

From your dev machine:

```bash
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  /home/kone/claude_projects/snmp-Mikrotik/ pi@192.168.1.91:~/snmp-mikrotik/
ssh pi@192.168.1.91
```

On the board — identical to r28s-a **except leave `IPERF_TARGET=` blank**
(skip the `sed` line that sets it):

```bash
sudo apt update && sudo apt install -y iperf3
cd ~/snmp-mikrotik && uv sync
timedatectl status | grep synchronized

sudo mkdir -p /var/log/snmp-mikrotik && sudo chown pi:pi /var/log/snmp-mikrotik
sudo mkdir -p /etc/snmp-mikrotik
sudo cp deploy/snmp-mikrotik.env.example /etc/snmp-mikrotik/env   # IPERF_TARGET stays blank

sed -i "s/REPLACE_WITH_YOUR_USERNAME/pi/g; s#REPLACE_WITH_UV_ABS_PATH#$(command -v uv)#g" \
  deploy/snmp-mikrotik.service
sudo cp deploy/snmp-mikrotik.service /etc/systemd/system/
sudo cp deploy/iperf3-server.service /etc/systemd/system/
sudo cp deploy/snmp-mikrotik-cleanup.service deploy/snmp-mikrotik-cleanup.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now iperf3-server.service
sudo systemctl enable --now snmp-mikrotik.service
sudo systemctl enable --now snmp-mikrotik-cleanup.timer
```

## Verifying it worked

On either board, after a minute or two:

```bash
tail -f /var/log/snmp-mikrotik/link_log_*.csv     # per-poll SNMP data, snmp_ok column
cat /var/log/snmp-mikrotik/events.csv             # monitor_start, snmp_down/recovered, etc.
```

Expect `monitor_start` in `events.csv` on both boards, and `snmp_ok=True` rows in
`link_log` once SNMP reachability to `192.168.1.80` is confirmed from each board's
actual network position.

## Changing log retention

Edit the `-mtime +14` value in `/etc/systemd/system/snmp-mikrotik-cleanup.service`
(and the copy in `deploy/` if you want the repo to stay in sync), then:

```bash
sudo systemctl daemon-reload
```

No need to touch `snmp-mikrotik-cleanup.timer` — it only controls the daily
trigger, not the retention window. `events.csv` is excluded from cleanup on
purpose (see comment in the unit file) — it's meant to persist indefinitely.

## Resilience to a peer reboot

- SNMP polling on each board is independent of the peer board's state — it
  polls the MikroTik AP directly, not the peer.
- `iperf3-server.service` (`Restart=always`) comes back automatically on
  reboot or crash, independent of `snmp-mikrotik.service`.
- If r28s-b is down when r28s-a's scheduled iperf3 client test fires, the
  failure is logged as `iperf3_unreachable` in `events.csv` and retried every
  5 minutes (`IPERF_RETRY_SEC`) until it succeeds, then resumes the normal
  hourly schedule and logs `iperf3_recovered`.
- A deliberate `systemctl stop` or reboot logs `monitor_stop` in `events.csv`
  before exiting. A hard power loss can't log anything gracefully — it shows
  up as a gap between the last data row's timestamp and the next
  `monitor_start`.
