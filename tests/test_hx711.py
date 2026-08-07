import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hardware.hx711 import HX711, HX711TimeoutError


class FakeDataInput:
    def __init__(self, values):
        self._values = list(values)
        self._fallback = self._values[-1] if self._values else False

    def read(self):
        if self._values:
            return self._values.pop(0)
        return self._fallback


class FakeClockOutput:
    def __init__(self):
        self.writes = []
        self.closed = False

    def write(self, value):
        self.writes.append(bool(value))

    def close(self):
        self.closed = True


def bits_for_24(value):
    return [bool((value >> bit) & 0x1) for bit in range(23, -1, -1)]


class HX711Tests(unittest.TestCase):
    def test_reads_positive_value(self):
        target = 0x123456
        data = FakeDataInput([False] + bits_for_24(target))
        clock = FakeClockOutput()

        hx = HX711(dout_pin=0, pd_sck_pin=1, data_input=data, clock_output=clock)
        actual = hx.read_raw(timeout_seconds=0.01)

        self.assertEqual(actual, target)

    def test_reads_negative_value(self):
        target_24 = 0xF00000
        data = FakeDataInput([False] + bits_for_24(target_24))
        clock = FakeClockOutput()

        hx = HX711(dout_pin=0, pd_sck_pin=1, data_input=data, clock_output=clock)
        actual = hx.read_raw(timeout_seconds=0.01)

        self.assertEqual(actual, target_24 - (1 << 24))

    def test_timeout_when_not_ready(self):
        data = FakeDataInput([True] * 1000)
        clock = FakeClockOutput()

        hx = HX711(dout_pin=0, pd_sck_pin=1, data_input=data, clock_output=clock)

        with self.assertRaises(HX711TimeoutError):
            hx.read_raw(timeout_seconds=0.001)


if __name__ == "__main__":
    unittest.main()
