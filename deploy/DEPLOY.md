# Deployment: two NanoPi R28S (Debian trixie, ARM64)

Concrete runbook for this specific setup. Both boards run `monitor.py --headless`
(independent SNMP polling + their own CSV logs) plus an always-on iperf3 server;
only one board runs the periodic iperf3 client test schedule.

| Board  | IP            | User | Role                                    |
|--------|---------------|------|------------------------------------------|
| r28s-a | 192.168.1.90  | pi   | SNMP polling + iperf3 server + **iperf3 client schedule** (target: r28s-b) |
| r28s-b | 192.168.1.91  | pi   | SNMP polling + iperf3 server only        |

Both boards need SNMP (UDP/161) reachability to the MikroTik master AP at
`192.168.1.80`. Verify before trusting the systemd units — `snmpget` isn't
installed by default, it's the `snmp` package (`apt install -y snmp`,
included in each board's install step below):

```bash
snmpget -v2c -c public 192.168.1.80 .1.3.6.1.4.1.14988.1.1.1.8.1.12.3
```

Log retention: 14 days (`snmp-mikrotik-cleanup.timer`), ~5–7 MB/day/board —
trivial against the 28GB free on the SD card. See "Changing log retention" below
if you ever want to adjust it.

## Networking overview: eth0 to MikroTik, eth1 to laptop

Each board has two NICs, ending up on separate static subnets with no
default gateway on either — **once configured, the board has no internet
access**, so any step needing apt/PyPI (installing `iperf3`, `uv sync`) must
happen *before* the network reconfiguration, while the board still has its
original DHCP address with internet access. This is why each per-board
section below does installs first, network changes second.

| Interface | Connects to        | Subnet          | r28s-a IP      | r28s-b IP      |
|-----------|---------------------|-----------------|----------------|----------------|
| `eth0`    | MikroTik devices    | `192.168.1.0/24`| `192.168.1.90` | `192.168.1.91` |
| `eth1`    | Laptop (direct/NIC) | `192.168.2.0/24`| `192.168.2.90` | `192.168.2.91` |

This setup uses **NAT/masquerade** from `eth1` to `eth0`: the laptop's
traffic to the MikroTik devices and to the other board appears to originate
from the R28S's own `eth0` address, so **no route changes are needed on the
MikroTik devices or the other R28S**. The laptop still addresses the real
device IPs directly (e.g. `ssh pi@192.168.1.91`, Winbox to `192.168.1.80`) —
only the return path is NAT'd.

Networking is managed by **NetworkManager** (`nmcli`) on this image. The
default connection profile names don't match the interface names (`eth0`'s
profile is typically called `Wired connection 1`, and `eth1` often has no
profile at all until a cable is plugged in) — so rename/create profiles
explicitly rather than assuming `nmcli connection modify eth0` will work.

### Checking link speed

Both R28S ports should negotiate gigabit. Use `ethtool`, not `nmcli`, to
check the actual negotiated speed:

```bash
sudo ethtool eth0 | grep -E "Speed|Duplex|Supported link modes" -A1
```

Expect `Speed: 1000Mb/s`, `Duplex: Full`, and `1000baseT/Full` listed under
`Supported link modes` — if `1000baseT/Full` isn't listed at all, that port
is hardware-limited to 100M; if it's listed but `Speed` still shows 100Mb/s,
suspect the cable or the switch/hub port on the other end.

`nmcli device show eth0`'s `GENERAL.STATE: 100 (connected)` field is **not**
a link speed — it's NetworkManager's internal connection-state code (0–100,
where 100 means "fully activated"). It's easy to misread as "100 Mbps"; it
isn't related to negotiated speed at all.

## r28s-a (192.168.1.90) — iperf3 client schedule

### 1. Copy the project (while the board still has internet via DHCP)

**From Linux/macOS dev machine (rsync):**

```bash
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  /home/kone/claude_projects/snmp-Mikrotik/ pi@<r28s-a-dhcp-ip>:~/snmp-mikrotik/
ssh pi@<r28s-a-dhcp-ip>
```

**From a Windows machine (no rsync) — clone straight from GitHub instead:**

The repo is public at `https://github.com/guyver30/snmp-Mikrotik`, so the
simplest path is to skip copying files from Windows entirely and clone
directly on the board:

```bash
ssh pi@<r28s-a-dhcp-ip>
git clone https://github.com/guyver30/snmp-Mikrotik.git ~/snmp-mikrotik
cd ~/snmp-mikrotik
```

