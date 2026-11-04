# Example battery assembly: 4S LiFePO4, 334 Ah, 200 A BMS

> Public, non-identifying technical example based on one 4-cell configuration. No serial number, passwords, device address, names or raw config are published.

| Component | Details |
| --- | --- |
| Chemistry | LiFePO4 (LFP) |
| Cells | 4 × EVE LF334, series connection (**4S1P**) |
| Nominal capacity | **334 Ah** (series connection does not add amp-hours) |
| Nominal cell voltage | 3.22 V |
| Nominal pack voltage | **12.88 V** |
| Nominal energy | approximately **4.30 kWh** (12.88 V × 334 Ah) |
| BMS | JK-B2A8S20P, 200 A protection setting for charge/discharge |
| Active balancing | BMS enabled, start 3.40 V/cell, threshold delta 0.010 V, limit 2 A |
| Inverter / UPS used in this setup | KEMOT URZ3407-LFP4, 12 V, nominal AC output up to 1200 W |

**Note:** “200 A battery” is ambiguous. **334 Ah** is the battery capacity; **200 A** refers here to the JK BMS discharge/charge overcurrent protection settings and nominal BMS class. It is not a 200 Ah battery. Current that is *actually* safe depends on cell datasheet, cable gauge, fuses, terminals, thermal conditions and equipment specifications.

## Example settings decoded from `.jkcfg`

| Parameter | Exported setting |
| --- | ---: |
| Cell UVP / UVPR | 2.50 / 2.90 V |
| Cell OVP / OVPR | 3.65 / 3.45 V |
| Power-off voltage | 2.49 V/cell |
| SOC 0% / 100% voltage | 2.70 / 3.59 V/cell |
| Charge/discharge overcurrent | 200 / 200 A |
| Capacity configured in BMS | 334 Ah |

These are **recorded device settings, not recommended universal limits**. In the associated KEMOT UPS, a previously reported 11.0 V pack cutoff means approximately 2.75 V/cell *if perfectly balanced*. The BMS monitors each cell separately and may disconnect at 2.50 V for one weak cell even when pack voltage is higher. Never intentionally run the pack to the BMS emergency cutoff as a normal SOC test. UPS voltage percentage and JK coulomb-counted percentage may differ for LFP; voltage alone, especially under load, is not a precise SOC measurement.

No original `.jkcfg` sample is included because the full export can embed sensitive credentials and device identifiers. For reproducible tests, this repository generates synthetic JK02 frames instead.
