# analysis/detect_3line.py
import cv2
import numpy as np
from .roi import get_reaction_roi
from .focus import focus_score

def detect_reaction_3lines_from_image(img: np.ndarray):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    score = focus_score(gray)

    roi = get_reaction_roi(gray)
    blur = cv2.GaussianBlur(roi, (5, 5), 0)

    sobel = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
    projection = np.sum(np.abs(sobel), axis=1)

    peaks = projection > np.mean(projection) * 1.3
    line_count = int(np.sum(peaks)) // 12

    metrics = {
        "focus": score,
        "edge_strength": float(np.mean(projection))
    }

    return line_count, [], metrics