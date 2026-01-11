# analysis/detect_3line.py
import cv2
import numpy as np
from .focus import focus_score


def detect_reaction_3lines_from_image(img: np.ndarray):
    """
    3라인(L1/L2/L3) 반응라인 검출 – test_3line_auto 최종판 이식
    """

    h, w = img.shape[:2]

    roi_y1 = int(h * 0.35)
    roi_y2 = int(h * 0.58)
    roi = img[roi_y1:roi_y2, :]

    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 12, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    col_sum = np.sum(binary, axis=0).astype(np.float32)
    col_sum = cv2.GaussianBlur(col_sum, (31, 1), 0)

    thresh = np.mean(col_sum) + np.std(col_sum) * 0.5
    active = col_sum > thresh

    segments = []
    start = None
    for x in range(len(active)):
        if active[x] and start is None:
            start = x
        elif not active[x] and start is not None:
            if x - start > 6:
                segments.append((start, x))
            start = None
    if start is not None:
        segments.append((start, len(active)))

    if not segments:
        return 0, [], {}

    lines = []
    for x1, x2 in segments:
        cx = (x1 + x2) // 2
        intensity = float(np.max(col_sum[x1:x2]))
        lines.append((cx, x1, x2, intensity))

    expected = [int(w * 0.30), int(w * 0.50), int(w * 0.70)]
    matched = []

    for idx, exp_x in enumerate(expected):
        best = min(lines, key=lambda l: abs(l[0] - exp_x))
        matched.append((f"L{idx+1}", *best))

    max_int = max(l[4] for l in matched)

    boxes = []
    metrics = []

    roi_center_y = (roi_y1 + roi_y2) // 2
    line_h = int((roi_y2 - roi_y1) * 0.55)

    for label, cx, x1, x2, intensity in matched:
        box_w = max(x2 - x1, int(w * 0.015))
        box_x = max(0, min(w - box_w, cx - box_w // 2))
        box_y = max(0, roi_center_y - line_h // 2)

        boxes.append((box_x, box_y, box_w, line_h))
        metrics.append({
            "label": label,
            "center_x": cx,
            "intensity": round(intensity, 2),
            "confidence": round(intensity / (max_int + 1e-6), 3)
        })

    return len(boxes), boxes, {
        "focus": focus_score(img),
        "edge_strength": float(np.mean(col_sum)),
        "lines": metrics
    }
