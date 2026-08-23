# snmp-mikrotik

Real-time SNMP monitoring for a MikroTik wAP 60G point-to-point 60GHz wireless bridge. Polls both ends of the link, logs metrics to CSV, and optionally renders a live matplotlib dashboard.

```bash
# Live GUI (needs a display)
uv run --extra gui monitor.py

# Headless — SNMP polling + CSV logging + iperf3, no display required
uv run monitor.py --headless
```

See `CLAUDE.md` for OID layout, chart layout, and deployment details. See [`deploy/DEPLOY.md`](deploy/DEPLOY.md) for the exact runbook used to run this unattended on two NanoPi R28S boards.
