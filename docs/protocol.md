# JK02 `.jkcfg` structure — decoding notes

This project reads a **600-byte export** consisting of two JK02 BLE frames, not a text document:

| Absolute offset | Frame | Meaning |
| --- | --- | --- |
| 0–299 | 0x01 | Settings |
| 300–599 | 0x03 | Device metadata |

Each frame starts `55 AA EB 90`, followed by a frame type and counter. Byte 299 of each frame is the checksum: `sum(frame[0:299]) & 0xFF`. An incorrect size, header, frame type, or checksum is an error.

**Example**: the 32-bit little-endian bytes `C4 09 00 00` at settings frame offset 10 decode to integer `2500`; multiply by `0.001` to obtain **2.500 V** (cell UVP). The four bytes at offset 130 represent capacity in milliamp-hours: `334000` becomes **334 Ah**. Signed temperature values use 32-bit little-endian integers and factor `0.1 °C` (at offset 98). 1-byte signed discharge UTP fields are at offsets 296 and 297.

Important offsets relative to settings frame:

| Offset | Field | Unit |
| ---: | --- | --- |
| 10 | Cell undervoltage cutoff (UVP) | mV |
| 14 | Cell undervoltage recovery (UVPR) | mV |
| 18 | Cell overvoltage cutoff (OVP) | mV |
| 22 | Cell overvoltage recovery (OVPR) | mV |
| 26 | Balance delta | mV |
| 30, 34 | SOC 100%, SOC 0% threshold | mV |
| 38, 42 | Requested charge/float voltage (RCV/RFV) | mV |
| 46 | Power off cell voltage | mV |
| 50, 62 | Charge/discharge overcurrent settings | mA |
| 78 | Maximum balance current | mA |
| 82–113 | Temperature thresholds | 0.1 °C |
| 114 | Cell count | first byte |
| 118, 122, 126 | Charge/discharge/balancer enable | first byte |
| 130 | Nominal capacity | mAh |
| 138 | Balance start voltage | mV |
| 282–283 | Controls bitmask | uint16 LE |

Device-info frame publicly safe offsets **relative to frame 0x03**: 6–21 model, 22–29 hardware, 30–37 firmware. **Do not publish or expose** other fields: the second frame may contain serial numbers, usernames, device names, passwords and user-defined information. The decoder reads only allowlisted fields, never includes the original file or its path in output, and does not have a raw dump option.

This decoder does *not* connect to Bluetooth, import profiles, change settings, or calculate live SOC. Some config settings (e.g. RCV/RFV) may be unsupported in a given hardware/firmware revision even if an export contains values.

Protocol mapping based on [syssi/esphome-jk-bms JK02 BLE protocol notes](https://github.com/syssi/esphome-jk-bms/blob/main/docs/protocol-design-ble.md) and a locally checked frame structure. Device-specific deviations should be handled by separate documented variants, not guessed.
