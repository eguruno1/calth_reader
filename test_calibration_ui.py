#!/usr/bin/env python3
"""
Calibration UI 테스트 스크립트

각 캘리브레이션 페이지를 개별적으로 테스트할 수 있습니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from views.CalibrationInsertDeviceView import CalibrationInsertDeviceView
from views.CalibrationDeviceCheckView import CalibrationDeviceCheckView
from views.CalibrationEjectDeviceView import CalibrationEjectDeviceView
from views.CalibrationResultView import CalibrationResultView
from views.CalibrationCompleteView import CalibrationCompleteView


def test_insert_device():
    """Insert Device 페이지 테스트"""
    app = QApplication(sys.argv)
    window = CalibrationInsertDeviceView()
    window.show()
    return app.exec_()


def test_device_check():
    """Device Check 페이지 테스트"""
    app = QApplication(sys.argv)
    window = CalibrationDeviceCheckView()
    window.show()
    return app.exec_()


def test_eject_device():
    """Eject Device 페이지 테스트"""
    app = QApplication(sys.argv)
    window = CalibrationEjectDeviceView()
    window.show()
    return app.exec_()


def test_result_passed():
    """Result 페이지 테스트 (PASSED)"""
    app = QApplication(sys.argv)
    window = CalibrationResultView("PASSED")
    window.show()
    return app.exec_()


def test_result_failed():
    """Result 페이지 테스트 (FAILED)"""
    app = QApplication(sys.argv)
    window = CalibrationResultView("FAILED")
    window.show()
    return app.exec_()


def test_complete():
    """Complete 페이지 테스트"""
    app = QApplication(sys.argv)
    window = CalibrationCompleteView()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    print("Calibration UI 테스트 스크립트")
    print("=" * 50)
    print("1. Insert Device 페이지 테스트")
    print("2. Device Check 페이지 테스트")
    print("3. Eject Device 페이지 테스트")
    print("4. Result 페이지 테스트 (PASSED)")
    print("5. Result 페이지 테스트 (FAILED)")
    print("6. Complete 페이지 테스트")
    print("=" * 50)
    
    choice = input("테스트할 페이지 번호를 입력하세요 (1-6): ").strip()
    
    if choice == "1":
        sys.exit(test_insert_device())
    elif choice == "2":
        sys.exit(test_device_check())
    elif choice == "3":
        sys.exit(test_eject_device())
    elif choice == "4":
        sys.exit(test_result_passed())
    elif choice == "5":
        sys.exit(test_result_failed())
    elif choice == "6":
        sys.exit(test_complete())
    else:
        print("잘못된 선택입니다. 1-6 사이의 숫자를 입력해주세요.")
