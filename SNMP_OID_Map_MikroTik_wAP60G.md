# SNMP OID Map — MikroTik wAP 60G (RBwAPG-60ad)

**Host:** 192.168.1.80  
**Device:** MikroTik wAP 60G (RBwAPG-60ad)  
**RouterOS:** 7.20.8 (long-term)  
**Serial:** HGS0AFHKR07  
**Identity:** MikroTik  
**Location:** Garage28  
**Generated from:** SNMP Walk + MIKROTIK-MIB  

---

## 1. System Information (MIB-2 sysGroup — .1.3.6.1.2.1.1)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.1.1.0 | sysDescr | RouterOS RBwAPG-60ad |
| .1.3.6.1.2.1.1.2.0 | sysObjectID | .1.3.6.1.4.1.14988.1 (MikroTik) |
| .1.3.6.1.2.1.1.3.0 | sysUpTime | 1427000 (hundredths of sec ≈ 3h 57m) |
| .1.3.6.1.2.1.1.4.0 | sysContact | *(empty)* |
| .1.3.6.1.2.1.1.5.0 | sysName | MikroTik |
| .1.3.6.1.2.1.1.6.0 | sysLocation | Garage28 |
| .1.3.6.1.2.1.1.7.0 | sysServices | 78 |

---

## 2. Interfaces (MIB-2 ifTable — .1.3.6.1.2.1.2)

**Interface count:** 5

### 2.1 Interface Index & Names (.1.3.6.1.2.1.2.2.1.1 / .1.3.6.1.2.1.2.2.1.2)

| ifIndex | ifDescr (Name) | ifType | ifMtu | ifSpeed | ifPhysAddress | ifAdminStatus | ifOperStatus |
|---------|---------------|--------|-------|---------|---------------|---------------|-------------|
| 1 | lo | 1 (other/loopback) | 65536 | 0 | 00:00:00:00:00:00 | up(1) | up(1) |
| 2 | ether1 | 6 (ethernetCsmacd) | 1500 | 1000000000 (1Gbps) | F4:1E:57:08:4F:6D | up(1) | up(1) |
| 3 | wlan60-1 | 71 (ieee80211) | 1500 | 385000000 (385Mbps) | F4:1E:57:08:4F:6E | up(1) | down(2) |
| 4 | bridge | 209 (bridge) | 1500 | 0 | F4:1E:57:08:4F:6D | up(1) | up(1) |
| 5 | wlan60-station-1 | 71 (ieee80211) | 1500 | 385000000 (385Mbps) | F4:1E:57:08:4F:6E | up(1) | up(1) |

### 2.2 Interface Counters (.1.3.6.1.2.1.2.2.1.10–21)

| OID Suffix | Name | lo | ether1 | wlan60-1 | bridge | wlan60-station-1 |
|-----------|------|-----|--------|----------|--------|-----------------|
| .9.x | ifLastChange | 2249 | 3223 | 0 | 2252 | 2872 |
| .10.x | ifInOctets | 340 | 4,970,310 | 0 | 3,743,484,689 | 3,740,292,163 |
| .11.x | ifInUcastPkts | 5 | 54,589 | 0 | 2,685,408 | 2,609,983 |
| .12.x | ifInNUcastPkts | 0 | 0 | 0 | 0 | 0 |
| .13.x | ifInDiscards | 0 | 0 | 0 | 0 | 0 |
| .14.x | ifInErrors | 0 | 0 | 0 | 0 | 0 |
| .15.x | ifInUnknownProtos | 0 | 0 | 0 | 0 | 0 |
| .16.x | ifOutOctets | 340 | 27,304,547 | 0 | 3,798,579,862 | 2,720,983,174 |
| .17.x | ifOutUcastPkts | 5 | 46,404 | 0 | 2,541,809 | 1,975,945 |
| .18.x | ifOutNUcastPkts | 0 | 0 | 0 | 0 | 0 |
| .19.x | ifOutDiscards | 0 | 0 | 0 | 0 | 0 |
| .20.x | ifOutErrors | 0 | 0 | 0 | 0 | 0 |
| .21.x | ifOutQLen | 0 | 0 | 0 | 0 | 0 |

---

## 3. IF-MIB Extended (ifXTable — .1.3.6.1.2.1.31.1.1.1)

