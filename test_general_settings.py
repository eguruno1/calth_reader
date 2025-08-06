#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeneralSettingsView 단독 테스트
"""
import sys
import os

# 프로젝트 루트 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from views.GeneralSettingsView import GeneralSettingsView


def test_general_settings():
    """General Settings 페이지 테스트"""
    app = QApplication(sys.argv)
    window = GeneralSettingsView()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    test_general_settings()
