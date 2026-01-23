import numpy as np

def calculate_iou(box1, box2):
    """
    Calculate IoU between two boxes [x1, y1, x2, y2].
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union_area = box1_area + box2_area - intersection_area
    if union_area == 0:
        return 0
    return intersection_area / union_area

def box_contains_box(outer_box, inner_box, threshold=0.8):
    """
    Check if inner_box is mostly inside outer_box.
    threshold: Fraction of inner_box area that must be inside outer_box.
    """
    x1 = max(outer_box[0], inner_box[0])
    y1 = max(outer_box[1], inner_box[1])
    x2 = min(outer_box[2], inner_box[2])
    y2 = min(outer_box[3], inner_box[3])
    
    intersection_area = max(0, x2 - x1) * max(0, y2 - y1)
    
    inner_area = (inner_box[2] - inner_box[0]) * (inner_box[3] - inner_box[1])
    
    if inner_area == 0:
        return False
        
    return (intersection_area / inner_area) >= threshold
