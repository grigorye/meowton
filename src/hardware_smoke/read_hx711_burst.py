import statistics
import os
import time

import settings
from hardware.hx711 import HX711, HX711TimeoutError

SAMPLES = int(os.getenv("MEOWTON_BURST_SAMPLES", "1000"))
PROGRESS_EVERY = int(os.getenv("MEOWTON_BURST_PROGRESS_EVERY", "50"))


def sample(name: str, data_pin: int, clock_pin: int):
    sensor = HX711(dout_pin=data_pin, pd_sck_pin=clock_pin, gain=128)
    values = []
    timeouts = 0
    started = time.monotonic()
    interrupted = False
    try:
        for index in range(1, SAMPLES + 1):
            try:
                values.append(sensor.read_raw(timeout_seconds=settings.HX711_READ_TIMEOUT_S))
            except HX711TimeoutError:
                timeouts += 1

            if PROGRESS_EVERY > 0 and (index % PROGRESS_EVERY == 0):
                elapsed = time.monotonic() - started
                print(f"{name}: progress {index}/{SAMPLES} reads, timeouts={timeouts}, elapsed={elapsed:.1f}s")
    except KeyboardInterrupt:
        interrupted = True
        print(f"{name}: interrupted by user, printing partial results")
    finally:
        sensor.close()

    elapsed = time.monotonic() - started
    if values:
        avg = statistics.mean(values)
        stdev = statistics.pstdev(values)
        print(
            f"{name}: samples={len(values)} timeouts={timeouts} avg={avg:.2f} stdev={stdev:.2f} "
            f"elapsed={elapsed:.1f}s interrupted={interrupted}"
        )
    else:
        print(f"{name}: no samples, timeouts={timeouts} elapsed={elapsed:.1f}s interrupted={interrupted}")


def main():
    if settings.hardware_backend != "orangepi-zero3":
        raise RuntimeError("Set MEOWTON_HARDWARE=orangepi-zero3 before running this script")

    sample("food", settings.FOOD_DATA_PIN, settings.FOOD_CLOCK_PIN)
    sample("cat", settings.CAT_DATA_PIN, settings.CAT_CLOCK_PIN)


if __name__ == "__main__":
    main()