| OID Suffix | Name | lo | ether1 | wlan60-1 | bridge | wlan60-station-1 |
|-----------|------|-----|--------|----------|--------|-----------------|
| .1.x | ifName | lo | ether1 | wlan60-1 | bridge | wlan60-station-1 |
| .2.x | ifInMulticastPkts | 0 | 0 | 0 | 0 | 0 |
| .3.x | ifInBroadcastPkts | 0 | 0 | 0 | 0 | 0 |
| .4.x | ifOutMulticastPkts | 0 | 0 | 0 | 0 | 0 |
| .5.x | ifOutBroadcastPkts | 0 | 0 | 0 | 0 | 0 |
| .6.x | ifHCInOctets | 340 | 4,970,310 | 0 | 3,743,484,689 | 3,740,292,163 |
| .7.x | ifHCInUcastPkts | 5 | 54,589 | 0 | 2,685,408 | 2,609,983 |
| .8.x | ifHCInMulticastPkts | 0 | 3,989 | 0 | 0 | 0 |
| .9.x | ifHCInBroadcastPkts | 0 | 11,414 | 0 | 0 | 0 |
| .10.x | ifHCOutOctets | 340 | 27,304,547 | 0 | 3,798,579,862 | 2,720,983,174 |
| .11.x | ifHCOutUcastPkts | 5 | 46,404 | 0 | 2,541,809 | 1,975,945 |
| .12.x | ifHCOutMulticastPkts | 0 | 4,075 | 0 | 0 | 0 |
| .13.x | ifHCOutBroadcastPkts | 0 | 452 | 0 | 0 | 0 |
| .15.x | ifHighSpeed (Mbps) | 0 | 1000 | 385 | 0 | 385 |
| .18.x | ifAlias | *(empty)* | *(empty)* | *(empty)* | defconf | *(empty)* |

---

## 4. IP Address Table (MIB-2 — .1.3.6.1.2.1.4)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.4.1.0 | ipForwarding | 1 (forwarding) |
| .1.3.6.1.2.1.4.2.0 | ipDefaultTTL | 255 |
| .1.3.6.1.2.1.4.20.1.1.192.168.1.80 | ipAdEntAddr | 192.168.1.80 |
| .1.3.6.1.2.1.4.20.1.2.192.168.1.80 | ipAdEntIfIndex | 4 (bridge) |
| .1.3.6.1.2.1.4.20.1.3.192.168.1.80 | ipAdEntNetMask | 255.255.255.0 |

### 4.1 ARP Table (.1.3.6.1.2.1.4.22)

| IP Address | Interface | MAC Address |
|-----------|-----------|-------------|
| 192.168.1.5 | 4 (bridge) | E4:1F:D5:F0:F4:A6 |
| 192.168.1.9 | 4 (bridge) | 04:CF:4B:EC:D8:A8 |
| 192.168.1.58 | 4 (bridge) | 18:FD:74:3D:83:1A |
| 192.168.1.81 | 4 (bridge) | F4:1E:57:08:4F:6F |

---

## 5. HOST-RESOURCES-MIB (.1.3.6.1.2.1.25)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.25.1.1.0 | hrSystemUptime | 1427000 |
| .1.3.6.1.2.1.25.1.2.0 | hrSystemDate | 2026-01-29 13:15:25 |
| .1.3.6.1.2.1.25.2.2.0 | hrMemorySize | 262144 KB (256 MB) |

### 5.1 Storage Table (.1.3.6.1.2.1.25.2.3)

| Storage ID | Type | Description | Unit (bytes) | Size | Used |
|-----------|------|-------------|-------------|------|------|
| 65536 | hrStorageRam (.1.3.6.1.2.1.25.2.1.2) | main memory | 1024 | 262,144 (256 MB) | 79,512 (77.6 MB) |
| 131072 | hrStorageFixedDisk (.1.3.6.1.2.1.25.2.1.4) | system disk | 1024 | 16,384 (16 MB) | 15,208 (14.9 MB) |

### 5.2 Processor Table (.1.3.6.1.2.1.25.3)

| Index | Type | Status |
|-------|------|--------|
| 1 | hrDeviceProcessor | running(2) |
| 2 | hrDeviceProcessor | running(2) |
| 3 | hrDeviceProcessor | running(2) |
| 4 | hrDeviceProcessor | running(2) |

---

