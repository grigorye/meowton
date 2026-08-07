import statistics

import settings
from hardware.hx711 import HX711, HX711TimeoutError

SAMPLES = 1000


def sample(name: str, data_pin: int, clock_pin: int):
    sensor = HX711(dout_pin=data_pin, pd_sck_pin=clock_pin, gain=128)
    values = []
    timeouts = 0
    try:
        for _ in range(SAMPLES):
            try:
                values.append(sensor.read_raw(timeout_seconds=settings.HX711_READ_TIMEOUT_S))
            except HX711TimeoutError:
                timeouts += 1
    finally:
        sensor.close()

    if values:
        avg = statistics.mean(values)
        stdev = statistics.pstdev(values)
        print(f"{name}: samples={len(values)} timeouts={timeouts} avg={avg:.2f} stdev={stdev:.2f}")
    else:
        print(f"{name}: no samples, timeouts={timeouts}")


def main():
    if settings.hardware_backend != "orangepi-zero3":
        raise RuntimeError("Set MEOWTON_HARDWARE=orangepi-zero3 before running this script")

    sample("food", settings.FOOD_DATA_PIN, settings.FOOD_CLOCK_PIN)
    sample("cat", settings.CAT_DATA_PIN, settings.CAT_CLOCK_PIN)


if __name__ == "__main__":
    main()
