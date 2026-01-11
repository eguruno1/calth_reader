# analysis/roi.py
import numpy as np

def get_reaction_roi(image: np.ndarray):
    """ROI 계산 로직"""
    h, w = image.shape[:2]

    x1 = int(w * 0.25)
    x2 = int(w * 0.75)
    y1 = int(h * 0.35)
    y2 = int(h * 0.75)

    return image[y1:y2, x1:x2]