from typing import Dict, Set, Tuple


class ZoneRules:
    """Defines PPE requirements per zone.

    Example:
        rules = {"default": {"helmet","vest"}}
    """

    def __init__(self, rules: Dict[str, Set[str]] = None):
        # default zone requires helmet + vest
        self.rules = rules or {"default": {"helmet", "vest"}}

    def required_for(self, zone_id: str):
        return self.rules.get(zone_id, self.rules.get("default", set()))

    def check(self, detections, zone_id: str) -> Tuple[bool, Set[str]]:
        """Check detections for required PPE in zone.

        returns (is_compliant, missing_ppe_set)
        """
        required = set(self.required_for(zone_id))
        present = set()
        for d in detections:
            label = d.get("label")
            if label in required:
                present.add(label)
        missing = required - present
        return (len(missing) == 0, missing)
