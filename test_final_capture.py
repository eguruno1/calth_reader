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
CAM_WIDTH  = 3264
CAM_HEIGHT = 2464
FPS        = 21

LED_PORT   = "/dev/ttyTHS1"
LED_BAUD   = 115200

# SAVE_DIR   = "captures"
IMG_SAVE_DIR  = "./CalthReaderResult/images"
JSON_SAVE_DIR = "./CalthReaderResult/json"

# =========================================================
# LED 제어
# =========================================================
def led_on():
    ser = serial.Serial(LED_PORT, LED_BAUD, timeout=1)
    ser.write(b"L45")
    ser.close()
    print("💡 LED ON")

def led_off():
    ser = serial.Serial(LED_PORT, LED_BAUD, timeout=1)
    ser.write(b"L00")
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
    단순/안정판:
    - Canny Edge
    - HoughLinesP
    - 검출된 선 개수 반환
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blur, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=120,
        minLineLength=80,
        maxLineGap=10
    )

    return 0 if lines is None else len(lines)

# =========================================================
# 메인 로직
# =========================================================
def main():
    os.makedirs(IMG_SAVE_DIR, exist_ok=True)
    os.makedirs(JSON_SAVE_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path  = f"{IMG_SAVE_DIR}/capture_{ts}.png"
    json_path = f"{JSON_SAVE_DIR}/capture_{ts}.json"

    # 1. 카메라 오픈
    cap = open_camera()

    # 2. LED ON
    led_on()

    # 3. 노출/게인 안정화 대기
    print("📷 Stabilizing camera...")
    time.sleep(1.5)

    # 4. 프레임 1장 캡처
    ret, frame = cap.read()
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

    # 7-1. QR 코드 검출 (저장 이미지 기준)
    qr_text = detect_qr_from_image(img)

    # 7-2. 반응라인 검출 (저장 이미지 기준)
    line_count = detect_reaction_lines_from_image(img)

    # 8. JSON 결과 저장
    result = {
        "timestamp": ts,
        "image_path": img_path,
        "qr_detected": qr_text is not None,
        "qr_text": qr_text,
        "reaction_line_count": line_count
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"🧾 JSON saved: {json_path}")

    # 9. LED OFF & 자원 해제
    led_off()
    cap.release()

    print("🏁 Done")

# =========================================================
if __name__ == "__main__":
    main()
