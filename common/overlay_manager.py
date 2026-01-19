class OverlayManager:
    """
    프로젝트 전체 Overlay(모달/경고/차단 UI) 단일 관리
    """

    _current_overlay = None

    @classmethod
    def request_open(cls, widget):
        # 이미 다른 Overlay가 떠 있으면 거절
        if cls._current_overlay and cls._current_overlay is not widget:
            print(
                f"[OverlayManager] "
                f"{cls._current_overlay.__class__.__name__} active → "
                f"{widget.__class__.__name__} ignored"
            )
            return False

        cls._current_overlay = widget
        print(f"[OverlayManager] OPEN {widget.__class__.__name__}")
        return True

    @classmethod
    def close(cls, widget):
        if cls._current_overlay is widget:
            print(f"[OverlayManager] CLOSE {widget.__class__.__name__}")
            cls._current_overlay = None

    @classmethod
    def is_active(cls):
        return cls._current_overlay is not None
