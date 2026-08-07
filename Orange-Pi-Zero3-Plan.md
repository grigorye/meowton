The port should replace Raspberry Pi–specific GPIO calls with a small Orange Pi hardware abstraction, while preserving simulation mode and the rest of Meowton.

## Target architecture

Create three focused hardware drivers:

```
hardware/
├── gpio.py       # wiringOP digital input/output
├── hx711.py      # local HX711 protocol implementation
└── pwm.py        # Linux hardware PWM through /sys/class/pwm
```

Application code should not import `RPi.GPIO`, `wiringpi`, or manipulate sysfs directly.

## Pin mapping

Assuming the wiring stays on the same physical header pins:

| Function         | Existing RPi BCM | Physical | Zero 3 wPi |
| ---------------- | ---------------- | -------- | ---------- |
| Status LED       | 4                | 7        | 2          |
| Food HX711 data  | 23               | 16       | 9          |
| Food HX711 clock | 24               | 18       | 10         |
| Cat HX711 data   | 27               | 13       | 7          |
| Cat HX711 clock  | 17               | 11       | 5          |

The servo is different:

-   Existing servo: physical pin 12, which is not hardware PWM on Zero 3.
-   Rewire servo signal to physical pin 10, `PWM1`, wPi 4.
-   Alternatively use physical pin 8, `PWM2`, wPi 3.
-   Both conflict with UART5.

## Implementation plan

### 1. Centralize hardware configuration

Move pins and platform selection into `settings.py`, ideally supporting environment variables:

```
hardware_backend = os.getenv("MEOWTON_HARDWARE", "orangepi-zero3")

LED_PIN = 2
FOOD_DATA_PIN = 9
FOOD_CLOCK_PIN = 10
CAT_DATA_PIN = 7
CAT_CLOCK_PIN = 5

SERVO_PWM_CHIP = 0
SERVO_PWM_CHANNEL = 1
```

Keep `dev_mode`, but make simulation an explicit backend rather than scattered conditionals.

Suggested values:

```
MEOWTON_HARDWARE=orangepi-zero3
MEOWTON_HARDWARE=simulated
```

### 2. Add a digital GPIO wrapper

Implement the required subset with `wiringOP-Python`:

```
class DigitalInput:
    def read(self) -> bool: ...

class DigitalOutput:
    def write(self, value: bool) -> None: ...
    def close(self) -> None: ...
```

Call `wiringpi.wiringPiSetup()` once per process, not once per device.

Use wPi numbering consistently. Do not pass the old BCM values to wiringOP.

### 3. Replace the HX711 package

Remove the PyPI `hx711` dependency and add a local implementation using the wrapper.

Required behavior:

-   Configure DOUT as input and SCK as output.
-   Keep SCK low while idle.
-   Wait for DOUT to become low, with a timeout.
-   Clock exactly 24 data bits.
-   Apply the additional gain-selection pulse:
    -   1 pulse: channel A, gain 128
    -   2 pulses: channel B, gain 32
    -   3 pulses: channel A, gain 64
-   Sign-extend the 24-bit two’s-complement result.
-   Ensure SCK is not held high for 60 µs or longer, because that powers down the HX711.
-   Serialize access to each device.
-   Provide `read_raw()` or preserve the current `_read()` behavior temporarily.

Update `sensor_reader.py` to use this driver. Add timeouts and error logging so a disconnected HX711 does not block its thread forever.

### 4. Replace servo software PWM

Replace `GPIO.PWM` in `feeder.py` with a kernel-PWM class operating on:

```
/sys/class/pwm/pwmchip0/pwm1
```

For 50 Hz:

```
period = 20,000,000 ns
5% duty = 1,000,000 ns
6% duty = 1,200,000 ns
8% duty = 1,600,000 ns
```

Translate the existing percentage values with:

```
duty_ns = round(period_ns * duty_percent / 100)
```

The PWM driver should:

-   Export the channel if necessary.
-   Set period before duty cycle.
-   Enable it when needed.
-   Set duty cycle to zero after movement.
-   Disable and close safely during shutdown.
-   Handle an already-exported channel without failing.

Enable `ph-pwm12` and disable `ph-uart5` using `orangepi-config`, then reboot.

### 5. Port the status LED

Update `status_led.py` to use `DigitalOutput`.

Also fix its current simulation bug: `RPi.GPIO` is imported at module load even in development mode. Simulation must never import hardware libraries.

### 6. Make lifecycle cleanup reliable

Update `Meowton.stop()` so it closes:

-   Both HX711 devices
-   Status LED
-   Servo PWM channel
-   GPIO resources

Ensure cleanup still runs when an asyncio task fails or the container receives SIGTERM.

### 7. Update dependencies and container build

Remove:

```
RPi.GPIO
hx711
```