## 6. ENTITY-MIB (.1.3.6.1.2.1.47)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.47.1.1.1.1.2.65536 | entPhysicalDescr | RouterOS 7.20.8 (long-term) on RBwAPG-60ad |
| .1.3.6.1.2.1.47.1.1.1.1.5.65536 | entPhysicalClass | 3 (chassis) |
| .1.3.6.1.2.1.47.1.1.1.1.7.65536 | entPhysicalName | ARM |

---

## 7. BRIDGE-MIB (.1.3.6.1.2.1.17)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.17.1.1.0 | dot1dBaseBridgeAddress | F4:1E:57:08:4F:6D |
| .1.3.6.1.2.1.17.2.1.0 | dot1dStpProtocolSpecification | 3 (ieee8021d) |
| .1.3.6.1.2.1.17.2.2.0 | dot1dStpPriority | 32768 |

### 7.1 Bridge Forwarding Table (selected MACs)

13 MAC addresses learned across bridge ports.

---

## 8. MikroTik Private MIB (.1.3.6.1.4.1.14988)

### 8.1 Wireless 60GHz — mtxrWl60GTable (.1.3.6.1.4.1.14988.1.1.1.8)

**OID Base:** `.1.3.6.1.4.1.14988.1.1.1.8.1`  
**Interface index:** 3 (wlan60-1, AP mode)

| OID | MIB Name | Value | Description |
|-----|----------|-------|-------------|
| .1.3.6.1.4.1.14988.1.1.1.8.1.2.3 | mtxrWl60GMode | 3 | bridge mode |
| .1.3.6.1.4.1.14988.1.1.1.8.1.3.3 | mtxrWl60GSsid | MikroTik-84f6d | SSID |
| .1.3.6.1.4.1.14988.1.1.1.8.1.4.3 | mtxrWl60GConnected | 1 (true) | Connected |
| .1.3.6.1.4.1.14988.1.1.1.8.1.5.3 | mtxrWl60GRemote | F4:1E:57:08:4F:70 | Remote MAC |
| .1.3.6.1.4.1.14988.1.1.1.8.1.6.3 | mtxrWl60GFreq | 58320 MHz | Frequency |
| .1.3.6.1.4.1.14988.1.1.1.8.1.7.3 | mtxrWl60GMcs | 1 | MCS index |
| .1.3.6.1.4.1.14988.1.1.1.8.1.8.3 | mtxrWl60GSignal | 80 | Signal % |
| .1.3.6.1.4.1.14988.1.1.1.8.1.9.3 | mtxrWl60GTxSector | 35 | TX sector |
| .1.3.6.1.4.1.14988.1.1.1.8.1.11.3 | mtxrWl60GTxSectorInfo | center | Sector info |
| .1.3.6.1.4.1.14988.1.1.1.8.1.12.3 | mtxrWl60GRssi | -53 | RSSI (dBm) |
| .1.3.6.1.4.1.14988.1.1.1.8.1.13.3 | mtxrWl60GPhyRate | 385 | PHY rate (Mbps) |

### 8.2 Wireless 60GHz Station — mtxrWl60GStaTable (.1.3.6.1.4.1.14988.1.1.1.9)

**OID Base:** `.1.3.6.1.4.1.14988.1.1.1.9.1`  
**Interface index:** 5 (wlan60-station-1)

| OID | MIB Name | Value | Description |
|-----|----------|-------|-------------|
| .1.3.6.1.4.1.14988.1.1.1.9.1.2.5 | mtxrWl60GStaConnected | 1 (true) | Connected |
| .1.3.6.1.4.1.14988.1.1.1.9.1.3.5 | mtxrWl60GStaRemote | F4:1E:57:08:4F:70 | Remote MAC |
| .1.3.6.1.4.1.14988.1.1.1.9.1.4.5 | mtxrWl60GStaMcs | 1 | MCS index |
| .1.3.6.1.4.1.14988.1.1.1.9.1.5.5 | mtxrWl60GStaSignal | 80 | Signal % |
| .1.3.6.1.4.1.14988.1.1.1.9.1.6.5 | mtxrWl60GStaTxSector | 35 | TX sector |
| .1.3.6.1.4.1.14988.1.1.1.9.1.8.5 | mtxrWl60GStaPhyRate | 385 | PHY rate (Mbps) |
| .1.3.6.1.4.1.14988.1.1.1.9.1.9.5 | mtxrWl60GStaRssi | -53 | RSSI (dBm) |
| .1.3.6.1.4.1.14988.1.1.1.9.1.10.5 | mtxrWl60GStaDistance | 1268 | Distance (meters) |

