import settings
from hardware.hx711 import HX711


def read_sensor(name: str, data_pin: int, clock_pin: int):
    sensor = HX711(dout_pin=data_pin, pd_sck_pin=clock_pin, gain=128)
    try:
        value = sensor.read_raw(timeout_seconds=settings.HX711_READ_TIMEOUT_S)
    finally:
        sensor.close()
    print(f"{name}: raw={value}")


def main():
    if settings.hardware_backend != "orangepi-zero3":
        raise RuntimeError("Set MEOWTON_HARDWARE=orangepi-zero3 before running this script")

    read_sensor("food", settings.FOOD_DATA_PIN, settings.FOOD_CLOCK_PIN)
    read_sensor("cat", settings.CAT_DATA_PIN, settings.CAT_CLOCK_PIN)


if __name__ == "__main__":
    main()
