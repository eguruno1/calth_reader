# analysis/detect_2line.py
import cv2
import numpy as np
from .focus import focus_score


def detect_reaction_lines_from_image(img: np.ndarray):
    """
    2라인(C/T) 반응라인 검출 – 실제 검출 라인 수 기반 안정판
    """

    h, w = img.shape[:2]

    # ===============================
    # 1️⃣ Wide ROI + Y축 자동 보정
    # ===============================
    wide_y1 = int(h * 0.28)
    wide_y2 = int(h * 0.65)
    wide_roi = img[wide_y1:wide_y2, :]

    gray = cv2.cvtColor(wide_roi, cv2.COLOR_BGR2GRAY)
    proj_y = np.mean(255 - gray, axis=1)

    thresh_y = np.mean(proj_y) + np.std(proj_y) * 0.6
    ys = np.where(proj_y > thresh_y)[0]

    if len(ys) < 10:
        return 0, [], {}

    center_y = int(np.mean(ys)) + wide_y1

    roi_h = int(h * 0.18)
    roi_y1 = max(0, center_y - roi_h // 2)
    roi_y2 = min(h, center_y + roi_h // 2)
    roi = img[roi_y1:roi_y2, :]

    # ===============================
    # 2️⃣ R-G 강조
    # ===============================
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 12, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 11))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # ===============================
    # 3️⃣ X축 투영
    # ===============================
    proj_x = np.sum(binary, axis=0).astype(np.float32)
    proj_x = cv2.GaussianBlur(proj_x, (31, 1), 0)

    thresh_x = np.mean(proj_x) + np.std(proj_x) * 0.5
    mask = proj_x > thresh_x

    segments = []
    start = None
    for x in range(len(mask)):
        if mask[x] and start is None:
            start = x
        elif not mask[x] and start is not None:
            if x - start > 6:
                segments.append((start, x))
            start = None
    if start is not None and len(mask) - start > 6:
        segments.append((start, len(mask)))

    if not segments:
        return 0, [], {}

    # ===============================
    # 4️⃣ 실제 검출 라인 정보
    # ===============================
    lines = []
    for x1, x2 in segments:
        cx = (x1 + x2) // 2
        intensity = float(np.max(proj_x[x1:x2]))
        lines.append({
            "cx": cx,
            "x1": x1,
            "x2": x2,
            "intensity": intensity
        })

    # 좌 → 우
    lines.sort(key=lambda x: x["cx"])

    max_int = max(l["intensity"] for l in lines)

    boxes = []
    metrics = []

    # ⚠️ 핵심: 실제 검출된 라인 수만큼만 처리
    for idx, l in enumerate(lines[:2]):
        label = "C" if idx == 0 else "T"

        cx = l["cx"]
        x1 = l["x1"]
        x2 = l["x2"]
        intensity = l["intensity"]

        box_w = max(x2 - x1, int(w * 0.015))
        box_x = max(0, min(w - box_w, cx - box_w // 2))

        boxes.append((box_x, roi_y1, box_w, roi_y2 - roi_y1))
        metrics.append({
            "label": label,
            "center_x": cx,
            "intensity": round(intensity, 2),
            "confidence": round(intensity / (max_int + 1e-6), 3)
        })

    return len(metrics), boxes, {
        "focus": focus_score(img),
        "projection_mean": float(np.mean(proj_x)),
        "lines": metrics
    }

