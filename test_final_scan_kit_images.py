import cv2
import numpy as np
from pyzbar import pyzbar
import os
import json
from datetime import datetime

IMAGE_DIR = "./images"
TARGET_IMAGES = [
    "kit_bench_2line_ok.jpeg",
    "kit_bench_2line_ok_2.jpeg"
]

def detect_qr(image):
    qr_results = pyzbar.decode(image)
    if not qr_results:
        return None, None
    qr = qr_results[0]
    return qr.data.decode("utf-8"), qr.rect


def detect_reaction_lines(image, qr_rect=None):
    h, w = image.shape[:2]

    # 🔹 ROI 자동 설정 (QR 기준)
    if qr_rect:
        x, y, qw, qh = qr_rect
        roi_x1 = int(x - qw * 0.5)
        roi_x2 = int(x + qw * 1.5)
        roi_y1 = int(y + qh * 1.5)
        roi_y2 = int(y + qh * 4.5)
    else:
        # fallback (중앙)
        roi_x1 = int(w * 0.4)
        roi_x2 = int(w * 0.6)
        roi_y1 = int(h * 0.3)
        roi_y2 = int(h * 0.7)

    roi_x1 = max(0, roi_x1)
    roi_y1 = max(0, roi_y1)
    roi_x2 = min(w, roi_x2)
    roi_y2 = min(h, roi_y2)

    roi = image[roi_y1:roi_y2, roi_x1:roi_x2]

    # 🔹 전처리
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    th = cv2.adaptiveThreshold(
        blur,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )

    # 🔹 수평 Projection
    proj = np.sum(th, axis=1)
    proj = proj / np.max(proj)

    # 🔹 피크 검출
    indices = np.where(proj > 0.3)[0]

    lines = []
    if len(indices) > 0:
        current = [indices[0]]
        for idx in indices[1:]:
            if idx - current[-1] <= 3:
                current.append(idx)
            else:
                lines.append(current)
                current = [idx]
        lines.append(current)

    return len(lines)


def main():
    results = []
    ts = datetime.now().isoformat()

    for filename in TARGET_IMAGES:
        img_path = os.path.join(IMAGE_DIR, filename)

        if not os.path.exists(img_path):
            print(f"[WARN] Image not found: {img_path}")
            continue

        image = cv2.imread(img_path)
        if image is None:
            print(f"[ERROR] Failed to load: {img_path}")
            continue

        qr_text, qr_rect = detect_qr(image)
        line_count = detect_reaction_lines(image, qr_rect)

        result = {
            "timestamp": ts,
            "image": img_path,
            "qr_detected": qr_text is not None,
            "qr_text": qr_text,
            "reaction_line_count": line_count
        }

        results.append(result)

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
