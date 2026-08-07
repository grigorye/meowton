import time

import settings
from hardware.gpio import DigitalOutput


def main():
    if settings.hardware_backend != "orangepi-zero3":
        raise RuntimeError("Set MEOWTON_HARDWARE=orangepi-zero3 before running this script")

    print(f"Blinking LED on wPi pin {settings.LED_PIN}")
    led = DigitalOutput(settings.LED_PIN)
    try:
        for _ in range(10):
            led.write(True)
            time.sleep(0.2)
            led.write(False)
            time.sleep(0.2)
    finally:
        led.close()


if __name__ == "__main__":
    main()
