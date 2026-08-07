import asyncio

import settings
from cat_detector import CatDetector
from feeder import Feeder
from hardware.gpio import DigitalOutput
from util import Status


class StatusLed:
    def __init__(self):
        self._led = None
        if not settings.is_simulated_hardware:
            self._led = DigitalOutput(settings.LED_PIN)

    async def task(self, feeder: Feeder, cat_detector: CatDetector):
        if settings.is_simulated_hardware:
            return

        while True:
            if feeder.status == Status.OK and cat_detector.status == Status.OK:
                self._led.write(True)
                await asyncio.sleep(1)
                self._led.write(False)
                await asyncio.sleep(0.1)
            else:
                self._led.write(True)
                await asyncio.sleep(0.1)
                self._led.write(False)
                await asyncio.sleep(0.1)

    def close(self):
        if self._led is not None:
            self._led.close()
            self._led = None
