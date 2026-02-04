import logging
import time

class RelayController:
    """GPIO relay controller. GPIO HIGH => machine enabled.

    This module will try to import Jetson.GPIO or RPi.GPIO. If neither is
    available, initialization fails and the controller remains in BLOCK mode.
    """

    def __init__(self, enable_pin: int, gpio_module=None, active_high=True):
        self.enable_pin = enable_pin
        self.active_high = active_high
        self.gpio = None
        self.ready = False
        try:
            if gpio_module is not None:
                self.gpio = gpio_module
            else:
                try:
                    import Jetson.GPIO as GPIO

                    self.gpio = GPIO
                except Exception:
                    import RPi.GPIO as GPIO

                    self.gpio = GPIO
            self.gpio.setmode(self.gpio.BCM)
            self.gpio.setup(self.enable_pin, self.gpio.OUT, initial=self.gpio.LOW)
            # Default state: BLOCK -> ensure machine disabled
            self.disable()
            self.ready = True
        except Exception as e:
            logging.error("RelayController init failed: %s", e)
            self.ready = False

    def enable(self):
        try:
            if not self.ready:
                raise RuntimeError("RelayController not ready")
            # GPIO HIGH -> enable
            self.gpio.output(self.enable_pin, self.gpio.HIGH if self.active_high else self.gpio.LOW)
        except Exception:
            # fail-safe: disable on error
            self.disable()
            raise

    def disable(self):
        try:
            if not self.ready:
                return
            # GPIO LOW -> disable
            self.gpio.output(self.enable_pin, self.gpio.LOW if self.active_high else self.gpio.HIGH)
        except Exception:
            pass

    def cleanup(self):
        try:
            if self.gpio is not None:
                self.disable()
                self.gpio.cleanup()
        except Exception:
            pass
