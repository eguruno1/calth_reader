import cv2
import numpy as np
import sys
import os

# --------------------------------------------------
# 공통 유틸
# --------------------------------------------------

def classify_image_type(img):
    """
    PHOTO vs ILLUSTRATION 안정 판별 (개선판)
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 1️⃣ 채도 분산 (PHOTO는 큼)
    sat = hsv[:, :, 1]
    sat_std = np.std(sat)

    # 2️⃣ 텍스처 에너지 (PHOTO는 큼)
    lap = cv2.Laplacian(gray, cv2.CV_64F)
    lap_energy = np.mean(np.abs(lap))

    # 3️⃣ 에지 비율
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = np.sum(edges > 0) / edges.size

    # ▶ 결정 규칙 (튜닝 완료값)
    if sat_std < 18 and lap_energy < 3.0 and edge_ratio < 0.12:
        return "ILLUSTRATION"
    else:
        return "PHOTO"



# --------------------------------------------------
# PHOTO (실촬영 이미지) 처리
# --------------------------------------------------

def extract_result_window(img):
    h, w, _ = img.shape
    return img[int(h*0.30):int(h*0.70),
               int(w*0.35):int(w*0.65)]


def detect_lines_photo(result_roi):
    gray = cv2.cvtColor(result_roi, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(2.0, (8, 8))
    enhanced = clahe.apply(gray)

    edges = cv2.Canny(enhanced, 50, 150)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 25))
    vertical = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    vertical_sum = np.sum(vertical > 0, axis=0)
    thresh = result_roi.shape[0] * 0.2
    peaks = np.where(vertical_sum > thresh)[0]

    if len(peaks) == 0:
        return 0

    lines = 1
    for i in range(1, len(peaks)):
        if peaks[i] - peaks[i-1] > 15:
            lines += 1

    return min(lines, 2)


# --------------------------------------------------
# ILLUSTRATION 처리 (최종 안정판)
# --------------------------------------------------

def detect_lines_illustration(img):
    """
    ILLUSTRATION 최종 결정판
    - T 위치에서 '세로 반응 패턴'만 검출
    - UI 배경 False Positive 완전 차단
    """
    h, w, _ = img.shape

    # T 위치 ROI (고정)
    t_roi = img[int(h*0.42):int(h*0.57),
                int(w*0.55):int(w*0.72)]

    gray = cv2.cvtColor(t_roi, cv2.COLOR_BGR2GRAY)

    # 대비 강화
    clahe = cv2.createCLAHE(2.0, (8, 8))
    enhanced = clahe.apply(gray)

    # 이진화 (어두운 반응만)
    _, bw = cv2.threshold(
        enhanced,
        np.mean(enhanced) - 10,
        255,
        cv2.THRESH_BINARY_INV
    )

    # 세로 투영
    vertical_sum = np.sum(bw > 0, axis=0)

    # 세로로 충분히 긴 픽셀 기둥이 있는가?
    height_thresh = t_roi.shape[0] * 0.35
    columns = np.where(vertical_sum > height_thresh)[0]

    # 연속된 column 개수
    run = 0
    max_run = 0
    for i in range(len(columns)):
        if i == 0 or columns[i] == columns[i-1] + 1:
            run += 1
        else:
            run = 1
        max_run = max(max_run, run)

    # 🔑 반응 라인은 최소 폭을 가진다
    return max_run >= 3



# --------------------------------------------------
# 메인 분석 함수
# --------------------------------------------------

def analyze_testkit(image_path):
    print(f"image_path: {image_path}")

    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(image_path)

    # 1️⃣ 무조건 PHOTO 로직 먼저
    window = extract_result_window(img)
    line_cnt_photo = detect_lines_photo(window)

    if line_cnt_photo > 0:
        # PHOTO 결과 신뢰
        if line_cnt_photo == 2:
            c, t = "OK", "OK"
        else:
            c, t = "OK", "NO"

        return {
            "image_type": "PHOTO",
            "result": {
                "C": c,
                "T": t,
                "LineCnt": line_cnt_photo
            }
        }

    # 2️⃣ PHOTO에서 0이면 → ILLUSTRATION 시도
    t_ok = detect_lines_illustration(img)

    if t_ok:
        c, t, line_cnt = "OK", "OK", 2
    else:
        c, t, line_cnt = "NO", "NO", 0

    return {
        "image_type": "ILLUSTRATION",
        "result": {
            "C": c,
            "T": t,
            "LineCnt": line_cnt
        }
    }



# --------------------------------------------------
# 실행부
# --------------------------------------------------

if __name__ == "__main__":
    """
    if len(sys.argv) < 2:
        print("Usage: python test_opencv_v3.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    """
    image_path = "./images/kit_bench_2Line_over.jpeg"
    result = analyze_testkit(image_path)
    print(result)

    """
    image_path = "./images/kit_2CT_2line.jpg"
    result = analyze_testkit(image_path)
    print(result)

    image_path = "./images/kit_0CT.jpg"
    result = analyze_testkit(image_path)
    print(result)

    image_path = "./images/kit_2CT_1T.jpg"
    result = analyze_testkit(image_path)
    print(result)

    image_path = "./images/kit_2CT_1C_3.jpg"
    result = analyze_testkit(image_path)
    print(result)

    image_path = "./images/kit_2CT_2CT_2.jpg"
    result = analyze_testkit(image_path)
    print(result)
    """


# 테스트
# print(analyze_testkit("./images/kit_2CT_2line.jpg"))
# print(analyze_testkit("./images/kit_0CT.jpg"))
# print(analyze_testkit("./images/kit_2CT_2CT_2.jpg"))
# print(analyze_testkit("./images/kit_2CT_1T.jpg"))
# print(analyze_testkit("./images/kit_2CT_1C_3.jpg"))