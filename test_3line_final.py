"""
test_3line의 Docstring

[동작 순서]
0. 2라인 / 3라인 선택 판독
1. LED ON (UART) 
2. 카메라 오픈 (Jetson ISP 경유)
3. 노출/게인 안정화 대기
4. 포커스 안정화
5. 프레임 1장 캡처
6. 이미지 저장
7. 저장된 이미지 다시 로드(QR/Line 인식을 위해)
8. 모든 결과 JSON 파일로 저장
9. LED OFF & 자원 해제


프로그램 실행
 └─ 2 또는 3 입력
     ├─ 촬영
     ├─ 2 → 기존 2라인 로직
     └─ 3 → 신규 3라인 로직
         ↓
   박스 표시
   결과 텍스트 표시
   이미지 저장
   썸네일 생성
   JSON 저장
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import cv2
import json
import time
import serial
import numpy as np
import os
from datetime import datetime

# =========================================================
# 기본 설정
# =========================================================
CAM_WIDTH      = 1280
CAM_HEIGHT     = 720
FPS            = 30

LED_PORT       = "/dev/ttyTHS1"
LED_BAUD       = 115200
LED_ON_CMD     = b"L45"
LED_OFF_CMD    = b"L00"

IMG_SAVE_DIR   = "./CalthReaderResult/images"
JSON_SAVE_DIR  = "./CalthReaderResult/json"
THUMB_SAVE_DIR = "./CalthReaderResult/thumbnails"

# =========================================================
# LED 제어
# =========================================================
def led_on():
    ser = serial.Serial(LED_PORT, LED_BAUD, timeout=1)
    ser.write(LED_ON_CMD)
    ser.close()
    print("💡 LED ON")

def led_off():
    ser = serial.Serial(LED_PORT, LED_BAUD, timeout=1)
    ser.write(LED_OFF_CMD)
    ser.close()
    print("💡 LED OFF")

# =========================================================
# 카메라 오픈 (ISP 파이프라인)
# =========================================================
def open_camera():
    pipeline = (
        "nvarguscamerasrc ! "
        f"video/x-raw(memory:NVMM),width={CAM_WIDTH},height={CAM_HEIGHT},framerate={FPS}/1 ! "
        "nvvidconv ! video/x-raw,format=BGRx ! "
        "videoconvert ! video/x-raw,format=BGR ! appsink"
    )

    cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        raise RuntimeError("❌ Camera open failed")

    return cap

# =========================================================
# 실행 시 모드 선택 (2라인 / 3라인)
# =========================================================
def get_detection_mode():
    while True:
        mode = input("반응라인 검출 모드 선택 (2 또는 3 입력): ").strip()
        if mode in ("2", "3"):
            return int(mode)
        print("❌ 잘못된 입력입니다. 2 또는 3을 입력하세요.")

# =========================================================
# [기존] 2라인 전용 반응라인 검출 (구조 유지 + 위치 보정)
# =========================================================
def detect_reaction_lines_from_image(img):
    """
    2라인 전용 (C / T)
    - 카메라 위치 변화 자동 보정
    - 라인 중심 기준 ROI 이동
    - 반환: (라인 수, 박스 리스트)
    """

    h, w = img.shape[:2]

    # ======================================================
    # STEP 0. 전체 이미지 기준 반응라인 X 중심 추정 (⭐ 핵심)
    # ======================================================
    gray_full = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(2.0, (8, 8))
    gray_full = clahe.apply(gray_full)

    proj_full = np.mean(255 - gray_full, axis=0)
    proj_full = cv2.GaussianBlur(
        proj_full.astype(np.float32), (51, 1), 0
    )

    x_center_est = int(np.argmax(proj_full))

    # ======================================================
    # ROI 자동 이동 (중심 기준)
    # ======================================================
    roi_width = int(w * 0.50)

    roi_x1 = max(0, x_center_est - roi_width // 2)
    roi_x2 = min(w, roi_x1 + roi_width)

    roi_y1 = int(h * 0.30)
    roi_y2 = int(h * 0.62)

    roi = img[roi_y1:roi_y2, roi_x1:roi_x2].copy()

    # -------------------------------
    # R-G 강조 (기존 유지)
    # -------------------------------
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # -------------------------------
    # contour 기반 라인 분리
    # -------------------------------
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)

        if ch < (roi_y2 - roi_y1) * 0.45:
            continue
        if cw < 4 or cw > roi.shape[1] * 0.20:
            continue
        if cv2.contourArea(c) < 150:
            continue

        candidates.append((x, y, cw, ch))

    if not candidates:
        return 0, []

    # -------------------------------
    # 좌 → 우 정렬 (C / T)
    # -------------------------------
    candidates = sorted(candidates, key=lambda v: v[0])[:2]

    # -------------------------------
    # 박스 생성 (폭 통일)
    # -------------------------------
    max_w = max(cw for _, _, cw, _ in candidates)

    boxes = []
    for x, y, cw, ch in candidates:
        cx = x + cw // 2

        box_x = int(roi_x1 + cx - max_w // 2)
        box_y = roi_y1 + y
        box_w = max_w
        box_h = ch

        boxes.append((box_x, box_y, box_w, box_h))

    return len(boxes), boxes




# =========================================================
# [신규] 3라인 전용 반응라인 검출 (중심 기준 보정)
# =========================================================
def detect_reaction_3lines_from_image(img):
    """
    3라인 진단키트 전용 반응라인 검출 (좌표 보정 완료 버전)
    - 연한/진한 색상 무관
    - L1/L2/L3 위치 정확히 매칭
    - 반환: (라인 수, 박스 리스트)
    """

    h, w = img.shape[:2]

    # =========================
    # 1. ROI (Y축만 제한)
    # =========================
    roi_y1 = int(h * 0.35)
    roi_y2 = int(h * 0.58)
    roi = img[roi_y1:roi_y2, :]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # =========================
    # 2. 대비 강화
    # =========================
    clahe = cv2.createCLAHE(2.0, (8, 8))
    gray = clahe.apply(gray)

    # =========================
    # 3. 수직 투영 (전체 X 기준)
    # =========================
    proj = np.mean(255 - gray, axis=0)

    # =========================
    # 4. Threshold
    # =========================
    thresh = np.mean(proj) + np.std(proj) * 0.7
    mask = proj > thresh

    # =========================
    # 5. 연속 구간 검출
    # =========================
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

    if len(segments) == 0:
        return 0, []

    # =========================
    # 6. 중심 계산 (무게중심)
    # =========================
    centers = []
    for x1, x2 in segments:
        weights = proj[x1:x2]
        xs = np.arange(x1, x2)

        if np.sum(weights) > 0:
            cx = int(np.sum(xs * weights) / np.sum(weights))
        else:
            cx = int((x1 + x2) // 2)

        centers.append((cx, x1, x2))

    # =========================
    # 7. ⭐ 기대 위치 기반 매칭 (핵심 수정)
    # =========================
    expected = [
        int(w * 0.30),  # L1
        int(w * 0.50),  # L2
        int(w * 0.70),  # L3
    ]

    matched = []
    used = set()

    for exp_x in expected:
        best = None
        best_dist = 1e9

        for i, (cx, x1, x2) in enumerate(centers):
            if i in used:
                continue
            d = abs(cx - exp_x)
            if d < best_dist:
                best_dist = d
                best = (i, cx, x1, x2)

        if best:
            used.add(best[0])
            matched.append(best)

    # =========================
    # 8. 박스 생성 (폭 보정)
    # =========================
    print("matched:", matched)
    
    boxes = []
    min_box_w = int(w * 0.025)

    for _, cx, x1, x2 in matched:
        line_w = max(x2 - x1, min_box_w)
        box_x = max(0, int(cx - line_w // 2))

        boxes.append((
            box_x,
            roi_y1,
            line_w,
            roi_y2 - roi_y1
        ))

    return len(boxes), boxes


# =========================================================
# 포커스 보정 함수
# =========================================================
def focus_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# =========================================================
# 반응라인 박스 표시
# =========================================================
def draw_reaction_boxes(img, boxes, mode=2):
    """
    검출된 반응라인 박스 표시
    boxes:
      - [(x, y, w, h), ...] 또는
      - [{'x1':..,'y1':..,'x2':..,'y2':..,'id':..}, ...]
    mode : 2 or 3
    """

    for idx, box in enumerate(boxes):

        # ---------------------------
        # ✅ 박스 좌표 파싱 (핵심)
        # ---------------------------
        if isinstance(box, dict):
            x1 = int(box['x1'])
            y1 = int(box['y1'])
            x2 = int(box['x2'])
            y2 = int(box['y2'])
        else:
            x, y, w, h = box
            x1, y1 = int(x), int(y)
            x2, y2 = int(x + w), int(y + h)

        # ---------------------------
        # 라벨 / 색상
        # ---------------------------
        if mode == 2:
            color = (0, 255, 0) if idx == 0 else (0, 0, 255)
            label = "C" if idx == 0 else "T"
        else:
            color = (0, 0, 255)
            label = f"L{idx + 1}"

        # ---------------------------
        # 박스 표시
        # ---------------------------
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        cv2.putText(
            img,
            label,
            (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA
        )

# =========================================================
# 반응라인 박스 위치 보정.
# =========================================================
def refine_box_center_by_intensity(img, box, target_width=20):
    """
    연한 라인에서도 정확한 중심을 찾기 위한 X축 intensity 기반 보정
    box: (x, y, w, h)
    반환: (new_x, y, new_w, h)
    """

    x, y, w, h = box
    roi = img[y:y+h, x:x+w]

    if roi.size == 0:
        return box

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # X 방향 평균 intensity 프로파일
    profile = gray.mean(axis=0)

    # 가장 강한 반응 위치
    peak_x = int(np.argmax(profile))

    # 중심 기준으로 박스 재정렬
    center_x = x + peak_x
    new_x = int(center_x - target_width // 2)

    return (new_x, y, target_width, h)


# =========================================================
# 결과 라벨 생성
# =========================================================
def get_result_label(count, mode):
    text = "Positive"
    if count == 0:
        # return "무반응 (0)"
        text = "Error Line Count : " + str(count)
        return text 
    if mode == 2:
        if count == 2:
            text = "Positive Line Count : " + str(count)
        else:
            text = "Negative Line Count : " + str(count)
        return text
    else:
        return f"{count} Line Detected"

# =========================================================
# 썸네일 생성
# =========================================================
def create_thumbnail(img, original_path, max_size=300):
    os.makedirs(THUMB_SAVE_DIR, exist_ok=True)

    h, w        = img.shape[:2]
    scale       = max_size / max(h, w)
    thumb       = cv2.resize(img, (int(w * scale), int(h * scale)), cv2.INTER_AREA)

    base        = os.path.basename(original_path)
    name, ext   = os.path.splitext(base)
    thumb_path  = f"{THUMB_SAVE_DIR}/{name}_thumb{ext}"

    cv2.imwrite(thumb_path, thumb)
    return thumb_path

# =========================================================
# 메인
# =========================================================
def main():
    os.makedirs(IMG_SAVE_DIR, exist_ok=True)
    os.makedirs(JSON_SAVE_DIR, exist_ok=True)

    mode = get_detection_mode()

    cap = open_camera()
    led_on()
    time.sleep(1.0)

    print("📷 Stabilizing camera...")
    time.sleep(1.5)

    # 포커스 안정화
    print("📷 Adjusting focus...")
    best_score = 0
    best_frame = None

    # 🔥 ISP 안정화 프레임 버리기
    for _ in range(15):
        ret, frame = cap.read()
        if not ret:
            continue

        score = focus_score(frame)
        if score > best_score:
            best_score = score
            best_frame = frame.copy()

    # 포커스 최적 프레임 사용
    frame = best_frame

    if not ret:
        led_off()
        cap.release()
        raise RuntimeError("❌ Frame capture failed")

    ret, frame = cap.read()
    if not ret:
        led_off()
        cap.release()
        raise RuntimeError("❌ Frame capture failed")

    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path    = f"{IMG_SAVE_DIR}/capture_{ts}.png"
    json_path   = f"{JSON_SAVE_DIR}/capture_{ts}.json"

    cv2.imwrite(img_path, frame)
    print(f"✅ Image saved: {img_path}")

    img = cv2.imread(img_path)

    if img is None:
        led_off()
        cap.release()
        raise RuntimeError("❌ Failed to reload saved image")

    # 모드에 따른 반응라인 검출...
    if mode == 2:
        line_count, boxes = detect_reaction_lines_from_image(img)
    else:
        line_count, boxes = detect_reaction_3lines_from_image(img)

    draw_reaction_boxes(img, boxes, mode)

    label = get_result_label(line_count, mode)
    cv2.putText(
        img, label,
        (img.shape[1] // 2 - 120, img.shape[0] - 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2
    )

    cv2.imwrite(img_path, img)

    thumb_path = create_thumbnail(img, img_path)

    result = {
        "timestamp": ts,
        "image_path": img_path,
        "thumbnail_path": thumb_path,
        "json_path": json_path,
        "reaction_line_count": line_count,
        "mode": mode
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"🧾 JSON saved: {json_path}")
    print(f"🧾 JSON result: {result}")

    led_off()
    cap.release()
    print("🏁 Done")

# =========================================================
if __name__ == "__main__":
    main()
