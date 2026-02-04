import logging
from enum import Enum


class Action(Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


class Gatekeeper:
    """Decision engine enforcing exact logic:

    IF required_PPE_detected == TRUE:
        enable_machine()
        set_indicator(GREEN)
    ELSE:
        disable_machine()
        set_indicator(RED)

    There is no alternative path.
    """

    def __init__(self, controller, indicator, logger):
        """controller: RelayController or PLCController-like object with enable()/disable()
        indicator: IndicatorController-like object with set_allow()/set_block()
        logger: callable log_event(zone_id, missing_ppe, action)
        """
        self.controller = controller
        self.indicator = indicator
        self.logger = logger

    def enforce(self, zone_id: str, is_compliant: bool, missing_ppe: set):
        # Strict single-path logic
        if is_compliant:
            try:
                self.controller.enable()
            except Exception:
                # device error -> fail safe block
                try:
                    self.controller.disable()
                except Exception:
                    pass
                self.indicator.set_block()
                self.logger(zone_id, list(missing_ppe), Action.BLOCK.value)
                return Action.BLOCK
            # success
            self.indicator.set_allow()
            self.logger(zone_id, [], Action.ALLOW.value)
            return Action.ALLOW
        else:
            try:
                self.controller.disable()
            except Exception:
                pass
            self.indicator.set_block()
            self.logger(zone_id, list(missing_ppe), Action.BLOCK.value)
            return Action.BLOCK
