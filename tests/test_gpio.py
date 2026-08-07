import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hardware.gpio import DigitalInput, DigitalOutput, SimulatedGPIOBackend


class GPIOTests(unittest.TestCase):
    def test_simulated_output_to_input(self):
        backend = SimulatedGPIOBackend()

        output = DigitalOutput(2, backend=backend)
        input_pin = DigitalInput(2, backend=backend)

        output.write(True)
        self.assertTrue(input_pin.read())

        output.write(False)
        self.assertFalse(input_pin.read())

        output.close()
        self.assertFalse(input_pin.read())


if __name__ == "__main__":
    unittest.main()
