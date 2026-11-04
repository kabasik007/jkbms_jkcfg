"""Self-contained tests: synthetic data only, no real user configuration."""
import json
import struct
import unittest

from jkcfg import HEADER, JKCFGError, decode, render_markdown


def fixture() -> bytes:
    settings, info = bytearray(300), bytearray(300)
    for frame, typ in ((settings, 1), (info, 3)):
        frame[:4], frame[4] = HEADER, typ
    for offset, value in {
        10: 2500, 14: 2900, 18: 3650, 22: 3450, 26: 10,
        30: 3590, 34: 2700, 46: 2490, 50: 200000, 62: 200000,
        82: 650, 98: -100, 114: 4, 118: 1, 122: 1,
        126: 1, 130: 334000, 138: 3400,
    }.items():
        struct.pack_into('<i' if value < 0 else '<I', settings, offset, value)
    info[6:17] = b'JK-TEST-200'
    info[22:25] = b'19H'
    info[30:35] = b'19.26'
    info[62:78] = b'SECRET_PASSWORD_'
    info[86:102] = b'PRIVATE_SERIAL__'
    info[118:134] = b'SECRET_SETUPKEY_'
    for frame in (settings, info):
        frame[299] = sum(frame[:299]) & 0xff
    return bytes(settings + info)


class JKCFGTests(unittest.TestCase):
    def test_known_settings_and_safety(self):
        report = decode(fixture())
        self.assertEqual(report['settings']['battery']['cell_count'], 4)
        self.assertEqual(report['settings']['battery']['nominal_capacity_ah'], 334)
        self.assertEqual(report['settings']['voltage']['cell_uvp_v'], 2.5)
        self.assertEqual(report['settings']['voltage']['cell_uvpr_v'], 2.9)
        self.assertEqual(report['settings']['current']['discharge_overcurrent_a'], 200)
        self.assertEqual(report['settings']['temperature']['charge_undertemp_c'], -10)
        combined = json.dumps(report) + render_markdown(report)
        for secret in ('SECRET_PASSWORD_', 'PRIVATE_SERIAL__', 'SECRET_SETUPKEY_'):
            self.assertNotIn(secret, combined)

    def test_checksums(self):
        data = bytearray(fixture())
        data[11] ^= 1
        with self.assertRaisesRegex(JKCFGError, 'checksum'):
            decode(bytes(data))
        data = bytearray(fixture())
        data[320] ^= 1
        with self.assertRaisesRegex(JKCFGError, 'checksum'):
            decode(bytes(data))

    def test_rejects_unsupported_input(self):
        with self.assertRaisesRegex(JKCFGError, 'Expected'):
            decode(b'text')
        data = bytearray(fixture())
        data[4] = 2
        data[299] = sum(data[:299]) & 0xff
        with self.assertRaisesRegex(JKCFGError, 'unexpected type'):
            decode(bytes(data))
        data = bytearray(fixture())
        data[300] = 0
        with self.assertRaisesRegex(JKCFGError, 'header'):
            decode(bytes(data))


if __name__ == '__main__':
    unittest.main()
