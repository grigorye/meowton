import errno
from pathlib import Path


class PWMError(RuntimeError):
    pass


class SysfsPWM:
    def __init__(
        self,
        chip: int,
        channel: int,
        period_ns: int,
        base_path: str = "/sys/class/pwm",
    ):
        self.chip = chip
        self.channel = channel
        self.period_ns = period_ns
        self._base = Path(base_path)
        self._chip_dir = self._base / f"pwmchip{self.chip}"
        self._channel_dir = self._chip_dir / f"pwm{self.channel}"

        self._ensure_exported()
        self.set_period_ns(period_ns)
        self.set_duty_ns(0)
        self.disable()

    def _write_text(self, path: Path, value: str) -> None:
        try:
            path.write_text(value)
        except OSError as exc:
            raise PWMError(f"Failed writing {path}: {exc}") from exc

    def _ensure_exported(self) -> None:
        if not self._chip_dir.exists():
            raise PWMError(f"PWM chip path does not exist: {self._chip_dir}")

        if self._channel_dir.exists():
            return

        export_path = self._chip_dir / "export"
        try:
            self._write_text(export_path, f"{self.channel}\n")
        except PWMError as exc:
            if self._channel_dir.exists():
                return
            cause = exc.__cause__
            if isinstance(cause, OSError) and cause.errno == errno.EBUSY:
                return
            raise

    def set_period_ns(self, period_ns: int) -> None:
        self.period_ns = int(period_ns)
        self._write_text(self._channel_dir / "period", f"{self.period_ns}\n")

    def set_duty_ns(self, duty_ns: int) -> None:
        duty_ns = max(0, min(int(duty_ns), self.period_ns))
        self._write_text(self._channel_dir / "duty_cycle", f"{duty_ns}\n")

    def set_duty_percent(self, duty_percent: float) -> None:
        duty_ns = round(self.period_ns * duty_percent / 100.0)
        self.set_duty_ns(duty_ns)

    def enable(self) -> None:
        self._write_text(self._channel_dir / "enable", "1\n")

    def disable(self) -> None:
        self._write_text(self._channel_dir / "enable", "0\n")

    def close(self) -> None:
        self.set_duty_ns(0)
        self.disable()


class SimulatedPWM:
    def __init__(
        self,
        chip: int,
        channel: int,
        period_ns: int,
        base_path: str = "/sys/class/pwm",
    ):
        self.chip = chip
        self.channel = channel
        self.period_ns = period_ns
        self.last_duty_ns = 0
        self.enabled = False

    def set_period_ns(self, period_ns: int) -> None:
        self.period_ns = int(period_ns)

    def set_duty_ns(self, duty_ns: int) -> None:
        self.last_duty_ns = max(0, min(int(duty_ns), self.period_ns))

    def set_duty_percent(self, duty_percent: float) -> None:
        duty_ns = round(self.period_ns * duty_percent / 100.0)
        self.set_duty_ns(duty_ns)

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def close(self) -> None:
        self.set_duty_ns(0)
        self.disable()


def create_pwm(
    backend_name: str,
    chip: int,
    channel: int,
    period_ns: int,
    base_path: str = "/sys/class/pwm",
):
    if backend_name == "simulated":
        return SimulatedPWM(chip=chip, channel=channel, period_ns=period_ns, base_path=base_path)
    if backend_name == "orangepi-zero3":
        return SysfsPWM(chip=chip, channel=channel, period_ns=period_ns, base_path=base_path)
    raise PWMError(f"Unsupported hardware backend: {backend_name}")
