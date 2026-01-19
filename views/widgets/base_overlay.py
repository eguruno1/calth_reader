from PyQt5.QtWidgets import QWidget
from common.overlay_manager import OverlayManager

class BaseOverlayWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._opened = False

    def show_once(self):
        # OverlayManager에게 권한 요청
        if not OverlayManager.request_open(self):
            return False

        if self._opened:
            return False

        self._opened = True
        self.show()
        self.raise_()
        self.activateWindow()
        return True

    def close_overlay(self):
        if not self._opened:
            return

        self._opened = False
        OverlayManager.close(self)
        self.hide()
