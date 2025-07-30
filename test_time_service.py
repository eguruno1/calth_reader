#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 import 테스트 스크립트
"""

try:
    print("TimeService 임포트 테스트...")
    from services.time_service import TimeService
    print("✓ TimeService 임포트 성공")
    
    print("TimeService 인스턴스 생성 테스트...")
    time_service = TimeService()
    print("✓ TimeService 인스턴스 생성 성공")
    
    print("현재 시간 모드 조회 테스트...")
    mode = time_service.get_time_mode()
    print(f"✓ 현재 시간 모드: {mode}")
    
    print("현재 표시 시간 조회 테스트...")
    current_time = time_service.get_current_display_time()
    print(f"✓ 현재 표시 시간: {current_time}")
    
    print("\nUtils.py 임포트 테스트...")
    from views.Utils import get_time_service, update_date_time
    print("✓ Utils.py 함수들 임포트 성공")
    
    print("get_time_service() 테스트...")
    global_time_service = get_time_service()
    print("✓ 글로벌 TimeService 인스턴스 생성 성공")
    
    print("\n=== 모든 테스트 통과! ===")
    
except ImportError as e:
    print(f"✗ Import 오류: {e}")
except Exception as e:
    print(f"✗ 일반 오류: {e}")
