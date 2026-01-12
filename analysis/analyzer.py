# analysis/analyzer.py
from .detect_2line import detect_reaction_lines_from_image
from .detect_3line import detect_reaction_3lines_from_image

class Analyzer:

    @staticmethod
    def analyze(frame, test_type: str) -> dict:
        if "INFLUENZA" in test_type:
            mode = 3
        else:
            mode = 2

        if mode == 2:
            count, boxes, metrics = detect_reaction_lines_from_image(frame)
        else:
            count, boxes, metrics = detect_reaction_3lines_from_image(frame)

        return {
            "mode": mode,
            "line_count": count,
            "boxes": boxes,
            "metrics": metrics
        }