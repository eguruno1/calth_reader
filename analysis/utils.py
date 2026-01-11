# analysis/utils.py
import cv2

def draw_result_boxes(img, boxes, metrics):
    """
    img: BGR 원본 이미지
    boxes: [(x, y, w, h)]
    metrics: metrics["lines"]
    """
    vis = img.copy()

    for box, meta in zip(boxes, metrics):
        x, y, w, h = box
        label = meta.get("label", "")
        conf = meta.get("confidence", 0)

        color = (0, 255, 0)
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)

        text = f"{label} ({conf:.2f})"
        cv2.putText(
            vis,
            text,
            (x, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1,
            cv2.LINE_AA
        )

    return vis

# analysis/utils.py (같은 파일에 추가)
def create_thumbnail(img, width=320):
    h, w = img.shape[:2]
    scale = width / float(w)
    new_size = (width, int(h * scale))
    return cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)

