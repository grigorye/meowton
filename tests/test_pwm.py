import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hardware.pwm import SimulatedPWM, SysfsPWM


class PWMTests(unittest.TestCase):
    def test_simulated_pwm_duty_percent(self):
        pwm = SimulatedPWM(chip=0, channel=1, period_ns=20_000_000)
        pwm.set_duty_percent(5)
        self.assertEqual(pwm.last_duty_ns, 1_000_000)
        pwm.set_duty_percent(8)
        self.assertEqual(pwm.last_duty_ns, 1_600_000)

    def test_sysfs_pwm_existing_channel(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            channel_dir = base / "pwmchip0" / "pwm1"
            channel_dir.mkdir(parents=True)

            (channel_dir / "period").write_text("0\n")
            (channel_dir / "duty_cycle").write_text("0\n")
            (channel_dir / "enable").write_text("0\n")

            pwm = SysfsPWM(chip=0, channel=1, period_ns=20_000_000, base_path=str(base))
            pwm.set_duty_percent(6)
            pwm.enable()

            self.assertEqual((channel_dir / "period").read_text().strip(), "20000000")
            self.assertEqual((channel_dir / "duty_cycle").read_text().strip(), "1200000")
            self.assertEqual((channel_dir / "enable").read_text().strip(), "1")

            pwm.close()
            self.assertEqual((channel_dir / "enable").read_text().strip(), "0")


if __name__ == "__main__":
    unittest.main()