If you have local edits not yet pushed to GitHub, use `scp` from PowerShell
instead (Windows 10 1809+ ships an OpenSSH client with `scp` built in —
no extra install needed). `scp` has no `--exclude`, so remove `.venv`
first if it exists locally:

```powershell
scp -r C:\path\to\snmp-Mikrotik pi@<r28s-a-dhcp-ip>:~/snmp-mikrotik
ssh pi@<r28s-a-dhcp-ip>
```

### 2. Install dependencies (needs internet — do this before the network step)

```bash
sudo apt update && sudo apt install -y iperf3 snmp
cd ~/snmp-mikrotik && uv sync
timedatectl status | grep synchronized     # should say "yes"
```

The `iperf3` package install prompts "Should iperf3 server start
automatically?" — answer **No**. Its stock `iperf3.service` would bind the
same port 5201 as `deploy/iperf3-server.service` (installed in step 5), and
having both enabled causes one to fail to start. To skip the prompt
entirely, install non-interactively instead:

```bash
echo "iperf3 iperf3/start_daemon boolean false" | sudo debconf-set-selections
sudo DEBIAN_FRONTEND=noninteractive apt install -y iperf3 snmp
```

If you already answered "Yes" by accident, disable the stock service so it
doesn't fight with `iperf3-server.service`:

```bash
sudo systemctl disable --now iperf3.service
```

### 3. Configure static IPs (board loses internet access after this)

```bash
nmcli device status       # confirm eth0/eth1 device state
nmcli connection show     # find eth0's existing profile name, e.g. "Wired connection 1"
```

`eth1` must show `disconnected` (not `unavailable`) before you can bring up
a connection on it — `unavailable` means NetworkManager sees no carrier,
almost always because nothing is plugged in yet. Plug a cable into `eth1`
first; if it's still `unavailable`, try `sudo ip link set eth1 up`.

```bash
# Rename eth0's existing profile for clarity, then configure it
sudo nmcli connection modify "Wired connection 1" connection.id eth0
sudo nmcli connection modify eth0 \
  ipv4.addresses 192.168.1.90/24 \
  ipv4.method manual
# no ipv4.gateway on eth0 — MikroTik devices are on the same /24, no gateway needed
sudo nmcli connection up eth0

# eth1 usually has no profile yet — create one
sudo nmcli connection add type ethernet ifname eth1 con-name eth1 \
  ipv4.addresses 192.168.2.90/24 ipv4.method manual
sudo nmcli connection up eth1
```

If `eth0` already has a profile literally named `eth0` (or `eth1` already
has a profile), skip the rename/add step for that interface and use
`nmcli connection modify <name> ...` directly instead.

From this point on, reach the board at `192.168.1.90` (from the MikroTik
side) or `192.168.2.90` (from a laptop on `eth1`) — not its old DHCP address.

### 4. Enable IP forwarding + NAT (eth1 → eth0)

```bash
echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-ip-forward.conf
sudo sysctl --system

sudo tee /etc/nftables.conf > /dev/null <<'EOF'
#!/usr/sbin/nft -f
flush ruleset

table inet nat {
    chain postrouting {
        type nat hook postrouting priority 100;
        oifname "eth0" masquerade
    }
}
EOF

sudo systemctl enable --now nftables
sudo systemctl restart nftables
```

### 5. Activate services

```bash
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

Same order as r28s-a: copy + install (while internet is available), then
network, then activate services. Only the IPs and the skipped `IPERF_TARGET`
line differ.

### 1. Copy the project (while the board still has internet via DHCP)

Same options as r28s-a above — rsync from Linux/macOS, `git clone` directly
on the board (simplest from Windows), or `scp` for unpushed local edits:

```bash
# Linux/macOS
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  /home/kone/claude_projects/snmp-Mikrotik/ pi@<r28s-b-dhcp-ip>:~/snmp-mikrotik/
ssh pi@<r28s-b-dhcp-ip>

# OR, from any machine incl. Windows — clone straight from GitHub on the board
ssh pi@<r28s-b-dhcp-ip>
git clone https://github.com/guyver30/snmp-Mikrotik.git ~/snmp-mikrotik
cd ~/snmp-mikrotik
```

### 2. Install dependencies (needs internet — do this before the network step)

```bash
sudo apt update && sudo apt install -y iperf3 snmp
cd ~/snmp-mikrotik && uv sync
timedatectl status | grep synchronized
```

Answer **No** to the "Should iperf3 server start automatically?" prompt (or
install non-interactively — see the note in the r28s-a section above) so
the stock `iperf3.service` doesn't conflict with `deploy/iperf3-server.service`.

### 3. Configure static IPs (board loses internet access after this)

```bash
nmcli device status
nmcli connection show
```

```bash
sudo nmcli connection modify "Wired connection 1" connection.id eth0
sudo nmcli connection modify eth0 \
  ipv4.addresses 192.168.1.91/24 \
  ipv4.method manual
