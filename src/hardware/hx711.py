import threading
import time
from typing import Optional

from hardware.gpio import DigitalInput, DigitalOutput


class HX711Error(RuntimeError):
    pass


class HX711TimeoutError(HX711Error):
    pass


_GAIN_TO_PULSES = {
    128: 1,
    32: 2,
    64: 3,
}


class HX711:
    _global_read_lock = threading.Lock()

    def __init__(
        self,
        dout_pin: int,
        pd_sck_pin: int,
        gain: int = 128,
        data_input: Optional[DigitalInput] = None,
        clock_output: Optional[DigitalOutput] = None,
    ):
        if gain not in _GAIN_TO_PULSES:
            raise HX711Error(f"Unsupported gain: {gain}")

        self._gain_pulses = _GAIN_TO_PULSES[gain]
        self._data = data_input or DigitalInput(dout_pin)
        self._clock = clock_output or DigitalOutput(pd_sck_pin)
        self._clock.write(False)
        self._lock = threading.Lock()
        self._warned_clock_high = False
        self._clock_high_warning_count = 0

    def _warn_if_clock_high_too_long(self, started_high_ns: int) -> None:
        high_ns = time.perf_counter_ns() - started_high_ns
        if high_ns >= 60_000 and not self._warned_clock_high:
            print(f"HX711 warning: clock high period reached {high_ns} ns")
            self._warned_clock_high = True
            self._clock_high_warning_count += 1

    def consume_clock_high_warning_count(self) -> int:
        count = self._clock_high_warning_count
        self._clock_high_warning_count = 0
        return count

    def _clock_pulse(self) -> None:
        # Keep the high period as short as possible; >=60 us powers down HX711.
        started_high_ns = time.perf_counter_ns()
        self._clock.write(True)
        self._clock.write(False)
        self._warn_if_clock_high_too_long(started_high_ns)

    def recover(self) -> None:
        # Force a power-down and power-up cycle after repeated timeouts.
        with self._global_read_lock:
            with self._lock:
                self._clock.write(True)
                time.sleep(0.00008)
                self._clock.write(False)

    def _wait_ready(self, timeout_seconds: float) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if not self._data.read():
                return True
            time.sleep(0.001)
        return False

    def read_raw(self, timeout_seconds: float = 0.2) -> int:
        with self._global_read_lock:
            with self._lock:
                if not self._wait_ready(timeout_seconds):
                    raise HX711TimeoutError("Timed out waiting for HX711 DOUT to go low")

                value = 0
                for _ in range(24):
                    started_high_ns = time.perf_counter_ns()
                    self._clock.write(True)
                    self._clock.write(False)
                    self._warn_if_clock_high_too_long(started_high_ns)
                    bit = 1 if self._data.read() else 0
                    value = (value << 1) | bit

                for _ in range(self._gain_pulses):
                    self._clock_pulse()

                if value & 0x800000:
                    value -= 1 << 24

                return value

    def close(self) -> None:
        self._clock.write(False)
        self._clock.close()