### 8.3 Wireless General (.1.3.6.1.4.1.14988.1.1.1)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.1.4.0 | mtxrWlStatTxRate | 0 |
| .1.3.6.1.4.1.14988.1.1.1.6.0 | mtxrWlStatRxRate | 0 |
| .1.3.6.1.4.1.14988.1.1.1.10.0 | mtxrWlRtabEntryCount | 0 |

### 8.4 Health — mtxrHealth (.1.3.6.1.4.1.14988.1.1.3)

| OID | MIB Name | Value | Description |
|-----|----------|-------|-------------|
| .1.3.6.1.4.1.14988.1.1.3.9.0 | mtxrHlActiveFan | n/a | No active fan |
| .1.3.6.1.4.1.14988.1.1.3.14.0 | mtxrHlProcessorFrequency | 672 | CPU freq (MHz) |

### 8.5 License — mtxrLicense (.1.3.6.1.4.1.14988.1.1.4)

| OID | MIB Name | Value | Description |
|-----|----------|-------|-------------|
| .1.3.6.1.4.1.14988.1.1.4.1.0 | mtxrLicSoftwareId | PYDW-E6TL | Software ID |
| .1.3.6.1.4.1.14988.1.1.4.3.0 | mtxrLicLevel | 3 | License level |
| .1.3.6.1.4.1.14988.1.1.4.4.0 | mtxrLicVersion | 7.20.8 | Software version |
| .1.3.6.1.4.1.14988.1.1.4.5.0 | mtxrLicUpgradableTo | 7 | Max upgrade level |

### 8.6 DHCP — mtxrDHCP (.1.3.6.1.4.1.14988.1.1.6)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.6.1.0 | mtxrDHCPLeaseCount | 0 |

### 8.7 System — mtxrSystem (.1.3.6.1.4.1.14988.1.1.7)

| OID | MIB Name | Value | Description |
|-----|----------|-------|-------------|
| .1.3.6.1.4.1.14988.1.1.7.1.0 | mtxrSystemReboot | 0 | Reboot trigger |
| .1.3.6.1.4.1.14988.1.1.7.2.0 | mtxrUSBPowerReset | 0 | USB power reset |
| .1.3.6.1.4.1.14988.1.1.7.3.0 | mtxrSerialNumber | HGS0AFHKR07 | Board serial |
| .1.3.6.1.4.1.14988.1.1.7.4.0 | mtxrFirmwareVersion | 7.20.8 | Current firmware |
| .1.3.6.1.4.1.14988.1.1.7.5.0 | mtxrNote | *(empty)* | Note |
| .1.3.6.1.4.1.14988.1.1.7.6.0 | mtxrBuildTime | 2026-01-30 09:17:54 | Build timestamp |
| .1.3.6.1.4.1.14988.1.1.7.7.0 | mtxrFirmwareUpgradeVersion | 7.20.8 | Upgrade version |
| .1.3.6.1.4.1.14988.1.1.7.8.0 | mtxrDisplayName | wAP 60G | Display name |
| .1.3.6.1.4.1.14988.1.1.7.9.0 | mtxrBoardName | RBwAPG-60ad | Board name |

### 8.8 Neighbor Discovery — mtxrNeighbor (.1.3.6.1.4.1.14988.1.1.11)

| Neighbor | OID Suffix | MIB Name | Value |
|----------|-----------|----------|-------|
| **#1** | .1.1.2.1 | mtxrNeighborIpAddress | 192.168.1.81 |
| | .1.1.3.1 | mtxrNeighborMacAddress | F4:1E:57:08:4F:70 |
| | .1.1.4.1 | mtxrNeighborVersion | 7.20.8 (long-term) 2026-01-30 09:17:54 |
| | .1.1.5.1 | mtxrNeighborPlatform | MikroTik |
| | .1.1.6.1 | mtxrNeighborIdentity | MikroTik |
| | .1.1.7.1 | mtxrNeighborSoftwareID | 7T5F-5PDV |
| | .1.1.8.1 | mtxrNeighborInterfaceID | 5 (wlan60-station-1) |
| **#2** | .1.1.2.2 | mtxrNeighborIpAddress | 192.168.1.58 |
| | .1.1.3.2 | mtxrNeighborMacAddress | 18:FD:74:3D:83:1A |
| | .1.1.4.2 | mtxrNeighborVersion | 6.49.18 (long-term) |
| | .1.1.5.2 | mtxrNeighborPlatform | MikroTik |
| | .1.1.6.2 | mtxrNeighborIdentity | MikroTik |
| | .1.1.7.2 | mtxrNeighborSoftwareID | U6KE-N5YW |
| | .1.1.8.2 | mtxrNeighborInterfaceID | 2 (ether1) |

