import time

import settings
from hardware.pwm import create_pwm


def main():
    if settings.hardware_backend != "orangepi-zero3":
        raise RuntimeError("Set MEOWTON_HARDWARE=orangepi-zero3 before running this script")

    pwm = create_pwm(
        backend_name=settings.hardware_backend,
        chip=settings.SERVO_PWM_CHIP,
        channel=settings.SERVO_PWM_CHANNEL,
        period_ns=settings.SERVO_PWM_PERIOD_NS,
        base_path=settings.SERVO_PWM_BASE_PATH,
    )

    try:
        pwm.enable()
        for duty in (5, 6, 8):
            print(f"Setting duty to {duty}%")
            pwm.set_duty_percent(duty)
            time.sleep(1.0)
        pwm.set_duty_percent(0)
    finally:
        pwm.close()


if __name__ == "__main__":
    main()
