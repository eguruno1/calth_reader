#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import json
import time
import serial
import numpy as np
import os
from datetime import datetime
from pyzbar.pyzbar import decode

# =========================================================
# 설정값
# =========================================================
CAM_WIDTH     = 1280
CAM_HEIGHT    = 720
FPS           = 30

LED_PORT      = "/dev/ttyTHS1"
LED_BAUD      = 115200
LED_ON_CMD    = "L45"
LED_OFF_CMD   = "L00"

# SAVE_DIR   = "captures"
IMG_SAVE_DIR  = "./CalthReaderResult/images"
JSON_SAVE_DIR = "./CalthReaderResult/json"

# =========================================================
# LED 제어
# =========================================================
def led_on():
    ser = serial.Serial(LED_PORT, LED_BAUD, timeout=1)
    ser.write(LED_ON_CMD.encode("ascii"))
    ser.close()
    print("💡 LED ON")

def led_off():
    ser = serial.Serial(LED_PORT, LED_BAUD, timeout=1)
    ser.write(LED_OFF_CMD.encode("ascii"))
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
# QR 코드 검출 (저장 이미지 기준)
# =========================================================
def detect_qr_from_image(img):
    qrs = decode(img)
    if not qrs:
        return None
    return qrs[0].data.decode("utf-8")