### 8.9 GPS — mtxrGps (.1.3.6.1.4.1.14988.1.1.12)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.12.1.0 | mtxrDate | 0 |
| .1.3.6.1.4.1.14988.1.1.12.6.0 | mtxrSattelites | 0 |
| .1.3.6.1.4.1.14988.1.1.12.7.0 | mtxrValid | 0 (no GPS) |

### 8.10 Wireless Modem — mtxrWirelessModem (.1.3.6.1.4.1.14988.1.1.13)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.13.1.0 | mtxrWirelessModemSignalStrength | 0 |
| .1.3.6.1.4.1.14988.1.1.13.2.0 | mtxrWirelessModemSignalECIO | 0 |
| .1.3.6.1.4.1.14988.1.1.13.10.0 | mtxrWirelessModemRSRP | 0 |
| .1.3.6.1.4.1.14988.1.1.13.11.0 | mtxrWirelessModemRSRQ | 0 |
| .1.3.6.1.4.1.14988.1.1.13.12.0 | mtxrWirelessModemSINR | 0 |

*(No wireless modem present — all values zero/empty)*

### 8.11 Interface Stats — mtxrInterfaceStats (.1.3.6.1.4.1.14988.1.1.14.1)

**OID Base:** `.1.3.6.1.4.1.14988.1.1.14.1.1`

| OID Suffix | MIB Name | lo | ether1 | wlan60-1 | bridge | wlan60-station-1 |
|-----------|----------|-----|--------|----------|--------|-----------------|
| .2.x | mtxrInterfaceStatsName | lo | ether1 | wlan60-1 | bridge | wlan60-station-1 |
| .11.x | mtxrInterfaceStatsDriverRxBytes | 0 | 4,964,752 | 0 | 0 | 0 |
| .12.x | mtxrInterfaceStatsDriverRxPackets | 0 | 54,540 | 0 | 0 | 0 |
| .13.x | mtxrInterfaceStatsDriverTxBytes | 0 | 27,247,534 | 0 | 0 | 0 |
| .14.x | mtxrInterfaceStatsDriverTxPackets | 0 | 46,371 | 0 | 0 | 0 |
| .31.x | mtxrInterfaceStatsRxBytes | 0 | 5,183,186 | 0 | 0 | 0 |
| .34.x | mtxrInterfaceStatsRx64 | 0 | 23,903 | 0 | 0 | 0 |
| .35.x | mtxrInterfaceStatsRx65To127 | 0 | 21,053 | 0 | 0 | 0 |
| .36.x | mtxrInterfaceStatsRx128To255 | 0 | 7,277 | 0 | 0 | 0 |
| .37.x | mtxrInterfaceStatsRx256To511 | 0 | 2,310 | 0 | 0 | 0 |
| .42.x | mtxrInterfaceStatsRxBroadcast | 0 | 11,416 | 0 | 0 | 0 |
| .44.x | mtxrInterfaceStatsRxMulticast | 0 | 3,989 | 0 | 0 | 0 |
| .61.x | mtxrInterfaceStatsTxBytes | 0 | 27,445,980 | 0 | 0 | 0 |
| .64.x | mtxrInterfaceStatsTx64 | 0 | 5,431 | 0 | 0 | 0 |
| .65.x | mtxrInterfaceStatsTx65To127 | 0 | 15,665 | 0 | 0 | 0 |
| .66.x | mtxrInterfaceStatsTx128To255 | 0 | 2,545 | 0 | 0 | 0 |
| .67.x | mtxrInterfaceStatsTx256To511 | 0 | 8,421 | 0 | 0 | 0 |
| .68.x | mtxrInterfaceStatsTx512To1023 | 0 | 54 | 0 | 0 | 0 |
| .69.x | mtxrInterfaceStatsTx1024To1518 | 0 | 14,260 | 0 | 0 | 0 |
| .72.x | mtxrInterfaceStatsTxBroadcast | 0 | 452 | 0 | 0 | 0 |
| .74.x | mtxrInterfaceStatsTxMulticast | 0 | 4,075 | 0 | 0 | 0 |

