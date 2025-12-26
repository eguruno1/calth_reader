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
import json
from pyzbar.pyzbar import decode


# ============================================================
# QR DETECTION
# ============================================================

def detect_qr(img):
    """
    QR 코드 탐지 및 텍스트 추출
    """
    qrs = decode(img)
    if not qrs:
        return None, None

    qr = qrs[0]
    text = qr.data.decode("utf-8").strip()
    pts = np.array([(p.x, p.y) for p in qr.polygon])

    if len(pts) < 4:
        return text, None

    return text, pts


def rotate_by_qr(img, pts):
    """
    QR 위치 기준 회전 보정
    """
    rect = cv2.minAreaRect(pts)
    angle = rect[-1]

    if angle < -45:
        angle += 90

    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h))


def mask_qr(img, pts):
    """
    QR 영역 마스킹 (라인 간섭 제거)
    """
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255)
    img[mask == 255] = (0, 0, 0)
    return img


# ============================================================
# RESULT ROI
# ============================================================

def extract_result_window(img):
    """
    결과창 ROI (비율 기반)
    """
    h, w = img.shape[:2]
    return img[int(h*0.30):int(h*0.70),
               int(w*0.35):int(w*0.65)]


# ============================================================
# LINE DETECTION
# ============================================================

def find_vertical_candidates(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(2.5, (8,8))
    enhanced = clahe.apply(gray)

    edges = cv2.Canny(enhanced, 40, 120)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 25))
    vertical = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = roi.shape[:2]
    boxes = []

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        if ch > h * 0.25 and cw < w * 0.20:
            boxes.append((x, y, cw, ch))

    return boxes


def verify_real_line(roi, bbox):
    x, y, w, h = bbox
    cut = roi[y:y+h, x:x+w]

    score = 0
    if w >= 2:
        score += 1
    if np.std(cv2.cvtColor(cut, cv2.COLOR_BGR2GRAY)) > 5:
        score += 1

    hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)
    if np.mean(hsv[...,1]) > 20:
        score += 1

    return score >= 2


def detect_lines(roi):
    candidates = find_vertical_candidates(roi)
    valid = []

    for b in candidates:
        if verify_real_line(roi, b):
            valid.append(b)

    valid.sort(key=lambda x: x[0])
    lines = []

    for b in valid:
        if not lines or abs(b[0] - lines[-1][0]) > 12:
            lines.append(b)

    return min(len(lines), 2)


# ============================================================
# REALTIME CAMERA LOOP
# ============================================================

def run_camera(camera_src=0):
    """
    camera_src:
      - 0           → 기본 웹캠
      - /dev/video0 → USB 카메라
      - rtsp://...  → RTSP 스트림
    """

    cap = cv2.VideoCapture(camera_src)

    fixed_rotation = False
    cached_angle_pts = None
    qr_text_cached = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()

        # QR 탐지는 초기에만
        if not fixed_rotation:
            qr_text, pts = detect_qr(frame)
            if pts is not None:
                frame = rotate_by_qr(frame, pts)
                cached_angle_pts = pts
                qr_text_cached = qr_text
                fixed_rotation = True

        # QR 마스킹 (고정)
        if fixed_rotation and cached_angle_pts is not None:
            frame = mask_qr(frame, cached_angle_pts)

        roi = extract_result_window(frame)
        line_cnt = detect_lines(roi)

        if line_cnt == 2:
            status = "C:OK  T:OK"
        elif line_cnt == 1:
            status = "C:OK  T:NO"
        else:
            status = "C:NO  T:NO"

        # Overlay
        cv2.putText(display, status, (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,0), 2)

        if qr_text_cached:
            cv2.putText(display, "QR:", (30, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
            y = 110
            for line in qr_text_cached.splitlines():
                cv2.putText(display, line, (30, y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)
                y += 30

        cv2.imshow("TestKit Realtime", display)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()


# ============================================================
# ENTRY
# ============================================================

if __name__ == "__main__":
    run_camera(0)   # 0: webcam
