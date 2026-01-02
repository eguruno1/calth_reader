#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2
import json
import time
import serial
import numpy as np
from datetime import datetime
from pyzbar.pyzbar import decode

# =========================
# 설정
# =========================
CAM_WIDTH  = 3264
CAM_HEIGHT = 2464
FPS        = 21

LED_PORT   = "/dev/ttyTHS1"
LED_BAUD   = 115200

# SAVE_DIR   = "captures"
IMG_SAVE_DIR  = "./CalthReaderResult/images"
JSON_SAVE_DIR = "./CalthReaderResult/json"

# =========================
# LED 제어
# =========================
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

# =========================
# 카메라 오픈 (ISP)
# =========================
def open_camera(): 
    gst_pipeline = (
        "nvarguscamerasrc ! "
        f"video/x-raw(memory:NVMM),width={CAM_WIDTH},height={CAM_HEIGHT},framerate={FPS}/1 ! "
        "nvvidconv ! video/x-raw,format=BGRx ! "
        "videoconvert ! video/x-raw,format=BGR ! appsink"
    )
    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        raise RuntimeError("❌ Camera open failed")
    return cap

# =========================
# QR 코드 인식
# =========================
def detect_qr(img):
    qrs = decode(img) # pzbar lib 사용.
    if not qrs:
        return None
    return qrs[0].data.decode("utf-8")

# =========================
# 반응라인(C/T) 검출 (단순 안정판)
# =========================
def detect_reaction_lines(img):
    gray  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur  = cv2.GaussianBlur(gray, (5,5), 0)
    edges = cv2.Canny(blur, 50, 150)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi/180,
        threshold=120,
        minLineLength=80,
        maxLineGap=10
    )

    return 0 if lines is None else len(lines)

# =========================
# 메인
# =========================
def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path  = f"{IMG_SAVE_DIR}/capture_{ts}.png"
    json_path = f"{JSON_SAVE_DIR}/capture_{ts}.json"

    cap = open_camera()
    led_on()

    print("📷 Stabilizing camera...")
    time.sleep(1.5)   # 노출 안정화

    ret, frame = cap.read()
    if not ret:
        led_off()
        raise RuntimeError("❌ Frame capture failed")

    cv2.imwrite(img_path, frame)
    print(f"✅ Image saved: {img_path}")

    qr_text    = detect_qr(frame)
    line_count = detect_reaction_lines(frame)

    result = {
        "timestamp": ts,
        "image": img_path,
        "qr_detected": qr_text is not None,
        "qr_text": qr_text,
        "reaction_line_count": line_count
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"🧾 JSON saved: {json_path}")

    led_off()
    cap.release()
    print("🏁 Done")

if __name__ == "__main__":
    import os
    os.makedirs(IMG_SAVE_DIR, exist_ok=True)
    os.makedirs(JSON_SAVE_DIR, exist_ok=True)
    main()
