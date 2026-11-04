# JK BMS `.jkcfg` Decoder

**Offline Python decoder for binary JK BMS configuration exports.** No external dependencies, Bluetooth connection, network requests or writes to the battery. It **never prints** serial numbers, passwords, user data, raw payload or the input filename.

## Українською — як розшифрувати

1. У застосунку JK BMS відкрийте екран налаштувань та знайдіть функцію **Export configuration / Save settings** (назва залежить від версії). Збережіть `.jkcfg` у себе на комп'ютері, **не публікуйте оригінал**.
2. Встановіть Python 3.10 або новіший, завантажте цей репозиторій.
3. У терміналі з папки репозиторію виконайте:

```bash
python jkcfg.py "config.jkcfg"
python jkcfg.py "config.jkcfg" --format json --output sanitized.json
python jkcfg.py "config.jkcfg" --format markdown --output sanitized.md
```

On Windows use `py -3 jkcfg.py "C:\\path\\config.jkcfg" --format json -o sanitized.json`.

**Зберегти й повторно використати:** файл `.jkcfg` — оригінальна резервна копія налаштувань із програми JK; цей застосунок лише **читає** його. `sanitized.json` / `sanitized.md` — зрозумілий звіт для архіву чи порівняння, **не** файл для імпорту назад у BMS. Щоб зробити новий експорт після змін, знову скористайтеся опцією Export у застосунку JK BMS.

> ⚠️ `.jkcfg` is not plain text. It may include **serial numbers, passwords, user data and device identifiers**. Never commit or upload raw exports to a public repository. This tool intentionally suppresses all such fields; examine generated reports before sharing.

## What the decoder does

- Checks exactly **600 bytes**, with **two 300-byte JK02 frames** (`0x01` settings and `0x03` device info).
- Checks `55 AA EB 90` headers and both 8-bit additive checksums.
- Parses little-endian fields, converting millivolts to volts, milliamps to amps, milliamp-hours to amp-hours, temperatures to °C.
- Reads safe device metadata (model, hardware, firmware) and configuration values only; no hidden identifiers.
- Outputs Markdown by default or structured JSON, for offline use.
- **Does not** restore/write settings, contact the BMS, infer real battery SOC, or guarantee safety of settings.

See [exact byte offsets and checksum method](docs/protocol.md) and [a sanitized example 4S EVE LF334 / JK 200 A assembly](docs/battery_4s_334ah.md).

## Testing

```bash
python -m unittest discover -s tests -v
```

All tests use synthetic JK02 frames. The real export is not bundled.

## Compatibility & limitations

Designed for the **JK02 600-byte `.jkcfg` variant** (settings + device-info frames). Other JK/JBD/Seplos exports, text dumps and different frame sizes are rejected instead of guessed. Field meanings can vary with firmware; verify safety-critical values in the official BMS app. The 200 A value is a **BMS current limit setting**, not 200 Ah of battery capacity.

Protocol reference: [syssi/esphome-jk-bms JK02 BLE format](https://github.com/syssi/esphome-jk-bms/blob/main/docs/protocol-design-ble.md). Unofficial project; not affiliated with JK/Jikong. Use at your own risk.
