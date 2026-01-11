# analysis/detect_2line.py
import cv2
import numpy as np
from .roi import get_reaction_roi
from .focus import focus_score

def detect_reaction_lines_from_image(img: np.ndarray):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    score = focus_score(gray)

    roi = get_reaction_roi(gray)
    _, th = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    projection = np.sum(255 - th, axis=1)
    peaks = projection > np.mean(projection) * 1.5

    line_count = int(np.sum(peaks)) // 15

    metrics = {
        "focus": score,
        "projection_mean": float(np.mean(projection))
    }

    return line_count, [], metrics