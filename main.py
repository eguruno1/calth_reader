# -*- coding: utf-8 -*-
#
# Created by: BenchSoft.co.
#

import sys
from PyQt5.QtWidgets import QApplication
from views.Utils import set_app_font

if __name__ == "__main__":
    app = QApplication(sys.argv)
    set_app_font()
    from controllers.ui_controller import AppController
    controller = AppController()
    controller.show()
    sys.exit(app.exec_())
