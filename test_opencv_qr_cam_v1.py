"""
test_opencv_qr_cam_v1의 Docstring

Ubuntu 사전 설치 (필수)
sudo apt update
sudo apt install -y libzbar0 libzbar-dev
pip install opencv-python pyzbar numpy

Camera Frame
   ↓
QR 탐지
   ├─ QR 있음 → 회전 보정
   ├─ QR 영역 마스킹
   ↓
결과창 ROI 추출
   ↓
라인 검출 (C/T)
   ↓
결과 Overlay + 출력

"""

import cv2
import numpy as np
import os
import json
from datetime import datetime
from pyzbar.pyzbar import decode

# ============================================================
# SAVE PATH
# ============================================================
SAVE_DIR = "./CalthReaderResult/images"
os.makedirs(SAVE_DIR, exist_ok=True)

# ============================================================
# QR DETECTION (FAST)
# ============================================================

def detect_qr_fast(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, None, fx=0.4, fy=0.4)

    qrs = decode(small)
    if not qrs:
        return None, None

    qr = qrs[0]
    text = qr.data.decode("utf-8").strip()
    pts = np.array([(p.x / 0.4, p.y / 0.4) for p in qr.polygon])
    return text, pts

# ============================================================
# IMAGE UTILS
# ============================================================

def mask_qr(img, pts):
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255)
    img[mask == 255] = 0
    return img

def extract_result_window(img):
    h, w = img.shape[:2]
    return img[int(h * 0.30):int(h * 0.70),
               int(w * 0.35):int(w * 0.65)]

# ============================================================
# LINE DETECTION
# ============================================================

def detect_lines(roi):
    gray16 = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # RG10 → 8bit 변환 (필수)
    gray8 = (gray16 >> 2).astype(np.uint8)

    edges = cv2.Canny(gray8, 40, 120)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 25))
    vertical = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(
        vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    h, w = roi.shape[:2]
    xs = []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        if ch > h * 0.3 and cw < w * 0.2:
            xs.append(x)

    xs = sorted(xs)
    filtered = []
    for x in xs:
        if not filtered or abs(x - filtered[-1]) > 12:
            filtered.append(x)

    return min(len(filtered), 2)


# ============================================================
# SAVE RESULT (ONCE)
# ============================================================

def save_result_once(img, qr_text, line_cnt):
    ts = datetime.now()
    ts_str = ts.strftime("%Y%m%d_%H%M%S_%f")

    if line_cnt == 2:
        status = "C_OK_T_OK"
    elif line_cnt == 1:
        status = "C_OK_T_NO"
    else:
        status = "C_NO_T_NO"

    img_name = f"{status}_{ts_str}.jpg"
    json_name = f"{status}_{ts_str}.json"

    cv2.imwrite(os.path.join(SAVE_DIR, img_name), img)

    data = {
        "timestamp": ts.isoformat(),
        "qr_detected": qr_text is not None,
        "qr_text": qr_text,
        "line_count": line_cnt,
        "result": {
            "C": "OK" if line_cnt >= 1 else "NO",
            "T": "OK" if line_cnt == 2 else "NO"
        },
        "image_file": img_name
    }

    with open(os.path.join(SAVE_DIR, json_name), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("✅ Saved:", img_name)

# ============================================================
# CAMERA LOOP (V4L2 RAW RG10)
# ============================================================

def run_camera():
    cap = cv2.VideoCapture("/dev/video0", cv2.CAP_V4L2)
    if not cap.isOpened():
        print("❌ Camera open failed (V4L2)")
        return

    # 해상도 명시 (v4l2-ctl 기준)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    qr_text = None
    qr_pts = None
    frame_count = 0

    MAX_FRAMES = 150  # 약 5초 (30fps 기준)

    while True:
        ret, raw = cap.read()
        if not ret or raw is None:
            continue

        # RAW RG10 → uint16
        if raw.ndim == 3:
            raw = cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)
        raw16 = raw.astype(np.uint16)

        # Bayer → RGB
        rgb = cv2.cvtColor(raw16, cv2.COLOR_BAYER_RG2BGR)

        if qr_text is None and frame_count % 10 == 0:
            qr_text, qr_pts = detect_qr_fast(rgb)
            if qr_text:
                print("✅ QR detected")

        proc = rgb
        if qr_pts is not None:
            proc = mask_qr(proc, qr_pts)

        roi = extract_result_window(proc)
        line_cnt = detect_lines(roi)

        # ✅ 종료 조건 1: QR 또는 라인
        if qr_text is not None or line_cnt >= 1:
            print("🎯 Detection condition met")
            save_result_once(rgb, qr_text, line_cnt)
            break

        # ✅ 종료 조건 2: 타임아웃
        if frame_count > MAX_FRAMES:
            print("⏱ Timeout – force save & exit")
            save_result_once(rgb, qr_text, line_cnt)
            break

        frame_count += 1

    cap.release()
    print("🎯 Program finished")

# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_camera()