Add/build the official [`wiringOP-Python` `next` branch](https://github.com/orangepi-xunlong/wiringOP-Python).

Because Meowton runs in Podman, the module must exist inside the image—not only on the host. The build will likely need:

```
git
swig
python3-dev
python3-setuptools
build-essential
```

The current container is privileged, which should expose GPIO and PWM, but verify:

```
podman exec meowton sh -c \
  'ls -l /dev/gpiochip*; ls -l /sys/class/pwm'
```

A later hardening pass can replace `--privileged` with explicit devices and permissions.

### 8. Test in layers

Test hardware separately before starting NiceGUI:

1.  Blink the LED.
2.  Read one raw value from each HX711.
3.  Collect 1,000 HX711 readings and check for timeouts/corruption.
4.  Generate 50 Hz PWM with the servo disconnected.
5.  Verify waveform with an oscilloscope or logic analyzer if available.
6.  Connect the servo with an independent adequate power supply and common ground.
7.  Run simulated Meowton.
8.  Run real hardware without feeding.
9.  Perform a controlled feeding test.
10.  Reboot and confirm systemd startup.

## Important caveats and unknowns

-   The physical-to-wPi mapping should be confirmed on the actual board with `gpio readall`.
-   wiringOP behavior can differ between the official Orange Pi image and Armbian. The kernel and OS image matter.
-   `pwmchip0/pwm1` naming must be confirmed after enabling the overlay; kernel versions may expose a different chip/channel layout.
-   The official documentation says PWM is supported, but wiringOP’s ordinary digital API is not the same as kernel hardware PWM.
-   HX711 bit-banging is timing-sensitive. wiringOP’s compiled calls should be fast enough, but this needs measurement under application load.
-   Python 3.14 may expose compatibility problems in older wiringOP Python bindings. Pin the container’s Python version if necessary.
-   Container access to memory-mapped wiringOP hardware may behave differently from host execution, even under `--privileged`. Test a minimal wiringOP program inside the container early.
-   The servo must be moved from physical pin 12 to a PWM-capable pin.
-   Enabling PWM1/PWM2 consumes the UART5 pins.
-   Do not power the servo from a GPIO output. Use a suitable 5 V supply and connect its ground to the Orange Pi ground.
-   Existing scale calibration should remain valid electrically, but sign/order changes in the replacement HX711 reader may require recalibration.

## On-device verification commands

Run these steps on the Orange Pi Zero 3 after wiring changes (servo moved to PWM-capable pin) and after enabling PWM via `orangepi-config`.

1. Confirm pin mapping and PWM visibility:

```sh
gpio readall
ls -l /sys/class/pwm
ls -l /sys/class/pwm/pwmchip0
```

2. Confirm container can see required devices (if running in Podman):

```sh
podman exec meowton sh -c 'ls -l /dev/gpiochip*; ls -l /sys/class/pwm'
```

3. Run LED smoke test:

```sh
cd /app/src
MEOWTON_HARDWARE=orangepi-zero3 python hardware_smoke/blink_led.py
```

4. Run single-read HX711 smoke test:

```sh
cd /app/src
MEOWTON_HARDWARE=orangepi-zero3 python hardware_smoke/read_hx711_once.py
```

5. Run burst HX711 test (1000 reads with timeout counters):

```sh
cd /app/src
MEOWTON_HARDWARE=orangepi-zero3 python hardware_smoke/read_hx711_burst.py
```

6. Run PWM waveform smoke test with servo disconnected first:

```sh
cd /app/src
MEOWTON_HARDWARE=orangepi-zero3 python hardware_smoke/pwm_servo_test.py
```

7. Validate waveform using a scope/logic analyzer at the servo signal pin:
- Frequency: 50 Hz
- Period: 20 ms
- Duty pulses: 1.0 ms (5%), 1.2 ms (6%), 1.6 ms (8%)

8. Connect servo with external 5V supply and common ground, then repeat PWM test.

9. Start Meowton in simulated mode (functional sanity):

```sh
cd /app/src
MEOWTON_HARDWARE=simulated python main.py dev
```

10. Start Meowton in Orange Pi mode, observe startup and runtime logs for HX711 timeouts/errors:

```sh
cd /app/src
MEOWTON_HARDWARE=orangepi-zero3 python main.py
```

11. Perform controlled feeding test and validate shutdown cleanup:
- Trigger feed cycle.
- Stop process via SIGTERM.
- Confirm PWM disabled and LED off after stop.

## systemd startup verification checklist

Use this checklist after creating/updating the service unit, and after a reboot.

1. Validate service definition and enablement:

```sh
sudo systemctl daemon-reload
sudo systemctl enable meowton
systemctl is-enabled meowton
systemctl cat meowton
```

2. Start and inspect runtime status:

```sh
sudo systemctl start meowton
systemctl status meowton --no-pager
```

3. Inspect current-boot logs:

```sh
journalctl -u meowton -b --no-pager
```

4. Reboot and verify auto-start:

```sh
sudo reboot
# after reconnecting
systemctl status meowton --no-pager
journalctl -u meowton -b --no-pager
```

5. Verify graceful SIGTERM cleanup path:

```sh
sudo systemctl stop meowton
journalctl -u meowton -b --no-pager | tail -n 100
```

Expected log patterns during healthy startup/runtime:
- `Feeder: Waitting for request`
- `Feeder: Got feed request` only when feed is triggered
- `SensorReader[food]: HX711 timeout waiting for data` only when the sensor is disconnected/unready
- `SensorReader[cat]: HX711 timeout waiting for data` only when the sensor is disconnected/unready

Expected log patterns during controlled shutdown:
- `Received signal ... stopping Meowton` (when process receives SIGTERM/SIGINT)
- Service exits without repeated traceback loops

Investigate immediately if observed:
- `Meowton: task failed:`
- Continuous HX711 timeout logs while sensors should be connected and idle-ready
- Service restart loops in `systemctl status`