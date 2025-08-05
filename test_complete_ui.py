#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pre-Testing Complete UI 테스트
Calibration과 QC Complete 화면 테스트
"""
import sys
import os
from PyQt5.QtWidgets import QApplication

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.PreTestingCompleteView import PreTestingCompleteView
from config.pretest_config import PretestConfig

def test_calibration_complete():
    """Calibration Complete 페이지 테스트"""
    app = QApplication(sys.argv)
    window = PreTestingCompleteView()
    
    # 테스트 데이터 설정
    test_data = {
        'pretest_type': PretestConfig.TYPE_CALIBRATION,
        'operator_id': 'OP12345',
        'device_id': 'CAL-001',
        'type': 1,
        'lot': 'CAL_LOT123',
        'exp_date': '2025-12-31'
    }
    window.set_data(test_data)
    window.show()
    return app.exec_()

def test_qc_complete():
    """QC Complete 페이지 테스트"""
    app = QApplication(sys.argv)
    window = PreTestingCompleteView()
    
    # 테스트 데이터 설정
    test_data = {
        'pretest_type': PretestConfig.TYPE_QC,
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
    print("Pre-Testing Complete UI 테스트")
    print("1. Calibration Complete")
    print("2. QC Complete")
    
    choice = input("테스트할 페이지를 선택하세요 (1-2): ")
    
    if choice == "1":
        test_calibration_complete()
    elif choice == "2":
        test_qc_complete()
    else:
        print("잘못된 선택입니다.")