*(Only ether1 reports detailed hardware-level stats; bridge/wlan stats are at the MIB-2 level)*

### 8.12 Partition — mtxrPartition (.1.3.6.1.4.1.14988.1.1.17)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.17.1.1.2.1 | mtxrPartitionName | part0 |
| .1.3.6.1.4.1.14988.1.1.17.1.1.3.1 | mtxrPartitionSize | 15 MB |
| .1.3.6.1.4.1.14988.1.1.17.1.1.4.1 | mtxrPartitionVersion | RouterOS v7.20.8 2026-01-30 09:17:54 |
| .1.3.6.1.4.1.14988.1.1.17.1.1.5.1 | mtxrPartitionActive | 1 (true) |
| .1.3.6.1.4.1.14988.1.1.17.1.1.6.1 | mtxrPartitionRunning | 1 (true) |

### 8.13 IPSec — mtxrIPSec (.1.3.6.1.4.1.14988.1.1.20)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.20.1.1.0 | mtxrIkeSACount | 0 (no IPSec tunnels) |

### 8.14 WiFi/CAPsMAN — mtxrWifi (.1.3.6.1.4.1.14988.1.1.21)

| OID | MIB Name | Value | Description |
|-----|----------|-------|-------------|
| .1.3.6.1.4.1.14988.1.1.21.1.1.0 | mtxrWifiCapsmanEnabled | 2 (false) | CAPsMAN disabled |
| .1.3.6.1.4.1.14988.1.1.21.1.3.0 | mtxrWifiCapsmanCACertificate | none | |
| .1.3.6.1.4.1.14988.1.1.21.1.4.0 | mtxrWifiCapsmanCertificate | none | |
| .1.3.6.1.4.1.14988.1.1.21.1.5.0 | mtxrWifiCapsmanRequirePeerCertificate | 2 (false) | |
| .1.3.6.1.4.1.14988.1.1.21.1.8.0 | (wifi config) | none | |

### 8.15 Connection Tracking — mtxrCT (.1.3.6.1.4.1.14988.1.1.22)

| OID | MIB Name | Value |
|-----|----------|-------|
| .1.3.6.1.4.1.14988.1.1.22.1.1.0 | (CT total entries) | 0 |
| .1.3.6.1.4.1.14988.1.1.22.1.2.0 | (CT max entries) | 0 |
| .1.3.6.1.4.1.14988.1.1.22.1.3.0 | (CT active) | 0 |

---

## 9. Other Standard MIBs Present

### 9.1 UPS-MIB (.1.3.6.1.2.1.33) — Stub only

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.33.1.3.2.0 | upsBatteryNumBatteries | 1 |
| .1.3.6.1.2.1.33.1.4.3.0 | upsOutputNumLines | 1 |

### 9.2 UCD-SNMP (.1.3.6.1.4.1.2021)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.4.1.2021.11.10.0 | ssCpuIdle | 0 |

### 9.3 Squid-MIB (.1.3.6.1.4.1.3495) — Stub/proxy counters

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.4.1.3495.1.1.3.0 | cacheUptime | 14270 |

### 9.4 CISCO-VLAN-MEMBERSHIP-MIB (.1.3.6.1.4.1.9.9.150)

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.4.1.9.9.150.1.1.1.0 | vmVmpsVQPVersion | 0 |

### 9.5 DHCP Server (.1.3.6.1.2.1.9999) — MikroTik extension

| OID | Name | Value |
|-----|------|-------|
| .1.3.6.1.2.1.9999.1.1.1.1.0 | (DHCP server name) | RouterOS DHCP server |
| .1.3.6.1.2.1.9999.1.1.1.2.0 | (DHCP server OID) | .1.3.6.1.4.1.14988.1 |

---

## 10. Key OIDs for Checkmk SNMP Monitoring

These are the most useful OIDs to configure as service checks in Checkmk:

### Critical Monitoring OIDs

