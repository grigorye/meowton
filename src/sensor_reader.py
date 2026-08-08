import asyncio
import random
import threading
import time
from typing import Callable

import settings
from hardware.hx711 import HX711, HX711TimeoutError

MeasurementCallback = Callable[[int], None]


class SensorReader:
    """read data from hardware via a thread, and calls measurement_callback. (in a threadsafe way)"""

    __loop: asyncio.AbstractEventLoop

    def __init__(self, name: str, data_pin: int, clk_pin: int, sim: bool,
                 measurement_callback: MeasurementCallback):

        self.sim_value = 0
        self.sim_noise = 20

        self.__data_pin = data_pin
        self.__clk_pin = clk_pin
        self.__sim = sim

        self.__thread: threading.Thread | None = None
        self.__stop_event = threading.Event()
        self.__name = name
        self.__hx711: HX711 | None = None
        self.__read_timeout_s = settings.HX711_READ_TIMEOUT_S
        self.__read_interval_s = settings.HX711_READ_INTERVAL_S
        self.__timeout_recovery_s = settings.HX711_TIMEOUT_RECOVERY_S
        self.__adaptive_timing_enabled = settings.HX711_ADAPTIVE_TIMING_ENABLED
        self.__adaptive_trigger_timeouts = max(1, settings.HX711_ADAPTIVE_TRIGGER_TIMEOUTS)
        self.__adaptive_read_timeout_s = max(self.__read_timeout_s, settings.HX711_ADAPTIVE_READ_TIMEOUT_S)
        self.__adaptive_read_interval_s = max(self.__read_interval_s, settings.HX711_ADAPTIVE_READ_INTERVAL_S)
        self.__adaptive_timeout_recovery_s = max(self.__timeout_recovery_s, settings.HX711_ADAPTIVE_TIMEOUT_RECOVERY_S)
        self.__adaptive_timing_applied = False
        self.__consecutive_timeouts = 0
        self.__last_timeout_log = 0.0

        # self.__loop = asyncio.get_event_loop()
        self.__measurement_callback = measurement_callback

    def simulator_thread(self):

        while not self.__stop_event.is_set():
            raw_value = self.sim_value + int(random.normalvariate(0, self.sim_noise))
            # print(f"jan {raw_value}")
            self.__loop.call_soon_threadsafe(self.__measurement_callback, raw_value)

            time.sleep(0.1)

    def reader_thread(self):
        self.__hx711 = HX711(
            dout_pin=self.__data_pin,
            pd_sck_pin=self.__clk_pin,
            gain=128,
        )

        try:
            while not self.__stop_event.is_set():
                try:
                    raw_value = self.__hx711.read_raw(timeout_seconds=self.__read_timeout_s)
                except HX711TimeoutError:
                    self.__consecutive_timeouts += 1
                    # Avoid flooding logs if a sensor is disconnected.
                    now = time.monotonic()
                    if now - self.__last_timeout_log >= 5:
                        print(f"SensorReader[{self.__name}]: HX711 timeout waiting for data")
                        self.__last_timeout_log = now
                    self.__maybe_apply_adaptive_timing("timeout")
                    if self.__hx711 is not None and hasattr(self.__hx711, "recover"):
                        self.__hx711.recover()
                    if self.__timeout_recovery_s > 0:
                        time.sleep(self.__timeout_recovery_s)
                    continue
                except Exception as exc:
                    print(f"SensorReader[{self.__name}]: HX711 read error: {exc}")
                    time.sleep(0.1)
                    continue

                self.__consecutive_timeouts = 0
                self.__maybe_apply_adaptive_timing("clock-high")
                self.__loop.call_soon_threadsafe(self.__measurement_callback, raw_value)
                if self.__read_interval_s > 0:
                    time.sleep(self.__read_interval_s)
        finally:
            if self.__hx711 is not None:
                self.__hx711.close()
                self.__hx711 = None

    def __maybe_apply_adaptive_timing(self, reason: str) -> None:
        if not self.__adaptive_timing_enabled or self.__adaptive_timing_applied:
            return

        if reason == "timeout":
            if self.__consecutive_timeouts < self.__adaptive_trigger_timeouts:
                return
            self.__apply_adaptive_timing(reason)
            return

        if reason == "clock-high" and self.__hx711 is not None and hasattr(self.__hx711, "consume_clock_high_warning_count"):
            warning_count = self.__hx711.consume_clock_high_warning_count()
            if warning_count > 0:
                self.__apply_adaptive_timing(f"clock high warning x{warning_count}")

    def __apply_adaptive_timing(self, reason: str) -> None:
        self.__read_timeout_s = self.__adaptive_read_timeout_s
        self.__read_interval_s = self.__adaptive_read_interval_s
        self.__timeout_recovery_s = self.__adaptive_timeout_recovery_s
        self.__adaptive_timing_applied = True
        print(
            f"SensorReader[{self.__name}]: applying adaptive HX711 timing due to {reason} "
            f"(timeout={self.__read_timeout_s}s interval={self.__read_interval_s}s recovery={self.__timeout_recovery_s}s)"
        )

    def start(self):
        """start reader thread, or simtrhead if data/clk are not specified"""

        if self.__thread is not None:
            raise Exception("Thread already started")

        self.__loop = asyncio.get_running_loop()

        self.__stop_event.clear()

        #NOTE: via seperate async run_in_executor will be slower/more overhead
        if self.__sim:
            self.__thread = threading.Thread(target=self.simulator_thread)
        else:
            self.__thread = threading.Thread(target=self.reader_thread)

        self.__thread.start()

    def stop(self):
        self.__stop_event.set()
        if self.__thread is not None:
            self.__thread.join()
        self.__thread = None
