# -*- coding: utf-8 -*-
#
# Created by: BenchSoft.co.
#

import sys
import os
from PyQt5.QtWidgets import QApplication
from views.Utils import set_app_font

# ✅ 프로젝트 루트를 Python 경로에 추가 (핵심 수정)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_app_font()
    from controllers.ui_controller import AppController
    controller = AppController()
    controller.show()
    sys.exit(app.exec_())

