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

## r28s-a (192.168.1.90) — iperf3 client schedule

### 1. Copy the project (from your dev machine, while the board still has internet via DHCP)

```bash
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  /home/kone/claude_projects/snmp-Mikrotik/ pi@<r28s-a-dhcp-ip>:~/snmp-mikrotik/
ssh pi@<r28s-a-dhcp-ip>
```

### 2. Install dependencies (needs internet — do this before the network step)

```bash
sudo apt update && sudo apt install -y iperf3
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
sudo DEBIAN_FRONTEND=noninteractive apt install -y iperf3
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

### 1. Copy the project (from your dev machine, while the board still has internet via DHCP)

```bash
rsync -av --exclude .venv --exclude '.git' --exclude '*.csv' \
  /home/kone/claude_projects/snmp-Mikrotik/ pi@<r28s-b-dhcp-ip>:~/snmp-mikrotik/
ssh pi@<r28s-b-dhcp-ip>
```

### 2. Install dependencies (needs internet — do this before the network step)

```bash
sudo apt update && sudo apt install -y iperf3
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
