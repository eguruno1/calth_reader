"""
test_opencv_qr_v2의 Docstring
의료기기/진단키트 쪽에서는 OpenCV + pyzbar 이중화가 사실상 표준

pip install pyzbar pillow

※ macOS에서 에러 나면:
brew install zbar

Ubuntu 사전 설치 (필수)
sudo apt update
sudo apt install -y libzbar0 libzbar-dev
pip install opencv-python pyzbar numpy
"""
import cv2
import numpy as np
import json
import math
from pyzbar.pyzbar import decode


# ============================================================
# QR DETECTION & ROTATION
# ============================================================

def detect_qr(img):
    """
    QR 코드 탐지 및 텍스트 추출
    """
    qr_objs = decode(img)
    if not qr_objs:
        return None, None

    qr = qr_objs[0]
    text = qr.data.decode("utf-8").strip()
    points = qr.polygon

    if len(points) < 4:
        return text, None

    pts = np.array([(p.x, p.y) for p in points])
    return text, pts


def rotate_by_qr(img, pts):
    """
    QR 위치 기준 자동 회전 보정
    """
    rect = cv2.minAreaRect(pts)
    angle = rect[-1]

    if angle < -45:
        angle += 90

    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h))
    return rotated


def mask_qr_area(img, pts):
    """
    QR 영역을 검정 마스크 처리하여 라인 검출 간섭 제거
    """
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, [pts.astype(np.int32)], 255)
    img[mask == 255] = (0, 0, 0)
    return img


# ============================================================
# RESULT WINDOW (AUTO ROI)
# ============================================================

def extract_result_window(img):
    """
    모든 키트 공통 결과창 ROI (비율 기반)
    """
    h, w = img.shape[:2]
    return img[int(h * 0.30):int(h * 0.70),
               int(w * 0.35):int(w * 0.65)]


# ============================================================
# LINE DETECTION (ROBUST)
# ============================================================

def find_vertical_candidates(roi):
    """
    수직 라인 후보 영역 추출
    """
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(2.5, (8, 8))
    enhanced = clahe.apply(gray)

    edges = cv2.Canny(enhanced, 40, 120)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 25))
    vertical = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = roi.shape[:2]
    candidates = []

    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        if ch > h * 0.25 and cw < w * 0.20:
            candidates.append((x, y, cw, ch))
            print(f"# candidates : {candidates}")

    return candidates


def verify_real_line(roi, bbox):
    """
    실제 라인인지 검증 (명도, 색상, 두께)
    """
    x, y, w, h = bbox
    cut = roi[y:y+h, x:x+w]

    score = 0

    if w >= 2:
        score += 1

    if np.std(cv2.cvtColor(cut, cv2.COLOR_BGR2GRAY)) > 5:
        score += 1

    hsv = cv2.cvtColor(cut, cv2.COLOR_BGR2HSV)
    color_ratio = np.sum(hsv[..., 1] > 20) / (hsv.shape[0] * hsv.shape[1])
    if color_ratio > 0.20:
        score += 1

    return score >= 2


def detect_lines(roi):
    """
    최종 라인 개수 검출
    """
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
# MAIN PIPELINE
# ============================================================

def analyze_testkit(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Image not found")

    qr_text, qr_pts = detect_qr(img)

    if qr_pts is not None:
        img = rotate_by_qr(img, qr_pts)
        img = mask_qr_area(img, qr_pts)

    roi = extract_result_window(img)
    line_cnt = detect_lines(roi)

    print(f"# Line Cnt : {line_cnt}")

    if line_cnt == 2:
        c, t = "OK", "OK"
    elif line_cnt == 1:
        c, t = "OK", "NO"
    else:
        c, t = "NO", "NO"

    return {
        "result": {
            "C": c,
            "T": t,
            "LineCnt": line_cnt
        },
        "qr": {
            "exists": qr_text is not None,
            "text": qr_text
        }
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("2 Line")
    path = "./images/kit_bench_2Line_over.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    print("#########################################")
    
    print("QR Test")
    path = "./images/kit_bench_qr_test.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    """
    print("#########################################")
    print("0 Line")
    path = "./images/kit_bench_zero.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("#########################################")
    print("1 Line")
    path = "./images/kit_bench_1line.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("#########################################")
    print("2 Line")
    path = "./images/kit_bench_2line_ok.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("#########################################")
    print("3 Line")
    path = "./images/kit_bench_3line_1_over.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("#########################################")
    print("3 Line")
    path = "./images/kit_bench_3line_2_over.jpeg"
    res = analyze_testkit(path)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    """


    

