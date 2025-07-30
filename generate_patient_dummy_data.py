#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patient Result 더미 데이터 생성 스크립트
"""
import sys
import os
import random
from datetime import datetime, timedelta

# 프로젝트 루트 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from models.database_models import PatientResultDB, get_db_manager
from repositories.result_repository import patient_result_repo

def generate_dummy_patient_results(count=20):
    """Patient Result 더미 데이터 생성"""
    
    # 검사 항목 리스트
    items = ["Influenza", "COVID-19", "RSV", "Strep A"]
    
    # 오퍼레이터 ID 리스트
    operators = ["OP001", "OP002", "OP003", "OP004", "OP005"]
    
    # 결과 데이터 템플릿
    result_templates = {
        "Influenza": [
            {"influenza_a": "Positive", "influenza_b": "Negative"},
            {"influenza_a": "Negative", "influenza_b": "Positive"},
            {"influenza_a": "Negative", "influenza_b": "Negative"},
            {"influenza_a": "Positive", "influenza_b": "Positive"},
        ],
        "COVID-19": [
            {"covid19": "Positive"},
            {"covid19": "Negative"},
            {"covid19": "Inconclusive"},
        ],
        "RSV": [
            {"rsv": "Positive"},
            {"rsv": "Negative"},
        ],
        "Strep A": [
            {"strep_a": "Positive"},
            {"strep_a": "Negative"},
        ]
    }
    
    # Lot 번호 리스트
    lot_numbers = ["LOT2024001", "LOT2024002", "LOT2024003", "LOT2024004", "LOT2024005"]
    
    # 컨트롤 타입
    controls = ["Internal Control", "External Control", None]
    
    # 더미 데이터 생성
    dummy_results = []
    
    for i in range(count):
        # 랜덤 날짜 생성 (최근 30일 내)
        days_ago = random.randint(0, 30)
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        test_date = datetime.now() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # 랜덤 검사 항목 선택
        item = random.choice(items)
        
        # 환자 ID 생성 (P + 5자리 숫자)
        patient_id = f"P{random.randint(10000, 99999):05d}"
        
        # 결과 데이터 선택
        result_data = random.choice(result_templates[item])
        
        # PatientResultDB 객체 생성
        patient_result = PatientResultDB(
            item=item,
            test_date=test_date,
            operator_id=random.choice(operators),
            patient_id=patient_id,
            result_data=result_data,
            lot_number=random.choice(lot_numbers),
            control=random.choice(controls)
        )
        
        dummy_results.append(patient_result)
    
    return dummy_results

def main():
    """메인 함수"""
    print("Patient Result 더미 데이터 생성을 시작합니다...")
    
    try:
        # 더미 데이터 생성
        dummy_results = generate_dummy_patient_results(20)
        
        # 데이터베이스에 저장
        db_manager = get_db_manager()
        session = db_manager.get_session()
        
        try:
            # 더미 데이터 추가
            for result in dummy_results:
                session.add(result)
            
            # 커밋
            session.commit()
            print(f"✅ {len(dummy_results)}개의 Patient Result 더미 데이터가 성공적으로 생성되었습니다!")
            
            # 생성된 데이터 확인
            print("\n생성된 데이터 샘플:")
            for i, result in enumerate(dummy_results[:5]):  # 처음 5개만 출력
                print(f"{i+1}. {result.item} | {result.patient_id} | {result.test_date.strftime('%Y-%m-%d %H:%M')} | {result.result_data}")
            
            if len(dummy_results) > 5:
                print(f"... 총 {len(dummy_results)}개 중 5개만 표시")
                
        except Exception as e:
            session.rollback()
            print(f"❌ 데이터베이스 저장 중 오류 발생: {e}")
            return False
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ 더미 데이터 생성 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 더미 데이터 생성이 완료되었습니다!")
        print("이제 ResultListView에서 Patient Results를 확인해보세요.")
    else:
        print("\n💥 더미 데이터 생성에 실패했습니다.")
