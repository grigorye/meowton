import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from scale import Scale
except ModuleNotFoundError as exc:
    if exc.name == "peewee":
        Scale = None
    else:
        raise


class ScaleStabilityTests(unittest.TestCase):
    @unittest.skipIf(Scale is None, "peewee not available in local test environment")
    def test_stabilizes_with_large_calibration_factor_using_raw_threshold(self):
        scale_name = "test_scale_stability"
        scale, _ = Scale.get_or_create(
            name=scale_name,
            stable_range=0.1,
            stable_range_perc=0,
            stable_measurements=3,
            stable_auto_tarre_count=0.1,
            stable_auto_tarre_max=0.1,
        )

        scale.sensor_filter.filter_diff = 10000
        scale.sensor_filter.save()

        # Simulate a broken calibration factor that would make gram spread look huge.
        scale.calibration.factor = 10.0
        scale.calibration.offset = 0
        scale.stable_reset(0)

        for raw in [100000, 100020, 99990, 100010, 100000]:
            scale.measurement(raw)

        self.assertTrue(scale.stable)


if __name__ == "__main__":
    unittest.main()
