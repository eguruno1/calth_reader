"""
test_led_cam_qr의 Docstring
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_led_cam_qr.py

[동작 순서]
1. 카메라 오픈 (Jetson ISP 경유)
2. LED ON (UART)
3. 자동 초점 대기 (프레임 안정화)
4. 이미지 1장 촬영
5. 이미지 저장
6. QR 코드 존재 여부 확인 및 스캔 (1회)
7. 반응 라인 검출
8. 모든 결과 JSON 파일로 저장
"""

import cv2
import os
import time
import json
import serial
import numpy as np
from datetime import datetime

# ============================================================
# [1] 환경 설정
# ============================================================

IMG_SAVE_DIR = "./CalthReaderResult/images"
JSON_SAVE_DIR = "./CalthReaderResult/json"

os.makedirs(IMG_SAVE_DIR, exist_ok=True)
os.makedirs(JSON_SAVE_DIR, exist_ok=True)

# UART (LED 제어)
UART_PORT = "/dev/ttyTHS2"  # "/dev/ttyTHS1"
UART_BAUD = 115200

LED_ON_CMD = "L45"
LED_OFF_CMD = "L00"

# ============================================================
# [2] LED 제어 함수
# ============================================================

def led_on(ser):
    ser.write(LED_ON_CMD.encode())
    ser.flush()
    print("💡 LED ON")

def led_off(ser):
    ser.write(LED_OFF_CMD.encode())
    ser.flush()
    print("💡 LED OFF")

# ============================================================
# [3] Jetson ISP 카메라 오픈
# ============================================================

def open_camera():
    """
    IMX219 + Jetson
    - ISP 사용
    - 노출 / 게인 고정
    - 근거리 키트 촬영 안정화
    """

    gst_pipeline = (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=3264, height=2464, framerate=21/1 ! "
        "nvvidconv ! "
        "video/x-raw, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! appsink drop=1 sync=false"
    )

    """기존 테스트 속성
    gst_pipeline = (
        "nvarguscamerasrc sensor-id=0 "
        "exposuretimerange=\"100000 100000\" "
        "gainrange=\"1 1\" "
        "aeantibanding=0 ! "
        "video/x-raw(memory:NVMM), "
        "width=3264, height=2464, framerate=21/1 ! "
        "nvvidconv ! "
        "video/x-raw, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! "
        "appsink drop=1 sync=false"
    )

    gst_pipeline = (
        "nvarguscamerasrc ! "
        "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
        "nvvidconv flip-method=2 ! "
        "video/x-raw, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! appsink max-buffers=1 drop=true"
    )
    """

    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    if not cap.isOpened():
        raise RuntimeError("❌ Camera open failed (ISP pipeline)")

    print("📷 Camera opened (3264x2464 @21fps, ISP OK)")
    return cap

# ============================================================
# [4] 초점 안정화 (프레임 워밍업)
# ============================================================

def focus_warmup(cap, seconds=2):
    """
    Jetson 카메라는 첫 프레임들이 불안정함
    → 일정 시간 프레임 버림
    """
    print("📷 Focusing...")
    t0 = time.time()
    last = None

    while time.time() - t0 < seconds:
        ret, frame = cap.read()
        if ret:
            last = frame

    if last is None:
        raise RuntimeError("❌ No frame captured")

    return last

# ============================================================
# [5] QR 코드 스캔 (1회)
# ============================================================

def detect_qr(image):
    qr = cv2.QRCodeDetector()
    data, pts, _ = qr.detectAndDecode(image)

    if data:
        print("📦 QR detected:", data)
        return True, data
    else:
        print("📦 QR not detected")
        return False, None

# ============================================================
# [6] 반응 라인 검출
# ============================================================

def detect_reaction_lines(image):
    """
    단순 수직 라인 개수 검출 예제
    (C/T 라인 존재 여부 판단용)
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Canny는 반드시 uint8
    edges = cv2.Canny(gray, 40, 120)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=120,
        minLineLength=80,
        maxLineGap=10
    )

    count = 0
    if lines is not None:
        for l in lines:
            x1, y1, x2, y2 = l[0]
            # 거의 수직인 선만 카운트
            if abs(x1 - x2) < 10:
                count += 1

    print(f"🧪 Reaction lines detected: {count}")
    return count

# ============================================================
# [7] 메인 로직
# ============================================================

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(IMG_SAVE_DIR, f"capture_{timestamp}.jpg")
    json_path = os.path.join(JSON_SAVE_DIR, f"result_{timestamp}.json")

    result = {
        "timestamp": timestamp,
        "image": image_path,
        "qr_detected": False,
        "qr_data": None,
        "reaction_line_count": 0
    }

    # UART 연결
    ser = serial.Serial(UART_PORT, UART_BAUD, timeout=1)

    try:
        cap = open_camera()

        # LED ON
        led_on(ser)

        # 초점 안정화
        frame = focus_warmup(cap)

        # LED OFF (촬영 직후)
        led_off(ser)

        # 이미지 저장
        cv2.imwrite(image_path, frame)
        print("📸 Image saved:", image_path)

        # QR 코드 스캔 (1회)
        qr_ok, qr_data = detect_qr(frame)
        result["qr_detected"] = qr_ok
        result["qr_data"] = qr_data

        # 반응 라인 검출
        line_count = detect_reaction_lines(frame)
        result["reaction_line_count"] = line_count

        # JSON 저장
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        print("📝 JSON saved:", json_path)

    finally:
        try:
            cap.release()
        except:
            pass
        ser.close()

    print("✅ Done")

# ============================================================
# [8] 실행 진입점
# ============================================================

if __name__ == "__main__":
    main()
