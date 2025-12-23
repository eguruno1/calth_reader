# -*- coding: utf-8 -*-
"""
PostgreSQL ORM Integration Test (Idempotent Version)

- PostgreSQL only
- SQLite 미사용
- 중복 실행 안전
- 실제 DB 데이터 재사용
"""

import unittest

from database.connection import get_db_session, test_db_connection
from database.models import (
    Patient,
    TestType,
    User,
    TestSession,
    MeasurementResult,
)


class TestORMIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """데이터베이스 서비스 테스트"""
        print("=" * 50)
        print("🔍 데이터베이스 서비스 테스트 시작")
        print("=" * 50)

        if not test_db_connection():
            raise RuntimeError("PostgreSQL connection failed")

    def setUp(self):
        print(f"✅ 데이터베이스 서비스 로드 성공")
        self.session = get_db_session()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    # -------------------------------------------------
    # Master Data
    # -------------------------------------------------
    def test_01_create_master_data(self):
        """
        TestType / User
        (있으면 재사용, 없으면 생성)
        """
        test_type = (
            self.session.query(TestType)
            .filter_by(code="CALTH")
            .first()
        )

        if not test_type:
            test_type = TestType(
                code="CALTH",
                name="Calth Reader Test",
                description="Integration Test"
            )
            self.session.add(test_type)

        # 환자 생성 테스트
        print("\n📝 User 생성 테스트...")
        user = (
            self.session.query(User)
            .filter_by(user_id="tester01")
            .first()
        )

        if not user:
            user = User(
                user_id="tester01",
                password_hash="hashed-password",
                name="Integration Tester",
                role="operator"
            )
            self.session.add(user)

        self.session.commit()

        self.assertIsNotNone(test_type.id)
        self.assertIsNotNone(user.id)

    # -------------------------------------------------
    # Patient
    # -------------------------------------------------
    def test_02_create_patient(self):
        # 환자 생성 테스트
        print("\n📝 환자 생성 테스트...")

        patient = (
            self.session.query(Patient)
            .filter_by(patient_code="P-INT-001")
            .first()
        )

        if not patient:
            patient = Patient(
                patient_code="P-INT-001",
                birth_year=1980,
                gender="M"
            )
            self.session.add(patient)
            self.session.commit()

        self.assertIsNotNone(patient.id)

    # -------------------------------------------------
    # Test Session
    # -------------------------------------------------
    def test_03_create_test_session(self):
        # 테스트 세션 생성
        print("\n🧪 테스트 세션 생성...")

        test_type = (
            self.session.query(TestType)
            .filter_by(code="CALTH")
            .first()
        )
        user = (
            self.session.query(User)
            .filter_by(user_id="tester01")
            .first()
        )
        patient = (
            self.session.query(Patient)
            .filter_by(patient_code="P-INT-001")
            .first()
        )

        self.assertIsNotNone(test_type)
        self.assertIsNotNone(user)

        session_obj = (
            self.session.query(TestSession)
            .filter_by(
                test_type_id=test_type.id,
                operator_id=user.id,
                patient_id=patient.id if patient else None
            )
            .first()
        )

        if not session_obj:
            session_obj = TestSession(
                test_type=test_type,
                operator=user,
                patient=patient,
                device_serial="DEV-001"
            )
            self.session.add(session_obj)
            self.session.commit()

        self.assertIsNotNone(session_obj.id)
        self.assertEqual(session_obj.status, "in_progress")

    # -------------------------------------------------
    # Measurement Result
    # -------------------------------------------------
    def test_04_add_measurement_result(self):
        # MeasurementResult 스키마 테스트
        print("\n📊 MeasurementResult 스키마 테스트...")

        session_obj = (
            self.session.query(TestSession)
            .order_by(TestSession.id.desc())
            .first()
        )

        self.assertIsNotNone(session_obj)

        result = (
            self.session.query(MeasurementResult)
            .filter_by(
                session_id=session_obj.id,
                measurement_type="image_analysis"
            )
            .first()
        )

        if not result:
            result = MeasurementResult(
                session=session_obj,
                measurement_type="image_analysis",
                result_data={"mean": 0.91},
                quality_score=98.5,
                is_valid=True
            )
            self.session.add(result)
            self.session.commit()

        self.assertIsNotNone(result.id)

    # -------------------------------------------------
    # Relationship Test
    # -------------------------------------------------
    def test_05_relationships(self):
        session_obj = (
            self.session.query(TestSession)
            .order_by(TestSession.id.desc())
            .first()
        )

        self.assertIsNotNone(session_obj)
        self.assertTrue(len(session_obj.measurement_results) > 0)

if __name__ == "__main__":
    unittest.main()
