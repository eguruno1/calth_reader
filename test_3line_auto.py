"""
test_3line_auto 의 Docstring
카메라 위치 변경으로 ROI 영역확대
위치 자동 판독 추가.

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
    2라인(C / T) 자동 판독 (1280x720 기준 안정 버전)

    ✔ 카메라 입력 해상도: 1280 x 720 (리사이즈 없음)
    ✔ 카메라 위치 변경 자동 보정 (Y축 ROI 재정렬)
    ✔ 진한 C / 연한 T 모두 대응
    ✔ 좌표계: 모든 box 좌표는 '원본 이미지 기준'

    반환:
      line_count : 검출된 라인 수 (0 / 1 / 2)
      boxes      : [(x, y, w, h), ...]  ← img 좌표
      metrics    : [{label, center_x, intensity, confidence}]
    """

    # -----------------------------------------------------
    # 0️⃣ 입력 이미지 크기 (1280x720 전제)
    # -----------------------------------------------------
    h, w = img.shape[:2]  # h=720, w=1280

    # =====================================================
    # 1️⃣ 1차 Wide ROI
    # =====================================================
    wide_y1 = int(h * 0.28)
    wide_y2 = int(h * 0.65)
    wide_roi = img[wide_y1:wide_y2, :]

    gray = cv2.cvtColor(wide_roi, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(2.0, (8, 8))
    gray = clahe.apply(gray)

    proj_y = np.mean(255 - gray, axis=1)
    thresh_y = np.mean(proj_y) + np.std(proj_y) * 0.6

    ys = np.where(proj_y > thresh_y)[0]
    if len(ys) < 10:
        return 0, [], []

    center_y = int(np.mean(ys)) + wide_y1

    # =====================================================
    # 2️⃣ 자동 재정렬 ROI
    # =====================================================
    roi_h = int(h * 0.18)
    roi_y1 = max(0, center_y - roi_h // 2)
    roi_y2 = min(h, center_y + roi_h // 2)

    roi = img[roi_y1:roi_y2, :]

    # =====================================================
    # 3️⃣ 색상 기반 라인 강조 (R - G)
    # =====================================================
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 12, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 11))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # =====================================================
    # 4️⃣ X축 투영 → 후보 라인 검출
    # =====================================================
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
        return 0, [], []

    # =====================================================
    # 5️⃣ 라인 중심 / 강도 계산
    # =====================================================
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

    # 좌 → 우 정렬 (C 먼저, T 다음)
    lines.sort(key=lambda x: x["cx"])

    # =====================================================
    # 6️⃣ C / T 판정 + 박스 생성
    # =====================================================
    metrics = []
    boxes = []

    # 🔧 FIX: dict 기반 intensity 접근
    max_int = max(l["intensity"] for l in lines)

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

    return len(boxes), boxes, metrics

# =========================================================
# [신규] 3라인 전용 반응라인 검출 (2라인 판독 기준 통합)
# =========================================================
def detect_reaction_3lines_from_image(img):
    """
    3라인 진단키트 전용 반응라인 검출 (2라인 알고리즘 통합 최종판)

    ✔ 2라인과 동일한 박스 기준 (ROI 중심 기반)
    ✔ 실제 판독라인 위치 정합
    ✔ metrics (label / intensity / confidence) 동일 구조
    ✔ 반환:
        line_count : 검출 라인 수
        boxes      : [(x, y, w, h)]
        metrics    : [{label, center_x, intensity, confidence}]
    """

    h, w = img.shape[:2]

    # =====================================================
    # 1️⃣ ROI 설정 (기존 유지)
    # =====================================================
    roi_y1 = int(h * 0.35)
    roi_y2 = int(h * 0.58)
    roi = img[roi_y1:roi_y2, :]

    roi_h, roi_w = roi.shape[:2]

    # =====================================================
    # 2️⃣ R-G 강조 (2라인과 동일)
    # =====================================================
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 12, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # =====================================================
    # 3️⃣ X축 투영 (intensity 계산용)
    # =====================================================
    col_sum = np.sum(binary, axis=0).astype(np.float32)
    col_sum = cv2.GaussianBlur(col_sum, (31, 1), 0)

    thresh = np.mean(col_sum) + np.std(col_sum) * 0.5
    active = col_sum > thresh

    # =====================================================
    # 4️⃣ 연속 X 세그먼트 검출
    # =====================================================
    segments = []
    start = None

    for x in range(len(active)):
        if active[x] and start is None:
            start = x
        elif not active[x] and start is not None:
            if x - start > 6:
                segments.append((start, x))
            start = None

    if start is not None and len(active) - start > 6:
        segments.append((start, len(active)))

    if not segments:
        return 0, [], []

    # =====================================================
    # 5️⃣ 세그먼트 기반 라인 정보 계산
    # =====================================================
    lines = []

    for x1, x2 in segments:
        cx = (x1 + x2) // 2
        intensity = float(np.max(col_sum[x1:x2]))

        lines.append({
            "cx": cx,
            "x1": x1,
            "x2": x2,
            "intensity": intensity
        })

    if not lines:
        return 0, [], []

    # =====================================================
    # 6️⃣ 기대 위치 기반 L1/L2/L3 매칭 (기존 유지)
    # =====================================================
    expected = [
        int(w * 0.30),  # L1
        int(w * 0.50),  # L2
        int(w * 0.70),  # L3
    ]

    matched = []
    used = set()

    for idx, exp_x in enumerate(expected):
        best = None
        best_dist = 1e9

        for i, line in enumerate(lines):
            if i in used:
                continue
            d = abs(line["cx"] - exp_x)
            if d < best_dist:
                best_dist = d
                best = (i, line)

        if best:
            used.add(best[0])
            best[1]["label"] = f"L{idx+1}"
            matched.append(best[1])

    if not matched:
        return 0, [], []

    # =====================================================
    # 7️⃣ 박스 생성 (2라인 판독 기준 동일)
    # =====================================================
    boxes = []
    metrics = []

    roi_center_y = (roi_y1 + roi_y2) // 2
    roi_total_h = roi_y2 - roi_y1
    line_h = int(roi_total_h * 0.55)

    max_int = max(l["intensity"] for l in matched)

    for line in matched:
        cx = line["cx"]
        x1 = line["x1"]
        x2 = line["x2"]
        intensity = line["intensity"]
        label = line["label"]

        box_w = max(x2 - x1, int(w * 0.015))
        box_x = max(0, min(w - box_w, cx - box_w // 2))

        box_y = int(roi_center_y - line_h // 2)
        box_y = max(0, min(h - line_h, box_y))

        boxes.append((
            int(box_x),
            int(box_y),
            int(box_w),
            int(line_h)
        ))

        metrics.append({
            "label": label,
            "center_x": cx,
            "intensity": round(intensity, 2),
            "confidence": round(intensity / (max_int + 1e-6), 3)
        })

    return len(boxes), boxes, metrics


# =========================================================
# 포커스 보정 함수
# =========================================================
def focus_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

# =========================================================
# 반응라인 박스 표시 (2라인 / 3라인 공용)
# =========================================================
def draw_reaction_boxes(img, boxes, metrics, mode=2):
    """
    검출된 반응라인 박스 표시(좌표 안전 보정 포함)

    boxes   : [(x, y, w, h), ...]
    metrics : [{'label': 'C'|'T'|'T1'..., 'confidence':..., ...}, ...]
    mode    : 2 or 3
    """

    img_h, img_w = img.shape[:2]

    for box, metric in zip(boxes, metrics):

        # ---------------------------
        # 박스 좌표 파싱
        # ---------------------------
        if isinstance(box, dict):
            x1 = int(box['x1'])
            y1 = int(box['y1'])
            x2 = int(box['x2'])
            y2 = int(box['y2'])
        else:
            x, y, w, h = box
            x1 = int(x)
            y1 = int(y)
            x2 = int(x + w)
            y2 = int(y + h)

        # ---------------------------
        # 🚨 좌표 유효성 검사 (핵심)
        # ---------------------------
        if x2 <= 0 or y2 <= 0 or x1 >= img_w or y1 >= img_h:
            print(f"⚠️ box out of image, skip: {(x1,y1,x2,y2)}")
            continue

        # 이미지 범위로 clamp
        x1 = max(0, min(x1, img_w - 1))
        y1 = max(0, min(y1, img_h - 1))
        x2 = max(0, min(x2, img_w - 1))
        y2 = max(0, min(y2, img_h - 1))

        label = metric.get("label", "L")
        conf = metric.get("confidence", 0.0)

        if label == "C":
            color = (0, 255, 0)
        elif label.startswith("T"):
            color = (0, 0, 255)
        else:
            color = (255, 0, 0)

        # ---------------------------
        # 박스 표시
        # ---------------------------
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)

        text = f"{label} ({conf:.2f})"
        print(f"🧾 draw box: {text}, box={(x1,y1,x2,y2)}")

        cv2.putText(
            img,
            text,
            (x1, max(0, y1 - 8)),
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
    # detect 함수에 들어가는 img와
    # draw에 쓰는 img를 반드시 동일 객체로 유지
    img_for_detect = img.copy()
    if mode == 2:
        line_count, boxes, metrics = detect_reaction_lines_from_image(img_for_detect)
    else:
        line_count, boxes, metrics = detect_reaction_3lines_from_image(img_for_detect)

    draw_reaction_boxes(img, boxes, metrics, mode)

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

    if metrics:
        print(f"🧾 Metrics result: {metrics}")

    led_off()
    cap.release()
    print("🏁 Done")

# =========================================================
if __name__ == "__main__":
    main()
