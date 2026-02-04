import logging


class IndicatorController:
    """Controls red/green stack lights and buzzer via GPIO.

    - `green_pin`, `red_pin`, `buzzer_pin` are BCM pin numbers.
    - Green only when PPE compliant. Red + buzzer when non-compliant.
    """

    def __init__(self, green_pin: int, red_pin: int, buzzer_pin: int = None, gpio_module=None):
        self.green_pin = green_pin
        self.red_pin = red_pin
        self.buzzer_pin = buzzer_pin
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
            self.gpio.setup(self.green_pin, self.gpio.OUT, initial=self.gpio.LOW)
            self.gpio.setup(self.red_pin, self.gpio.OUT, initial=self.gpio.LOW)
            if self.buzzer_pin is not None:
                self.gpio.setup(self.buzzer_pin, self.gpio.OUT, initial=self.gpio.LOW)
            self.ready = True
            self.set_block()
        except Exception as e:
            logging.error("Indicator init failed: %s", e)
            self.ready = False

    def set_allow(self):
        # Green only
        if not self.ready:
            return
        try:
            self.gpio.output(self.green_pin, self.gpio.HIGH)
            self.gpio.output(self.red_pin, self.gpio.LOW)
            if self.buzzer_pin is not None:
                self.gpio.output(self.buzzer_pin, self.gpio.LOW)
        except Exception:
            pass

    def set_block(self, beep=True):
        # Red + buzzer
        if not self.ready:
            return
        try:
            self.gpio.output(self.green_pin, self.gpio.LOW)
            self.gpio.output(self.red_pin, self.gpio.HIGH)
            if self.buzzer_pin is not None and beep:
                self.gpio.output(self.buzzer_pin, self.gpio.HIGH)
        except Exception:
            pass

    def off(self):
        if not self.ready:
            return
        try:
            self.gpio.output(self.green_pin, self.gpio.LOW)
            self.gpio.output(self.red_pin, self.gpio.LOW)
            if self.buzzer_pin is not None:
                self.gpio.output(self.buzzer_pin, self.gpio.LOW)
        except Exception:
            pass

    def cleanup(self):
        try:
            if self.gpio is not None:
                self.off()
                self.gpio.cleanup()
        except Exception:
            pass
