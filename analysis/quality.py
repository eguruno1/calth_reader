# analysis/quality.py
# Python 3.6.9 compatible

from __future__ import division

def clamp(value, min_value=0.0, max_value=1.0):
    return max(min_value, min(value, max_value))


def normalize(value, min_v, max_v):
    """
    value를 0~1 범위로 정규화
    """
    if value is None:
        return 0.0
    if max_v - min_v == 0:
        return 0.0
    return clamp((value - min_v) / (max_v - min_v))


def calculate_quality_score(
    metrics,
    line_count,
    expected_lines,
):
    """
    quality_score 계산 (0~100)

    metrics 예시:
    {
        "focus": 241.4,
        "projection_mean": 30535.0,
        "lines": [
            {"confidence": 1.0},
            {"confidence": 0.92}
        ]
    }
    """

    # -----------------------------
    # 1. Focus Score 정규화
    # -----------------------------
    # 실측 기반 경험값
    focus_raw = metrics.get("focus", 0.0)

    # 보통 30 ~ 400 사이에서 분포
    focus_norm = normalize(
        focus_raw,
        min_v=30.0,
        max_v=400.0
    )

    # -----------------------------
    # 2. Line Count 점수
    # -----------------------------
    if expected_lines <= 0:
        line_count_score = 0.0
    else:
        diff = abs(line_count - expected_lines)
        line_count_score = clamp(1.0 - (diff / float(expected_lines)))

    # -----------------------------
    # 3. Line Confidence 평균
    # -----------------------------
    confidences = []
    for line in metrics.get("lines", []):
        c = line.get("confidence")
        if c is not None:
            confidences.append(clamp(float(c)))

    if confidences:
        confidence_score = sum(confidences) / float(len(confidences))
    else:
        confidence_score = 0.0

    # -----------------------------
    # 4. Projection / Edge Strength
    # -----------------------------
    proj = metrics.get("projection_mean") or metrics.get("edge_strength") or 0.0

    # 경험적 범위 (환경 따라 튜닝 가능)
    projection_norm = normalize(
        proj,
        min_v=5000.0,
        max_v=35000.0
    )

    # -----------------------------
    # 5. 가중치 적용
    # -----------------------------
    quality_0_1 = (
        focus_norm * 0.30 +
        line_count_score * 0.20 +
        confidence_score * 0.30 +
        projection_norm * 0.20
    )

    # -----------------------------
    # 6. 0~100 변환
    # -----------------------------
    quality_score = round(clamp(quality_0_1) * 100.0, 2)

    return quality_score