# =========================================================
# 반응라인(C/T) 검출 (저장 이미지 기준)
# =========================================================
def detect_reaction_lines_from_image(img):
    """
    최종 안정판:
    - C/T 라인 정확 판별
    - C: 초록 박스
    - T: 빨간 박스
    - 0 / 1 / 2 반환
    """

    h, w = img.shape[:2]

    # -------------------------------
    # ROI (고정 환경 기준)
    # -------------------------------
    roi_y1 = int(h * 0.38)
    roi_y2 = int(h * 0.58)
    roi_x1 = int(w * 0.25)
    roi_x2 = int(w * 0.75)

    roi = img[roi_y1:roi_y2, roi_x1:roi_x2].copy()

    # -------------------------------
    # R-G 강조
    # -------------------------------
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # -------------------------------
    # 세로 프로파일
    # -------------------------------
    vertical_sum = np.sum(binary, axis=0)
    vertical_sum = cv2.GaussianBlur(
        vertical_sum.astype(np.float32), (31, 1), 0
    )

    peak_threshold = np.max(vertical_sum) * 0.3

    peaks = []
    in_peak = False
    start = 0

    for x in range(len(vertical_sum)):
        if vertical_sum[x] > peak_threshold and not in_peak:
            in_peak = True
            start = x
        elif vertical_sum[x] <= peak_threshold and in_peak:
            end = x
            center = (start + end) // 2
            width = end - start
            strength = np.max(vertical_sum[start:end])
            peaks.append((center, strength, width))
            in_peak = False

    if in_peak:
        end = len(vertical_sum)
        center = (start + end) // 2
        width = end - start
        strength = np.max(vertical_sum[start:end])
        peaks.append((center, strength, width))

    if not peaks:
        return 0

    peaks = sorted(peaks, key=lambda x: x[0])

    # -------------------------------
    # C 라인 (완화 기준)
    # -------------------------------
    final_peaks = []

    c_center, c_strength, c_width = peaks[0]
    if c_width < 5 or c_strength < peak_threshold:
        return 0

    final_peaks.append(("C", c_center, c_width))

    # -------------------------------
    # T 라인 (엄격 기준)
    # -------------------------------
    if len(peaks) >= 2:
        t_center, t_strength, t_width = peaks[1]
        if (
            t_width >= 6
            and t_strength > c_strength * 0.35
            and abs(t_center - c_center) > 35
        ):
            final_peaks.append(("T", t_center, t_width))

    # -------------------------------
    # 박스 표시
    # -------------------------------
    for label, center, width in final_peaks:
        x = roi_x1 + center
        color = (0, 255, 0) if label == "C" else (0, 0, 255)

        cv2.rectangle(
            img,
            (x - width // 2, roi_y1),
            (x + width // 2, roi_y2),
            color,
            2
        )

        cv2.putText(
            img,
            label,
            (x - 10, roi_y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA
        )

    return len(final_peaks)



def detect_reaction_lines_from_image_ver1(img):
    """
    반응라인(C/T) 검출 – 최종 안정판 (C/T 분리 강화)
    - C 라인: 완화된 기준
    - T 라인: 조건부 검증
    - 결과: 0 / 1 / 2 정확 판별
    - 결과 이미지에 박스 표시
    """

    h, w = img.shape[:2]

    # -------------------------------------------------
    # 1️⃣ ROI (고정 촬영 기준)
    # -------------------------------------------------
    roi_y1 = int(h * 0.38)
    roi_y2 = int(h * 0.58)
    roi_x1 = int(w * 0.25)
    roi_x2 = int(w * 0.75)

    roi = img[roi_y1:roi_y2, roi_x1:roi_x2].copy()

    # -------------------------------------------------
    # 2️⃣ R-G 차이 강조
    # -------------------------------------------------
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)
    diff = cv2.GaussianBlur(diff, (5, 5), 0)

    _, binary = cv2.threshold(diff, 18, 255, cv2.THRESH_BINARY)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 9))
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)

    # -------------------------------------------------
    # 3️⃣ 세로 프로파일 peak 추출
    # -------------------------------------------------
    vertical_sum = np.sum(binary, axis=0)
    vertical_sum = cv2.GaussianBlur(vertical_sum.astype(np.float32), (31, 1), 0)

    threshold = np.max(vertical_sum) * 0.35
    peaks = []

    in_peak = False
    start = 0

    for x in range(len(vertical_sum)):
        if vertical_sum[x] > threshold and not in_peak:
            in_peak = True
            start = x
        elif vertical_sum[x] <= threshold and in_peak:
            end = x
            center = (start + end) // 2
            width = end - start
            strength = np.max(vertical_sum[start:end])
            peaks.append((center, strength, width))
            in_peak = False

    if in_peak:
        end = len(vertical_sum)
        center = (start + end) // 2
        width = end - start
        strength = np.max(vertical_sum[start:end])
        peaks.append((center, strength, width))

    if not peaks:
        return 0

    peaks = sorted(peaks, key=lambda x: x[0])

    # -------------------------------------------------
    # 4️⃣ 라인 검증 함수 (C / T 분리)
    # -------------------------------------------------
    def is_valid_reaction_line(roi, center, width, is_control):
        x1 = max(center - width // 2, 0)
        x2 = min(center + width // 2, roi.shape[1])
        strip = roi[:, x1:x2]
        if strip.size == 0:
            return False

        b, g, r = cv2.split(strip)
        r_mean = np.mean(r)
        g_mean = np.mean(g)

        # 🔹 색상 조건
        if is_control:
            if r_mean < g_mean * 1.02:
                return False
        else:
            if r_mean < g_mean * 1.08:
                return False

        # 🔹 분산 (잔상 제거)
        if np.std(r) > 45:
            return False

        # 🔹 배경 대비
        margin = 10
        bg_l = roi[:, max(0, x1 - margin):x1]
        bg_r = roi[:, x2:min(roi.shape[1], x2 + margin)]
        if bg_l.size == 0 or bg_r.size == 0:
            return False

        bg_r_mean = np.mean(np.concatenate([bg_l[:, :, 2], bg_r[:, :, 2]]))

        if is_control:
            return (r_mean - bg_r_mean) > 4
        else:
            return (r_mean - bg_r_mean) > 12

    # -------------------------------------------------
    # 5️⃣ C 라인 검증
    # -------------------------------------------------
    c_center, c_strength, c_width = peaks[0]
    if not is_valid_reaction_line(roi, c_center, c_width, is_control=True):
        return 0

    final_peaks = [(c_center, c_strength, c_width)]

    # -------------------------------------------------
    # 6️⃣ T 라인 검증 (있다면)
    # -------------------------------------------------
    if len(peaks) >= 2:
        t_center, t_strength, t_width = peaks[1]

        if (
            is_valid_reaction_line(roi, t_center, t_width, is_control=False)
            and t_strength > c_strength * 0.35
            and t_width >= 6
            and abs(t_center - c_center) > 35
        ):
            final_peaks.append((t_center, t_strength, t_width))

    # -------------------------------------------------
    # 7️⃣ 결과 박스 표시
    # -------------------------------------------------
    for idx, (center, strength, width) in enumerate(final_peaks):
        x = roi_x1 + center
        y1 = roi_y1
        y2 = roi_y2
        color = (0, 255, 0) if idx == 0 else (0, 0, 255)
        cv2.rectangle(
            img,
            (x - width // 2, y1),
            (x + width // 2, y2),
            color,
            2
        )

    return len(final_peaks)




def detect_reaction_lines_from_image_old(img):
    """
    반응라인(C/T) 검출 – 밴드 병합 기반 최종 안정판
    4개 판독
    """

    h, w = img.shape[:2]

    # -------------------------------------------------
    # 1. 반응창 ROI (고정 환경 기준)
    # -------------------------------------------------
    roi_y1 = int(h * 0.35)
    roi_y2 = int(h * 0.60)
    roi = img[roi_y1:roi_y2, :]

    # -------------------------------------------------
    # 2. 색상 강조 (R - G)
    # -------------------------------------------------
    b, g, r = cv2.split(roi)
    diff = cv2.subtract(r, g)

    # -------------------------------------------------
    # 3. 블러 + 이진화
    # -------------------------------------------------
    diff = cv2.GaussianBlur(diff, (9, 9), 0)
    _, binary = cv2.threshold(
        diff, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # -------------------------------------------------
    # 4. ★ 라인 굵기 강화 (핵심)
    # -------------------------------------------------
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT, (21, 7)
    )
    binary = cv2.dilate(binary, kernel, iterations=2)

    # -------------------------------------------------
    # 5. 세로 투영
    # -------------------------------------------------
    vertical_profile = np.sum(binary > 0, axis=0)
    vertical_profile = cv2.GaussianBlur(
        vertical_profile.astype(np.float32), (31, 1), 0
    )

    threshold = 0.4 * np.max(vertical_profile)

    # -------------------------------------------------
    # 6. 밴드 위치 추출
    # -------------------------------------------------
    bands = []
    in_band = False
    start = 0

    for x, v in enumerate(vertical_profile):
        if v > threshold and not in_band:
            start = x
            in_band = True
        elif v <= threshold and in_band:
            end = x
            bands.append((start, end))
            in_band = False

    if in_band:
        bands.append((start, len(vertical_profile) - 1))

    # -------------------------------------------------
    # 7. ★ 밴드 병합 (이게 최종 해결책)
    # -------------------------------------------------
    MERGE_DISTANCE = 40  # 고정 촬영 환경 기준

    merged_centers = []
    for start, end in bands:
        center = (start + end) // 2

        if not merged_centers:
            merged_centers.append(center)
        else:
            if abs(center - merged_centers[-1]) < MERGE_DISTANCE:
                # 같은 라인 → 병합
                merged_centers[-1] = (merged_centers[-1] + center) // 2
            else:
                merged_centers.append(center)

    return len(merged_centers)


# =========================================================
# 포커스 보정 함수
# =========================================================
def focus_score(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# =========================================================
# 제공해준 반응라인 판독용 함수
# =========================================================
def colorimetric_analyze(cropped_img):
    def smooth(y, box_pts):
        box = np.ones(box_pts) / box_pts
        y_smooth = np.convolve(y, box, mode="same")
        return y_smooth

    r, g, b = cv2.split(cropped_img)
    h, w = g.shape

    inside_cut = g[int(h * 0.2):int(h * 0.8), int(w * 0.30):int(w * 0.70)]
    signal = np.array(inside_cut).mean(axis=1)
    x = np.linspace(0, 1, len(signal))

    if h <= 50:
        ws = int(h*0.05)
        margin = int(h*0.05)
    else:
        ws = 15
        margin = 10

    smooth_signal = smooth(signal, ws)
    left = np.mean(smooth_signal[ws:-ws][:margin])
    line = np.min(smooth_signal[ws:-ws])
    right = np.mean(smooth_signal[ws:-ws][-margin:])
    residual = min(left, right) - line
    # bigger than 1.5 -> positive
    return residual

# =========================================================
# 판독 결과 텍스트 추가 함수
# =========================================================
def draw_result_label(img, line_count):
    h, w = img.shape[:2]

    if line_count == 2:
        text = "Positive"
        color = (0, 0, 255)
    elif line_count == 1:
        text = "Negative"
        color = (0, 255, 0)
    else:
        text = "Error"
        color = (200, 200, 200)
    
    text = text + " Line Count : " + str(line_count)

    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1.2
    thickness = 3

    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)

    x = (w - tw) // 2
    y = h - 30

    # 배경 패드
    cv2.rectangle(
        img,
        (x - 20, y - th - 20),
        (x + tw + 20, y + 10),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        img,
        text,
        (x, y),
        font,
        scale,
        color,
        thickness,
        cv2.LINE_AA
    )



# =========================================================
# 메인 로직
# =========================================================
def main():
    os.makedirs(IMG_SAVE_DIR, exist_ok=True)
    os.makedirs(JSON_SAVE_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path  = f"{IMG_SAVE_DIR}/capture_{ts}.png"
    json_path = f"{JSON_SAVE_DIR}/capture_{ts}.json"

    try:

        # 1. LED ON
        led_on()
        time.sleep(1.0)

        # 2. 카메라 오픈
        cap = open_camera()

        # 3. 노출/게인 안정화 대기
        print("📷 Stabilizing camera...")
        time.sleep(1.5)

        # 3. 포커스 안정화
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

        # 4. 프레임 1장 캡처
        # ret, frame = cap.read()
        if not ret:
            led_off()
            cap.release()
            raise RuntimeError("❌ Frame capture failed")

        # 5. 이미지 저장
        cv2.imwrite(img_path, frame)
        print(f"✅ Image saved: {img_path}")

        # 6. 저장된 이미지 다시 로드 (중요!)
        img = cv2.imread(img_path)
        if img is None:
            led_off()
            cap.release()
            raise RuntimeError("❌ Failed to reload saved image")

        # 7-1. QR 코드 검출 (저장 이미지 기준) : QR Not Use
        # qr_text = detect_qr_from_image(img)
        qr_text = None

        # 7-2. 반응라인 검출 (저장 이미지 기준)
        line_count = detect_reaction_lines_from_image(img)
        print(f"✅ Line Count 1: {line_count}")
        # 검출결과 합성.
        draw_result_label(img, line_count)
        cv2.imwrite(img_path, img)

        # 7-3. 제공된 반응라인 함수
        line_count2 = colorimetric_analyze(img)
        print(f"✅ Line Count 2: {line_count2}")

        # 8. JSON 결과 저장
        result = {
            "timestamp": ts,
            "image_path": img_path,
            "qr_detected": qr_text is not None,
            "qr_text": qr_text,
            "reaction_line_count1": line_count,
            "reaction_line_count2": line_count2
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"🧾 JSON saved: {json_path}")

        # 9. LED OFF & 자원 해제
        led_off()
        cap.release()

        print("🏁 Done")

    finally:
        # 🔴 이게 없으면 Argus가 죽습니다
        if cap is not None:
            cap.release()
        led_off()
        cv2.destroyAllWindows()
# =========================================================
if __name__ == "__main__":
    main()
