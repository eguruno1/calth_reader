import cv2
import numpy as np
import time

# ================================
# Camera Open (ISP 적용)
# ================================
def open_camera():
    gst = (
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

    cap = cv2.VideoCapture(gst, cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        raise RuntimeError("❌ Camera open failed")

    return cap


# ================================
# Sharpness Metric (Laplacian)
# ================================
def calc_sharpness(gray):
    return cv2.Laplacian(gray, cv2.CV_64F).var()


# ================================
# Main Preview Loop
# ================================
def main():
    cap = open_camera()
    print("📷 Camera opened - Focus adjustment mode")

    best_score = 0.0

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        h, w, _ = frame.shape

        # ---- 중앙 ROI 설정 ----
        roi_w = int(w * 0.4)
        roi_h = int(h * 0.3)
        x1 = (w - roi_w) // 2
        y1 = (h - roi_h) // 2
        roi = frame[y1:y1+roi_h, x1:x1+roi_w]

        # ---- Sharpness 계산 ----
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        sharpness = calc_sharpness(gray)
        best_score = max(best_score, sharpness)

        # ---- 시각화 ----
        display = frame.copy()

        # ROI 박스
        cv2.rectangle(
            display,
            (x1, y1),
            (x1 + roi_w, y1 + roi_h),
            (0, 255, 0),
            3
        )

        # 텍스트 표시
        cv2.putText(
            display,
            f"Sharpness: {sharpness:.1f}",
            (40, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.6,
            (0, 255, 0),
            3
        )

        cv2.putText(
            display,
            f"Best: {best_score:.1f}",
            (40, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (0, 200, 255),
            2
        )

        cv2.putText(
            display,
            "Rotate lens slowly - maximize Sharpness",
            (40, h - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (255, 255, 255),
            2
        )

        cv2.imshow("IMX219 Focus Adjustment", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Focus preview closed")


# ================================
if __name__ == "__main__":
    main()
