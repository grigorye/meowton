import threading
from typing import Optional

import settings

INPUT = 0
OUTPUT = 1


class GPIOError(RuntimeError):
    pass


class GPIOBackend:
    def setup_input(self, pin: int) -> None:
        raise NotImplementedError()

    def setup_output(self, pin: int) -> None:
        raise NotImplementedError()

    def read(self, pin: int) -> bool:
        raise NotImplementedError()

    def write(self, pin: int, value: bool) -> None:
        raise NotImplementedError()

    def close_output(self, pin: int) -> None:
        raise NotImplementedError()

    def cleanup(self) -> None:
        raise NotImplementedError()


class SimulatedGPIOBackend(GPIOBackend):
    def __init__(self):
        self._pins: dict[int, bool] = {}

    def setup_input(self, pin: int) -> None:
        self._pins.setdefault(pin, False)

    def setup_output(self, pin: int) -> None:
        self._pins.setdefault(pin, False)

    def read(self, pin: int) -> bool:
        return bool(self._pins.get(pin, False))

    def write(self, pin: int, value: bool) -> None:
        self._pins[pin] = bool(value)

    def close_output(self, pin: int) -> None:
        self._pins[pin] = False

    def cleanup(self) -> None:
        self._pins.clear()


class WiringOPBackend(GPIOBackend):
    _setup_lock = threading.Lock()
    _setup_done = False

    def __init__(self):
        try:
            import wiringpi  # type: ignore
        except ImportError as exc:
            raise GPIOError("wiringOP-Python is required for orangepi-zero3 backend") from exc

        self._wiringpi = wiringpi
        self._ensure_setup()

    def _ensure_setup(self) -> None:
        with self._setup_lock:
            if self._setup_done:
                return
            result = self._wiringpi.wiringPiSetup()
            if result != 0:
                raise GPIOError(f"wiringPiSetup failed with code {result}")
            self._setup_done = True

    def setup_input(self, pin: int) -> None:
        self._wiringpi.pinMode(pin, INPUT)

    def setup_output(self, pin: int) -> None:
        self._wiringpi.pinMode(pin, OUTPUT)

    def read(self, pin: int) -> bool:
        return bool(self._wiringpi.digitalRead(pin))

    def write(self, pin: int, value: bool) -> None:
        self._wiringpi.digitalWrite(pin, 1 if value else 0)

    def close_output(self, pin: int) -> None:
        self.write(pin, False)

    def cleanup(self) -> None:
        # wiringPi does not expose a strong per-process cleanup API.
        pass


_backend_lock = threading.Lock()
_backend_instance: Optional[GPIOBackend] = None


def _build_default_backend() -> GPIOBackend:
    if settings.hardware_backend == "simulated":
        return SimulatedGPIOBackend()
    if settings.hardware_backend == "orangepi-zero3":
        return WiringOPBackend()
    raise GPIOError(f"Unsupported hardware backend: {settings.hardware_backend}")


def get_backend() -> GPIOBackend:
    global _backend_instance

    with _backend_lock:
        if _backend_instance is None:
            _backend_instance = _build_default_backend()
        return _backend_instance


def cleanup() -> None:
    global _backend_instance

    with _backend_lock:
        if _backend_instance is None:
            return
        _backend_instance.cleanup()
        _backend_instance = None


class DigitalInput:
    def __init__(self, pin: int, backend: Optional[GPIOBackend] = None):
        self.pin = pin
        self.backend = backend or get_backend()
        self.backend.setup_input(self.pin)

    def read(self) -> bool:
        return self.backend.read(self.pin)


class DigitalOutput:
    def __init__(self, pin: int, backend: Optional[GPIOBackend] = None):
        self.pin = pin
        self.backend = backend or get_backend()
        self.backend.setup_output(self.pin)
        self.write(False)

    def write(self, value: bool) -> None:
        self.backend.write(self.pin, value)

    def close(self) -> None:
        self.backend.close_output(self.pin)
