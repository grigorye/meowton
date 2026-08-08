import sys
import os


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

dev_mode = "dev" in sys.argv
if dev_mode:
    print("Using dev mode")

hardware_backend = os.getenv("MEOWTON_HARDWARE", "simulated" if dev_mode else "orangepi-zero3")
is_simulated_hardware = hardware_backend == "simulated"

LED_PIN = int(os.getenv("MEOWTON_LED_PIN", "2"))

FOOD_DATA_PIN = int(os.getenv("MEOWTON_FOOD_DATA_PIN", "9"))
FOOD_CLOCK_PIN = int(os.getenv("MEOWTON_FOOD_CLOCK_PIN", "10"))
CAT_DATA_PIN = int(os.getenv("MEOWTON_CAT_DATA_PIN", "7"))
CAT_CLOCK_PIN = int(os.getenv("MEOWTON_CAT_CLOCK_PIN", "5"))

SERVO_PWM_CHIP = int(os.getenv("MEOWTON_SERVO_PWM_CHIP", "0"))
SERVO_PWM_CHANNEL = int(os.getenv("MEOWTON_SERVO_PWM_CHANNEL", "1"))
SERVO_PWM_BASE_PATH = os.getenv("MEOWTON_SERVO_PWM_BASE_PATH", "/sys/class/pwm")
SERVO_PWM_PERIOD_NS = int(os.getenv("MEOWTON_SERVO_PWM_PERIOD_NS", "20000000"))

HX711_READ_TIMEOUT_S = float(os.getenv("MEOWTON_HX711_READ_TIMEOUT_S", "0.2"))
HX711_READ_INTERVAL_S = float(os.getenv("MEOWTON_HX711_READ_INTERVAL_S", "0.01"))
HX711_TIMEOUT_RECOVERY_S = float(os.getenv("MEOWTON_HX711_TIMEOUT_RECOVERY_S", "0.005"))
HX711_ADAPTIVE_TIMING_ENABLED = _env_bool("MEOWTON_HX711_ADAPTIVE_TIMING_ENABLED", True)
HX711_ADAPTIVE_TRIGGER_TIMEOUTS = int(os.getenv("MEOWTON_HX711_ADAPTIVE_TRIGGER_TIMEOUTS", "2"))
HX711_ADAPTIVE_READ_TIMEOUT_S = float(os.getenv("MEOWTON_HX711_ADAPTIVE_READ_TIMEOUT_S", "1.0"))
HX711_ADAPTIVE_READ_INTERVAL_S = float(os.getenv("MEOWTON_HX711_ADAPTIVE_READ_INTERVAL_S", "0.02"))
HX711_ADAPTIVE_TIMEOUT_RECOVERY_S = float(os.getenv("MEOWTON_HX711_ADAPTIVE_TIMEOUT_RECOVERY_S", "0.05"))

DISABLE_CAT_READER = _env_bool("MEOWTON_DISABLE_CAT_READER", False)
DISABLE_AUTO_FEED = _env_bool("MEOWTON_DISABLE_AUTO_FEED", False)
DISABLE_PWM = _env_bool("MEOWTON_DISABLE_PWM", False)


version="2.0"