| What to Monitor | OID | MIB Name | Why |
|----------------|-----|----------|-----|
| **60GHz Link Connected** | .1.3.6.1.4.1.14988.1.1.1.8.1.4.3 | mtxrWl60GConnected | Link up/down detection |
| **60GHz Signal %** | .1.3.6.1.4.1.14988.1.1.1.8.1.8.3 | mtxrWl60GSignal | Signal quality |
| **60GHz RSSI** | .1.3.6.1.4.1.14988.1.1.1.8.1.12.3 | mtxrWl60GRssi | Signal strength (dBm) |
| **60GHz PHY Rate** | .1.3.6.1.4.1.14988.1.1.1.8.1.13.3 | mtxrWl60GPhyRate | Link speed (Mbps) |
| **60GHz MCS** | .1.3.6.1.4.1.14988.1.1.1.8.1.7.3 | mtxrWl60GMcs | Modulation index |
| **60GHz Frequency** | .1.3.6.1.4.1.14988.1.1.1.8.1.6.3 | mtxrWl60GFreq | Operating freq (MHz) |
| **60GHz Distance** | .1.3.6.1.4.1.14988.1.1.1.9.1.10.5 | mtxrWl60GStaDistance | Link distance (m) |
| **Station Connected** | .1.3.6.1.4.1.14988.1.1.1.9.1.2.5 | mtxrWl60GStaConnected | Station link state |
| **Station RSSI** | .1.3.6.1.4.1.14988.1.1.1.9.1.9.5 | mtxrWl60GStaRssi | Station signal (dBm) |
| **CPU Frequency** | .1.3.6.1.4.1.14988.1.1.3.14.0 | mtxrHlProcessorFrequency | CPU MHz |
| **Memory Used** | .1.3.6.1.2.1.25.2.3.1.6.65536 | hrStorageUsed (RAM) | Memory usage |
| **Memory Total** | .1.3.6.1.2.1.25.2.3.1.5.65536 | hrStorageSize (RAM) | Memory capacity |
| **Disk Used** | .1.3.6.1.2.1.25.2.3.1.6.131072 | hrStorageUsed (disk) | Disk usage |
| **System Uptime** | .1.3.6.1.2.1.1.3.0 | sysUpTime | Uptime |
| **Firmware Version** | .1.3.6.1.4.1.14988.1.1.7.4.0 | mtxrFirmwareVersion | Version tracking |
| **Interface Status** | .1.3.6.1.2.1.2.2.1.8.x | ifOperStatus | Per-interface up/down |
| **Interface Traffic In** | .1.3.6.1.2.1.31.1.1.1.6.x | ifHCInOctets | Bandwidth in |
| **Interface Traffic Out** | .1.3.6.1.2.1.31.1.1.1.10.x | ifHCOutOctets | Bandwidth out |

### Suggested Checkmk Thresholds for 60GHz Link

| Metric | WARN | CRIT |
|--------|------|------|
| mtxrWl60GSignal (%) | < 60 | < 40 |
| mtxrWl60GRssi (dBm) | > -60 | > -70 |
| mtxrWl60GPhyRate (Mbps) | < 300 | < 100 |
| mtxrWl60GConnected | — | = 0 (disconnected) |

---

## 11. OID Tree Summary

```
.1.3.6.1.2.1          (MIB-2)
├── .1                 system (sysDescr, sysName, sysLocation, sysUpTime...)
├── .2                 interfaces (ifTable — 5 interfaces)
├── .4                 ip (addresses, ARP, routing)
├── .17                dot1dBridge (bridge, STP, forwarding)
├── .25                host (hrStorage, hrProcessor)
├── .31                ifMIB (ifXTable — HC counters, ifHighSpeed)
├── .33                upsMIB (stub)
├── .47                entityMIB (physical description)
├── .55                ipv6MIB (IPv6 interfaces, addresses)
└── .9999              (MikroTik DHCP extension)

.1.3.6.1.4.1.14988    (MikroTik private)
└── .1.1               mtXRouterOs
    ├── .1             mtxrWireless (60GHz link stats, station table)
    ├── .3             mtxrHealth (CPU freq, fans, voltage)
    ├── .4             mtxrLicense (software ID, level, version)
    ├── .6             mtxrDHCP (lease count)
    ├── .7             mtxrSystem (serial, firmware, board name)
    ├── .11            mtxrNeighbor (MNDP neighbor discovery)
    ├── .12            mtxrGps (not active)
    ├── .13            mtxrWirelessModem (not present)
    ├── .14            mtxrInterfaceStats (extended per-interface counters)
    ├── .17            mtxrPartition (firmware partitions)
    ├── .20            mtxrIPSec (no tunnels)
    ├── .21            mtxrWifi/CAPsMAN (disabled)
    └── .22            mtxrCT (connection tracking)
```
