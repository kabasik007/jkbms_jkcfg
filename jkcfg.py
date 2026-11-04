#!/usr/bin/env python3
"""Read-only, privacy-safe decoder for JK02 JK BMS .jkcfg exports.

Supported input: 600-byte dump = 300-byte settings frame (0x01) and
300-byte device-info frame (0x03). No Bluetooth, no writes to BMS.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

HEADER = bytes.fromhex('55 AA EB 90')
FRAME_SIZE = 300
EXPECTED_SIZE = 600

# Settings-frame offsets: (key, byte offset, signed?, coefficient, group).
# Coefficient is multiplied by the raw little-endian integer.
FIELDS: tuple[tuple[str, int, bool, float, str], ...] = (
    ('smart_sleep_voltage_v', 6, False, .001, 'voltage'),
    ('cell_uvp_v', 10, False, .001, 'voltage'),
    ('cell_uvpr_v', 14, False, .001, 'voltage'),
    ('cell_ovp_v', 18, False, .001, 'voltage'),
    ('cell_ovpr_v', 22, False, .001, 'voltage'),
    ('balance_trigger_delta_v', 26, False, .001, 'balancing'),
    ('soc_100_voltage_v', 30, False, .001, 'voltage'),
    ('soc_0_voltage_v', 34, False, .001, 'voltage'),
    ('cell_rcv_v', 38, False, .001, 'voltage'),
    ('cell_rfv_v', 42, False, .001, 'voltage'),
    ('power_off_voltage_v', 46, False, .001, 'voltage'),
    ('charge_overcurrent_a', 50, False, .001, 'current'),
    ('charge_ocp_delay_s', 54, False, 1, 'current'),
    ('charge_ocp_recovery_s', 58, False, 1, 'current'),
    ('discharge_overcurrent_a', 62, False, .001, 'current'),
    ('discharge_ocp_delay_s', 66, False, 1, 'current'),
    ('discharge_ocp_recovery_s', 70, False, 1, 'current'),
    ('short_circuit_recovery_s', 74, False, 1, 'current'),
    ('max_balance_current_a', 78, False, .001, 'balancing'),
    ('charge_overtemp_c', 82, False, .1, 'temperature'),
    ('charge_overtemp_recovery_c', 86, False, .1, 'temperature'),
    ('discharge_overtemp_c', 90, False, .1, 'temperature'),
    ('discharge_overtemp_recovery_c', 94, False, .1, 'temperature'),
    ('charge_undertemp_c', 98, True, .1, 'temperature'),
    ('charge_undertemp_recovery_c', 102, True, .1, 'temperature'),
    ('mos_overtemp_c', 106, True, .1, 'temperature'),
    ('mos_overtemp_recovery_c', 110, True, .1, 'temperature'),
    ('nominal_capacity_ah', 130, False, .001, 'battery'),
    ('short_circuit_delay_us', 134, False, 1, 'current'),
    ('balance_start_voltage_v', 138, False, .001, 'balancing'),
)

CONTROL_BITS = {
    'heating_enabled': 0,
    'temperature_sensors_disabled': 1,
    'gps_heartbeat': 2,
    'rs485_port_selected': 3,
    'display_always_on': 4,
    'special_charger': 5,
    'smart_sleep_enabled': 6,
    'pcl_module_disabled': 7,
    'timed_data_storage': 8,
    'charging_float_mode': 9,
}


class JKCFGError(ValueError):
    """Not a supported or integrity-checked JK02 .jkcfg export."""


def _frame(data: bytes, frame_number: int, expected_type: int) -> bytes:
    start = frame_number * FRAME_SIZE
    part = data[start:start + FRAME_SIZE]
    if part[:4] != HEADER:
        raise JKCFGError(f'Frame {frame_number + 1}: invalid JK02 header')
    if part[4] != expected_type:
        raise JKCFGError(f'Frame {frame_number + 1}: unexpected type 0x{part[4]:02x}')
    expected = sum(part[:-1]) & 0xff
    if part[-1] != expected:
        raise JKCFGError(f'Frame {frame_number + 1}: checksum mismatch')
    return part


def _u32(frame: bytes, offset: int, signed: bool = False) -> int:
    return struct.unpack_from('<i' if signed else '<I', frame, offset)[0]


def _safe_text(data: bytes) -> str:
    # Only three explicitly whitelisted device-info fields are ever decoded.
    candidate = data.split(b'\x00', 1)[0].decode('ascii', errors='replace')
    return candidate if re.fullmatch(r'[A-Za-z0-9._ /-]{1,20}', candidate) else 'unknown'


def decode(data: bytes) -> dict[str, Any]:
    """Return a whitelist-only report. Never serialize raw frames or credentials."""
    if len(data) != EXPECTED_SIZE:
        raise JKCFGError(f'Expected {EXPECTED_SIZE} bytes; received {len(data)}')
    settings = _frame(data, 0, 0x01)
    device = _frame(data, 1, 0x03)

    groups: dict[str, dict[str, Any]] = {
        'battery': {'cell_count': settings[114]},
        'voltage': {},
        'current': {},
        'balancing': {'enabled': bool(settings[126])},
        'temperature': {},
        'switches': {
            'charge_enabled': bool(settings[118]),
            'discharge_enabled': bool(settings[122]),
        },
    }
    for name, offset, signed, coefficient, group in FIELDS:
        raw = _u32(settings, offset, signed)
        groups[group][name] = (round(raw * coefficient, 4)
                               if coefficient != 1 else raw)
    controls_mask = struct.unpack_from('<H', settings, 282)[0]
    groups['switches']['controls'] = {
        name: bool(controls_mask & (1 << bit))
        for name, bit in CONTROL_BITS.items()
    }
    groups['temperature']['discharge_undertemp_c'] = struct.unpack_from('<b', settings, 296)[0]
    groups['temperature']['discharge_undertemp_recovery_c'] = struct.unpack_from('<b', settings, 297)[0]
    return {
        'format': 'JK02 .jkcfg (read-only)',
        'validation': {'bytes': len(data), 'settings_crc': 'valid', 'device_crc': 'valid'},
        'device': {
            'model': _safe_text(device[6:22]),
            'hardware_version': _safe_text(device[22:30]),
            'firmware_version': _safe_text(device[30:38]),
        },
        'settings': groups,
    }


def render_markdown(report: dict[str, Any]) -> str:
    device = report['device']
    lines = [
        '# JK BMS configuration (sanitized)', '',
        f"- Model: **{device['model']}**",
        f"- Hardware: {device['hardware_version']}",
        f"- Firmware: {device['firmware_version']}",
        '- Checksum verification: **passed (2/2)**', '',
        '> Read-only report; no serial numbers, passwords, identifiers, user data, or raw frames.',
        '> 200 A is a BMS current protection setting, not the battery capacity.', '',
    ]
    for section, values in report['settings'].items():
        lines.extend((f'## {section.replace("_", " ").title()}', '', '| Setting | Value |', '|---|---|'))
        for key, value in values.items():
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    lines.append(f'| {subkey} | {str(subvalue).lower()} |')
            else:
                lines.append(f'| {key} | {str(value).lower() if isinstance(value, bool) else value} |')
        lines.append('')
    lines.append('Values are configuration settings, not live measurements. Do not import edited reports into a BMS.')
    return '\n'.join(lines) + '\n'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Offline decoder for 600-byte JK02 .jkcfg files')
    parser.add_argument('file', type=Path, help='Original .jkcfg file (read-only)')
    parser.add_argument('--format', choices=('markdown', 'json'), default='markdown')
    parser.add_argument('--output', '-o', type=Path, help='Save sanitized report to a file')
    args = parser.parse_args(argv)
    try:
        # Prevent overwriting the raw backup, including aliases/symlinks/hard links.
        if args.output and args.output.exists() and args.file.exists() and args.output.samefile(args.file):
            raise JKCFGError('Output must not overwrite the original .jkcfg backup')
        report = decode(args.file.read_bytes())
        text = (json.dumps(report, ensure_ascii=False, indent=2) + '\n'
                if args.format == 'json' else render_markdown(report))
        if args.output:
            args.output.write_text(text, encoding='utf-8')
            print('Sanitized report saved.')  # Do not print paths or private file names
        else:
            print(text, end='')
    except JKCFGError as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 2
    except OSError:
        print('Error: unable to access input/output file', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
