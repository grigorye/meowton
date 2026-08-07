import asyncio
import sys
import time
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hardware.hx711 import HX711TimeoutError
from sensor_reader import SensorReader


class TimeoutHX711:
    instances = []

    def __init__(self, dout_pin, pd_sck_pin, gain=128):
        self.dout_pin = dout_pin
        self.pd_sck_pin = pd_sck_pin
        self.gain = gain
        self.closed = False
        self.read_count = 0
        TimeoutHX711.instances.append(self)

    def read_raw(self, timeout_seconds=0.2):
        self.read_count += 1
        raise HX711TimeoutError("timeout")

    def close(self):
        self.closed = True


class SensorReaderShutdownTests(IsolatedAsyncioTestCase):
    async def test_stop_while_hx711_timeouts(self):
        TimeoutHX711.instances.clear()

        reader = SensorReader("food", 9, 10, False, lambda value: None)

        with patch("sensor_reader.HX711", TimeoutHX711):
            reader.start()
            await asyncio.sleep(0.05)

            started = time.monotonic()
            reader.stop()
            elapsed = time.monotonic() - started

        self.assertLess(elapsed, 1.0)
        self.assertEqual(len(TimeoutHX711.instances), 1)
        self.assertGreater(TimeoutHX711.instances[0].read_count, 0)
        self.assertTrue(TimeoutHX711.instances[0].closed)


if __name__ == "__main__":
    import unittest

    unittest.main()