sudo nmcli connection up eth0

sudo nmcli connection add type ethernet ifname eth1 con-name eth1 \
  ipv4.addresses 192.168.2.91/24 ipv4.method manual
sudo nmcli connection up eth1
```

### 4. Enable IP forwarding + NAT (eth1 → eth0)

```bash
echo "net.ipv4.ip_forward=1" | sudo tee /etc/sysctl.d/99-ip-forward.conf
sudo sysctl --system

sudo tee /etc/nftables.conf > /dev/null <<'EOF'
#!/usr/sbin/nft -f
flush ruleset

table inet nat {
    chain postrouting {
        type nat hook postrouting priority 100;
        oifname "eth0" masquerade
    }
}
EOF

sudo systemctl enable --now nftables
sudo systemctl restart nftables
```

### 5. Activate services — identical to r28s-a **except leave `IPERF_TARGET=` blank**

```bash
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

## Laptop side + verifying the network

Plug the laptop into `eth1` and set a static IP in the same subnet, e.g.
`192.168.2.10/24`, gateway `192.168.2.90` (or `.91` on r28s-b) — no DNS
needed for local ssh/Winbox access.

```bash
ping 192.168.2.90        # the R28S itself, on eth1
ping 192.168.1.80        # MikroTik master, routed via eth1→eth0 NAT
ssh pi@192.168.1.91      # the other R28S, routed via eth1→eth0 NAT
```

Winbox to `192.168.1.80`/`192.168.1.81` should also work from the laptop
once the pings succeed.

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

## Updating the software

**Once the [network setup](#networking-overview-eth0-to-mikrotik-eth1-to-laptop)
above is applied, the board has no internet access** — `eth0`/`eth1` are
static with no default gateway, so `git pull` and `uv sync` (if it needs to
fetch a new/changed package) won't work run directly on the board anymore.
Pull the update on a machine that *does* have internet, then push it to the
board over the local network (`eth0` or `eth1`, whichever you can reach)
instead of pulling on the board itself.

Run this against one board at a time (avoid updating both simultaneously if
`IPERF_TARGET` is set — a client test running mid-update on one side will
just fail and retry, but there's no reason to risk both at once).

**1. On a machine with internet access** (your dev machine, or the laptop on `eth1`):

```bash
git clone https://github.com/guyver30/snmp-Mikrotik.git   # or: cd snmp-Mikrotik && git pull
```

**2. Push the update to the board** (rsync from Linux/macOS, or `scp` from
Windows — see the "Copy the project" step earlier for the Windows/no-rsync
options):

```bash
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  snmp-Mikrotik/ pi@192.168.1.90:~/snmp-mikrotik/    # or 192.168.2.90 from eth1, or .91/.91 for r28s-b
```

**3. On the board — stop, sync, restart:**

```bash
sudo systemctl stop snmp-mikrotik.service
sudo systemctl stop iperf3-server.service

cd ~/snmp-mikrotik
uv sync                # only needs internet if pyproject.toml/uv.lock changed;
                        # if it does and the board has no route, run `uv sync`
                        # on the dev machine first and rsync the .venv across too

sudo systemctl start iperf3-server.service
sudo systemctl start snmp-mikrotik.service

sudo systemctl status snmp-mikrotik.service iperf3-server.service
journalctl -u snmp-mikrotik -f
```

`snmp-mikrotik.service` doesn't need `daemon-reload` or a `cp` back into
`/etc/systemd/system/` unless the unit file itself (`deploy/snmp-mikrotik.service`)
changed — it just re-execs `uv run monitor.py --headless` from
`~/snmp-mikrotik` on start, so a plain code sync + restart is enough for
`monitor.py` changes. If the unit file *did* change, re-run the `sed` +
`cp` step from initial setup (substituting your actual username) before
`daemon-reload` and restart.

The stop is a graceful `SIGTERM`, which `monitor.py` catches to log a
`monitor_stop` event — expect a fresh `link_log_<timestamp>.csv` /
`iperf_log_<timestamp>.csv` pair and a new `monitor_start` event in
`events.csv` after the restart.

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
