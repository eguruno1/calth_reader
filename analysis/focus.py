# analysis/focus.py
import cv2
import numpy as np

def focus_score(gray: np.ndarray) -> float:
    """
    Laplacian 기반 초점 점수
    """
    return cv2.Laplacian(gray, cv2.CV_64F).var()