<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Can we use a couple of these devices [https://wiki.friendlyelec.com/wiki/index.php/NanoPi_R28S](https://wiki.friendlyelec.com/wiki/index.php/NanoPi_R28S) to connect to both sides (cats) of a wireless bridge to monitor iperf 3 and run python code for SNMP and logging (packet errors and other indicators)

Yes, you can use a couple of NanoPi R28S devices for this purpose. The R28S has the right hardware and runs full Linux, so it’s well suited to sit on each side of a wireless bridge, run iperf3, and do SNMP polling/logging in Python.[^1][^2]

## Why the NanoPi R28S fits this use case

Key points from the spec sheet:

- Dual Gigabit Ethernet ports (RTL8211F + RTL8111H) – you can physically connect one port to each “cat” (each side of the bridge) or use one port for the bridge and the other for management.[^2][^1]
- Integrated Wi‑Fi 6 + BT 5.3 – you can also use one R28S as the wireless client or AP side of the bridge if you want, though your current plan sounds like the wireless bridge is already in place and you just want monitors on each side.[^1][^2]
- Runs standard ARM Linux (e.g., Debian/Ubuntu/Armbian-style images from FriendlyELEC) – iperf3, Python, snmp libraries, and logging tools install normally.[^1]

That means each R28S can:

- Sit in the path (or parallel via a tap/switch) on its side of the bridge.
- Run an iperf3 server or client.
- Run a Python script that:
    - Periodically executes iperf3 tests.
    - Polls SNMP counters (errors, drops, discards, etc.) from the bridge devices or switches.
    - Logs everything with timestamps for later analysis.


## Basic architecture options

You have a few topologies depending on how intrusive you want to be:

### Option A – Passive monitoring via switch (recommended if possible)

- Place a small unmanaged or managed switch on each side of the wireless bridge.
- Connect:
    - Bridge device ↔ switch
    - Rest of LAN ↔ switch
    - NanoPi R28S ↔ switch (one of its Ethernet ports)
- The R28S doesn’t sit directly in the data path; it just:
    - Pings/iperf3’s to the other R28S across the bridge.
    - Polls SNMP on the bridge devices / switches.
- Pros: no single point of failure, easy to add/remove.
- Cons: you measure end‑to‑end performance, not per‑flow in the middle.


### Option B – Inline with dual NICs

- Use one R28S on each side, each with both Ethernet ports active:
    - eth0 → “inside” network segment
    - eth1 → wireless bridge device
- Configure Linux bridging or routing on the R28S so traffic passes through it.
- Then the R28S can:
    - Act as a transparent monitor (with iptables/nftables, tc, eBPF, etc.).
    - Run iperf3 between the two R28S units.
- Pros: very detailed control, can shape/measure specific flows.
- Cons: more complex, adds a potential failure point.

For most “monitor the wireless bridge” scenarios, Option A with switches plus active iperf3 between the two R28S is simplest and robust.

## Running iperf3 between two R28S units

On one R28S (server side):

```bash
sudo apt update
sudo apt install -y iperf3 python3 python3-pip
iperf3 -s
```

On the other R28S (client side), test manually first:

```bash
iperf3 -c <SERVER_IP> -t 30 -i 5
```

This gives you bandwidth, jitter, and retransmissions across the wireless bridge.

You can wrap this in Python using `subprocess` and parse the JSON output:

```python
import subprocess
import json

def run_iperf(server_ip, duration=30, interval=5):
    cmd = [
        "iperf3",
        "-c", server_ip,
        "-t", str(duration),
        "-i", str(interval),
        "-J"  # JSON output
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return data
```

Many projects already do this; there are existing Python wrappers and loggers for iperf3 you can adapt.[^3][^4]

## SNMP polling and logging in Python

For SNMP, typical libraries are `pysnmp` or `snmpwalk` + parsing, or `easy-snmp`. Example with `pysnmp` to get interface errors:

```bash
pip install pysnmp
```

```python
from pysnmp.hlapi import *
import time

def get_iface_errors(snmp_target, oid_ifInErrors="1.3.6.1.2.1.2.2.1.14", oid_ifOutErrors="1.3.6.1.2.1.2.2.1.20", ifindex=2):
    # ifindex is the interface index on the device
    errorIndication, errorStatus, errorIndex, varBinds = next(
        getCmd(SnmpEngine(),
               CommunityData('public'),
               UdpTransportTarget((snmp_target, 161)),
               ContextData(),
               ObjectType(ObjectIdentity(oid_ifInErrors, ifindex)),
               ObjectType(ObjectIdentity(oid_ifOutErrors, ifindex)),
               lexicographicMode=False)
    )
    if errorIndication or errorStatus:
        return None
    in_err = int(varBinds[^0][^1])
    out_err = int(varBinds[^1][^1])
    return in_err, out_err
```

You can:

- Poll both sides’ switches / APs / bridges periodically.
- Log interface counters (in/out errors, discards, CRC errors).
- Correlate with iperf3 results (throughput drops, retransmissions).


## Example combined monitoring script (outline)

On each R28S, you could run something like:

```python
import time
import json
import subprocess
from datetime import datetime
import csv

SERVER_IP = "192.168.10.2"  # other R28S
LOG_FILE = "bridge_monitor.csv"

def run_iperf():
    cmd = ["iperf3", "-c", SERVER_IP, "-t", "20", "-i", "5", "-J"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(res.stdout)

def log_row(row):
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow(row)

while True:
    ts = datetime.now().isoformat()
    iperf_data = run_iperf()
    bandwidth = iperf_data["end"]["sum_received"]["bits_per_second"]
    retrans = iperf_data["end"]["sum_sent"]["retransmits"]

    # Optionally add SNMP calls here
    # in_err, out_err = get_iface_errors("192.168.10.1")

    log_row([ts, bandwidth, retrans])  # , in_err, out_err
    time.sleep(60)  # wait between tests
```

Run this as a systemd service so it starts on boot and keeps logging.

## Practical considerations

- **OS image**: Use a stable FriendlyELEC/Armbian/Debian image for R28S with good Ethernet and Wi‑Fi driver support.[^1]
- **Time sync**: Ensure both R28S units use NTP so timestamps line up.
- **Storage**: Log to the microSD or eMMC; rotate logs to avoid filling the disk.
- **Power \& enclosure**: The R28S is compact; a small case and reliable 5V supply will make this a clean, long‑running monitor.

If you describe your exact bridge hardware (AP model, whether you have managed switches, and whether you want inline vs passive), I can sketch a concrete wiring diagram and a ready‑to‑run Python script tailored to your setup.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^16][^17][^18][^19][^20][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://wiki.friendlyelec.com/wiki/index.php/NanoPi_R28S

[^2]: https://www.cnx-software.com/2026/07/31/nanopi-r28s-a-tiny-dual-gbe-rockchip-rk3528a-wireless-sbc-and-router-with-a-usb-c-console-port/?amp=1

[^3]: https://github.com/rbocchinfuso/iperfspeed

[^4]: https://www.mteke.com/network-performance-tests-with-iperf3-and-python/

[^5]: https://gist.github.com/martignoni/b17aff9a45556aced4fef49d733f2c6e

[^6]: https://www.elektronik-kompendium.de/sites/raspberry-pi/2002161.htm

[^7]: https://github.com/morrownr/USB-WiFi/blob/main/home/AP_Mode/Bridged_Wireless_Access_Point.md

[^8]: https://learn.adafruit.com/using-a-raspberry-pi-as-a-router/network-bridge

[^9]: https://nanopi.org/NanoPi_Quick%20Start.html

[^10]: https://www.youtube.com/watch?v=7x4_Gzv2Hiw

[^11]: https://www.instructables.com/Running-a-Raspberry-Pi-Wi-Fi-Bridge/

[^12]: https://openwrt.org/toh/friendlyarm/nanopi_r2s

[^13]: https://www.devops.lol/rpi-bridge/

[^14]: https://blog.virt.ltd/archives/85/

[^15]: https://wiki.friendlyelec.com/wiki/index.php/NanoPi

[^16]: https://wiki.friendlyelec.com/wiki/index.php/NanoPi_R2S

[^17]: https://stackoverflow.com/questions/77009890/python-script-that-reads-iperf3-output

[^18]: https://personalbsd.org/download/Documents/SCH/NanoPi_R6S_2208_SCH.PDF

[^19]: https://medium.com/jacklee26/iperf3-log-parser-automation-project-eb3a96f7287f

[^20]: https://www.elecbee.com/en/product-detail/nanopi-r2s-mini-router-rk3328-development-board-dual-gigabit-ethernet-port-openwrt-lede_23083

