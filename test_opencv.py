import cv2
import numpy as np
import json
import os

def detect_line(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    thresh = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15))
    morph = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(
        morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if h > roi.shape[0] * 0.5 and w < 15:
            return True

    return False


def analyze_single_image(img):
    h, w, _ = img.shape

    # 🔹 ROI (비율 기반, 필요 시 조정)
    c_roi = img[int(h*0.25):int(h*0.75), int(w*0.20):int(w*0.40)]
    t_roi = img[int(h*0.25):int(h*0.75), int(w*0.45):int(w*0.65)]

    c_detected = detect_line(c_roi)
    t_detected = detect_line(t_roi)

    return {
        "C": "OK" if c_detected else "NO",
        "T": "OK" if t_detected else "NO",
        "LineCnt": int(c_detected) + int(t_detected)
    }


def analyze_testkit_folder(folder_path):
    results = {}

    valid_ext = (".jpg", ".jpeg", ".png")

    for file_name in os.listdir(folder_path):
        if not file_name.lower().endswith(valid_ext):
            continue

        file_path = os.path.join(folder_path, file_name)
        img = cv2.imread(file_path)

        if img is None:
            print(f"⚠️ 이미지 로드 실패: {file_name}")
            continue

        result = analyze_single_image(img)
        results[file_name] = {"result": result}

    return json.dumps(results, indent=2, ensure_ascii=False)


def analyze_testkit(image_path):
    img = cv2.imread(image_path)
    h, w, _ = img.shape

    # 🔹 ROI 비율 기반 설정 (조정 필요)
    c_roi = img[int(h*0.25):int(h*0.75), int(w*0.20):int(w*0.40)]
    t_roi = img[int(h*0.25):int(h*0.75), int(w*0.45):int(w*0.65)]

    c_detected = detect_line(c_roi)
    t_detected = detect_line(t_roi)

    line_cnt = int(c_detected) + int(t_detected)

    result = {
        "result": {
            "C": "OK" if c_detected else "NO",
            "T": "OK" if t_detected else "NO",
            "LineCnt": line_cnt
        }
    }

    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    image_folder = "./images"   # 🔹 여기만 수정하면 됨
    # print(analyze_testkit_folder(image_folder))
    # kit_2CT_2line.jpg
    print(analyze_testkit("./images/kit_2CT_2line.jpg"))
