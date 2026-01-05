"""
test_final_scan_kit_images의 Docstring

1. 이미지 로드
2. detect_2d_code()
   ├─ 실패 → line_count = 0
   └─ 성공 → qr_rect 확보
3. detect_reaction_lines(qr_rect 기준)
4. JSON 기록
"""

import cv2
import numpy as np
from pyzbar import pyzbar
import os
import json
from datetime import datetime
from pylibdmtx.pylibdmtx import decode as dm_decode

IMAGE_DIR = "./images"
TARGET_IMAGES = [
    "kit_bench_2line_ok.jpeg",
    "kit_bench_2line_ok_2.jpeg"
]

def detect_datamatrix(image):
    """
    산업용 수준 DataMatrix 검출 파이프라인
    - 자동 ROI
    - 스케일 피라미드
    - 다중 이진화
    - 회전 sweep
    """

    h, w = image.shape[:2]

    # 🔹 1. 상단 40%를 '후보 영역'으로 설정
    search_roi = image[0:int(h * 0.4), :]

    gray_full = cv2.cvtColor(search_roi, cv2.COLOR_BGR2GRAY)

    # 🔹 2. 스케일 피라미드 (작은 DM 대응)
    scales = [1.0, 1.5, 2.0, 2.5]

    for scale in scales:
        resized = cv2.resize(
            gray_full,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_CUBIC
        )

        # 🔹 3. 여러 이진화 방식
        binaries = []

        # (1) Adaptive
        binaries.append(
            cv2.adaptiveThreshold(
                resized, 255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31, 5
            )
        )

        # (2) OTSU
        _, otsu = cv2.threshold(
            resized, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        binaries.append(otsu)

        # (3) Canny edge 강조
        edges = cv2.Canny(resized, 50, 150)
        binaries.append(edges)

        # 🔹 4. 회전 sweep
        for bin_img in binaries:
            for angle in [0, 90, 180, 270]:
                if angle == 0:
                    test = bin_img
                elif angle == 90:
                    test = cv2.rotate(bin_img, cv2.ROTATE_90_CLOCKWISE)
                elif angle == 180:
                    test = cv2.rotate(bin_img, cv2.ROTATE_180)
                else:
                    test = cv2.rotate(bin_img, cv2.ROTATE_90_COUNTERCLOCKWISE)

                try:
                    results = dm_decode(
                        test,
                        timeout=800,
                        max_count=1
                    )
                except Exception:
                    continue

                if results:
                    text = results[0].data.decode("utf-8", errors="ignore")
                    return text, True

    return None, False


def detect_2d_code(image):
    """
    안정형 DataMatrix 스캐너
    - 다중 ROI
    - 다중 전처리
    - fail-safe 구조
    """

    h, w = image.shape[:2]

    roi_configs = [
        (0.00, 0.20, 0.00, 0.35),
        (0.00, 0.20, 0.30, 0.70),
        (0.00, 0.20, 0.65, 1.00),
        (0.00, 0.25, 0.15, 0.85),
        (0.00, 0.30, 0.00, 1.00),
    ]

    for (ry1, ry2, rx1, rx2) in roi_configs:
        y1 = int(h * ry1)
        y2 = int(h * ry2)
        x1 = int(w * rx1)
        x2 = int(w * rx2)

        roi = image[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # 🔥 전처리 세트 여러 개
        preprocessors = [
            lambda x: x,  # raw
            lambda x: cv2.GaussianBlur(x, (3, 3), 0),
            lambda x: cv2.createCLAHE(2.5, (8, 8)).apply(x),
        ]

        for prep in preprocessors:
            g = prep(gray)

            if g.shape[1] > 640:
                scale = 640 / g.shape[1]
                g = cv2.resize(g, None, fx=scale, fy=scale)

            try:
                results = dm_decode(
                    g,
                    timeout=300,
                    max_count=1
                )
            except Exception:
                continue

            if results:
                code = results[0]
                text = code.data.decode("utf-8", errors="ignore")
                x, y, w_box, h_box = code.rect

                return text, (x + x1, y + y1, w_box, h_box)

    return None, None


def detect_2d_code_single(image):
    """
    DataMatrix(ECC200) 고신뢰 스캐너
    - 다중 ROI 탐색
    - 위치/크기 변화 대응

    최적화 포인트:
    1. ROI 정책
    ┌──────────────────────────┐
    │ ROI 1: 상단 좌측 (작음)     │
    ├──────────────────────────┤
    │ ROI 2: 상단 중앙 (작음)     │
    ├──────────────────────────┤
    │ ROI 3: 상단 우측 (작음)     │
    ├──────────────────────────┤
    │ ROI 4: 상단 전체 (중간)     │
    ├──────────────────────────┤
    │ ROI 5: 상단 전체 (큼)       │
    └──────────────────────────┘
    """

    h, w = image.shape[:2]

    # --------------------------------------------
    # 1️⃣ ROI 후보군 정의 (위치 + 크기 다양화)
    # --------------------------------------------
    roi_configs = [
        # (y1, y2, x1, x2)
        (0.00, 0.20, 0.00, 0.35),   # 상단 좌측 (작음)
        (0.00, 0.20, 0.30, 0.70),   # 상단 중앙 (작음)
        (0.00, 0.20, 0.65, 1.00),   # 상단 우측 (작음)

        (0.00, 0.25, 0.15, 0.85),   # 상단 중앙 (중간)
        (0.00, 0.30, 0.00, 1.00),   # 상단 전체 (큼)
    ]

    for (ry1, ry2, rx1, rx2) in roi_configs:
        y1 = int(h * ry1)
        y2 = int(h * ry2)
        x1 = int(w * rx1)
        x2 = int(w * rx2)

        roi = image[y1:y2, x1:x2]

        if roi.size == 0:
            continue

        # ----------------------------------------
        # 2️⃣ 전처리
        # ----------------------------------------
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

        # 해상도 제한 (속도 핵심)
        max_width = 640
        if gray.shape[1] > max_width:
            scale = max_width / gray.shape[1]
            gray = cv2.resize(
                gray, None, fx=scale, fy=scale,
                interpolation=cv2.INTER_AREA
            )

        # ----------------------------------------
        # 3️⃣ DataMatrix 디코딩
        # ----------------------------------------
        results = dm_decode(
            gray,
            timeout=200,    # ROI 단위 제한
            max_count=1
        )

        if results:
            code = results[0]
            text = code.data.decode("utf-8", errors="ignore")

            x, y, w_box, h_box = code.rect

            # 전체 이미지 기준 좌표로 변환
            x_full = x + x1
            y_full = y + y1

            return text, (x_full, y_full, w_box, h_box)

    # 전부 실패
    return None, None


def detect_reaction_lines(image):
    h, w = image.shape[:2]

    # 🔹 키트 중앙 반응창 (비율 기반)
    roi = image[
        int(h * 0.35):int(h * 0.65),
        int(w * 0.35):int(w * 0.65)
    ]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blur, 40, 120)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=60,
        minLineLength=roi.shape[1] * 0.5,
        maxLineGap=10
    )

    if lines is None:
        return 0

    # 🔹 수평선만 카운트
    count = 0
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(y1 - y2) < 5:
            count += 1

    return min(count, 2)


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

        # qr_text, qr_rect = detect_qr(image) # QR
        qr_text, qr_detected = detect_datamatrix(image) # DataMatrix
        print(f"[QR or DataMatrix] Find to load: {qr_detected}")
        line_count = detect_reaction_lines(image)

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
