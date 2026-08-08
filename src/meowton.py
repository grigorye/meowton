import asyncio

import db
import settings
from cat_detector import CatDetector
from feeder import Feeder
from food_counter import FoodCounter
from food_scheduler import FoodScheduler
from hardware import gpio
from scale import Scale
from sensor_reader import SensorReader
from status_led import StatusLed


# NOTE: my catfood weigh aprox 0.33g per piece

class Meowton:
    """main class that instantiates the other classes and tasks"""
    food_reader: SensorReader
    food_scale: Scale
    food_counter: FoodCounter
    food_scheduler: FoodScheduler
    feeder: Feeder
    status_led: StatusLed

    cat_reader: SensorReader
    cat_scale: Scale
    cat_detector: CatDetector
    _tasks: list[asyncio.Task]

    def __init__(self, sim: bool):
        self._tasks = []
        self._stopped = False

        self._log_hardware_config()

        self.init_food(sim)
        self.init_cat(sim)
        self.status_led = StatusLed()

    def _log_hardware_config(self):
        print(
            "Meowton config: "
            f"backend={settings.hardware_backend}, "
            f"simulated={settings.is_simulated_hardware}, "
            f"led_pin={settings.LED_PIN}, "
            f"food_dout={settings.FOOD_DATA_PIN}, "
            f"food_sck={settings.FOOD_CLOCK_PIN}, "
            f"cat_dout={settings.CAT_DATA_PIN}, "
            f"cat_sck={settings.CAT_CLOCK_PIN}, "
            f"servo_pwm=pwmchip{settings.SERVO_PWM_CHIP}/pwm{settings.SERVO_PWM_CHANNEL}, "
            f"servo_period_ns={settings.SERVO_PWM_PERIOD_NS}, "
            f"hx711_timeout_s={settings.HX711_READ_TIMEOUT_S}, "
            f"hx711_interval_s={settings.HX711_READ_INTERVAL_S}, "
            f"hx711_recovery_s={settings.HX711_TIMEOUT_RECOVERY_S}, "
            f"disable_cat_reader={settings.DISABLE_CAT_READER}, "
            f"disable_auto_feed={settings.DISABLE_AUTO_FEED}"
        )



    # food scale stuff and default settings
    def init_food(self, sim):
        name = 'food'

        ( self.food_scale, created) = Scale.get_or_create(name=name, stable_range=0.1, stable_range_perc=0, stable_measurements=2, stable_auto_tarre_count=0.1, stable_auto_tarre_max=0.1)
        if created:
            self.food_scale.sensor_filter.filter_diff=10000
            self.food_scale.sensor_filter.save()

        self.food_reader = SensorReader(name, settings.FOOD_DATA_PIN, settings.FOOD_CLOCK_PIN, sim, self.food_scale.measurement)
        self.food_counter = FoodCounter()

        self.food_scheduler = FoodScheduler.get_or_none(id=1)
        if self.food_scheduler is None:
            self.food_scheduler = FoodScheduler.create()

        self.feeder = Feeder.get_or_create(id=1)[0]
        self.feeder.init(self.food_scale)

    # cat scale stuff and default settings
    def init_cat(self, sim):
        name = 'cat'

        ( self.cat_scale, created) = Scale.get_or_create(name=name, stable_range=30, stable_range_perc=1, stable_measurements=10, stable_auto_tarre_count=0.1, stable_auto_tarre_max=200)
        if created:

            self.cat_scale.sensor_filter.filter_diff=1000
            self.cat_scale.sensor_filter.save()

        self.cat_reader = SensorReader(name, settings.CAT_DATA_PIN, settings.CAT_CLOCK_PIN, sim, self.cat_scale.measurement)
        self.cat_detector = CatDetector()

    def _task_done(self, task: asyncio.Task):
        if task.cancelled():
            return
        exc = task.exception()
        if exc is None:
            return
        print(f"Meowton: task failed: {exc}")
        self.stop()

    async def start(self):
        tasks = []

        self.food_reader.start()
        if settings.DISABLE_CAT_READER:
            print("Meowton: cat reader disabled via MEOWTON_DISABLE_CAT_READER")
        else:
            self.cat_reader.start()

        if not settings.DISABLE_CAT_READER:
            tasks.append(asyncio.create_task(self.cat_detector.task(self.cat_scale)))
        tasks.append(asyncio.create_task(self.feeder.task()))
        tasks.append(asyncio.create_task(self.food_counter.task(self.food_scale, self.feeder, self.cat_detector)))
        tasks.append(asyncio.create_task(self.food_scheduler.task(self.feeder, self.cat_detector)))

        tasks.append(asyncio.create_task(self.status_led.task(self.feeder, self.cat_detector)))

        for task in tasks:
            task.add_done_callback(self._task_done)

        self._tasks = tasks

        return tasks

    def stop(self):
        if self._stopped:
            return
        self._stopped = True

        for task in self._tasks:
            task.cancel()
        self._tasks = []

        self.food_reader.stop()
        self.cat_reader.stop()
        self.status_led.close()
        self.feeder.stop()
        gpio.cleanup()


meowton = Meowton(settings.is_simulated_hardware)
