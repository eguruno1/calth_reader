#!/usr/bin/env python3
"""
Pre-Testing UI 테스트 스크립트

Calibration과 QC 공통 Pre-Testing 페이지를 테스트할 수 있습니다.
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from PyQt5.QtWidgets import QApplication
from views.PreTestingIntroView import PreTestingIntroView
from views.PreTestingInsertDeviceView import PreTestingInsertDeviceView
from config.pretest_config import PretestConfig


def test_calibration_intro():
    """Calibration Intro 페이지 테스트"""
    app = QApplication(sys.argv)
    window = PreTestingIntroView(pretest_type=PretestConfig.TYPE_CALIBRATION)
    window.show()
    return app.exec_()

def test_qc_intro():
    """QC Intro 페이지 테스트"""
    app = QApplication(sys.argv)
    window = PreTestingIntroView(pretest_type=PretestConfig.TYPE_QC)
    window.show()
    return app.exec_()

def test_calibration_insert():
    """Calibration Insert Device 페이지 테스트"""
    app = QApplication(sys.argv)
    window = PreTestingInsertDeviceView()
    
    # 테스트 데이터 설정
    test_data = {
        'pretest_type': PretestConfig.TYPE_CALIBRATION,
        'current_kit': 1,
        'total_kits': 4,
        'kit_names': ['음성', '저농도', '중농도', '고농도'],
        'operator_id': 'OP12345',
        'device_id': 'CAL-001',
        'type': 1,
        'lot': 'LOT123',
        'exp_date': '2025-12-31'
    }
    window.set_data(test_data)
    window.show()
    return app.exec_()

def test_qc_insert():
    """QC Insert Device 페이지 테스트"""
    app = QApplication(sys.argv)
    window = PreTestingInsertDeviceView()
    
    # 테스트 데이터 설정
    test_data = {
        'pretest_type': PretestConfig.TYPE_QC,
        'current_kit': 1,
        'total_kits': 3,
        'kit_names': ['Control 1', 'Control 2', 'Control 3'],
        'operator_id': 'OP12345',
        'device_id': 'QC-001',
        'type': 1,
        'lot': 'QC_LOT456',
        'exp_date': '2025-12-31'
    }
    window.set_data(test_data)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    print("Pre-Testing UI 테스트")
    print("1. Calibration Intro")
    print("2. QC Intro") 
    print("3. Calibration Insert Device")
    print("4. QC Insert Device")
    
    choice = input("테스트할 페이지를 선택하세요 (1-4): ")
    
    if choice == "1":
        test_calibration_intro()
    elif choice == "2":
        test_qc_intro()
    elif choice == "3":
        test_calibration_insert()
    elif choice == "4":
        test_qc_insert()
    else:
        print("잘못된 선택입니다.")
