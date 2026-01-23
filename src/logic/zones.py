import numpy as np
import cv2
import supervision as sv

class ZoneMonitor:
    def __init__(self, zones_config=None):
        """
        Manages multiple exclusion/counting zones.
        zones_config: dict or list of {name, polygon_points, max_count}
        """
        self.zones = []
        if zones_config:
            for z in zones_config:
                polygon = np.array(z['polygon'])
                self.zones.append({
                    'name': z['name'],
                    'polygon': polygon,
                    'zone': sv.PolygonZone(polygon=polygon), 
                    'max_count': z.get('max_count', 5)
                })

    def check_overcrowding(self, detections):
        """
        Check if any zone has too many people.
        """
        alarms = []
        # Filter for people
        people = detections[detections.class_id == 0]
        
        for z_item in self.zones:
            zone = z_item['zone']
            is_in_zone = zone.trigger(detections=people)
            count = is_in_zone.sum()
            
            if count > z_item['max_count']:
                alarms.append(f"Overcrowding in {z_item['name']}: {count} > {z_item['max_count']}")
                
        return alarms
