# Hardware smoke tests (Orange Pi Zero 3)

Run these scripts on the target board after enabling required overlays and wiring.

1. `python hardware_smoke/blink_led.py`
2. `python hardware_smoke/read_hx711_once.py`
3. `python hardware_smoke/read_hx711_burst.py`
4. `python hardware_smoke/pwm_servo_test.py` (servo disconnected for waveform checks)

All scripts require `MEOWTON_HARDWARE=orangepi-zero3`.

For faster HX711 burst debugging:
- `MEOWTON_BURST_SAMPLES=200` to reduce run time
- `MEOWTON_BURST_PROGRESS_EVERY=20` for periodic progress output
