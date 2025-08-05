# -*- coding: utf-8 -*-
"""
Pre-Testing 설정 파일
Calibration과 QC의 공통 설정을 관리
"""

class PretestConfig:
    """Pre-Testing 설정 클래스"""
    
    # Pre-Testing 타입 정의
    TYPE_CALIBRATION = "calibration"
    TYPE_QC = "qc"
    
    # 각 타입별 설정
    PRETEST_CONFIGS = {
        TYPE_CALIBRATION: {
            "title": "CALIBRATION",
            "form_title": "Calibration Information",
            "device_id_label": "Cal Device ID#:",
            "device_id_value": "CAL-001",
            "intro_title": "📋 Calibration Setup",
            "caution_title": "⚠️ Calibration Precautions",
            "insert_title": "📋 Insert Calibration Device",
            "insert_instruction": """Please insert the calibration device into the designated slot.

Ensure the device is properly aligned and fully inserted.
The device should click into place when correctly positioned.

Press "Next" when the device is properly inserted.""",
            "check_title": "🔍 Checking Calibration Device",
            "check_steps": [
                "Device connection check",
                "Device ID recognition", 
                "Calibration check",
                "Calibration validation"
            ],
            "eject_title": "📤 Remove Calibration Device",
            "eject_instruction": """Calibration is complete. Please remove the calibration device.

Gently pull the device out of the slot.
Store the device in a safe location for future use.

Press "Next" when the device has been removed.""",
            "result_title": "✓ CALIBRATION PASSED",
            "result_message": "Calibration completed successfully. The device is now ready for use.",
            "complete_title": "🎉 Calibration Complete!",
            "complete_message": """The calibration process has been completed successfully.

Your device is now properly calibrated and ready for accurate measurements.
All calibration data has been saved and the next calibration date has been scheduled.

Thank you for following the calibration procedure.""",
            "kit_names": ['음성', '저농도', '중농도', '고농도'],
            "total_kits": 4,
            "button_text": "Complete",
            "window_title_suffix": "Calibration"
        },
        
        TYPE_QC: {
            "title": "QC TEST",
            "form_title": "QC Test Information",
            "device_id_label": "QC Device ID#:",
            "device_id_value": "QC-001",
            "intro_title": "📋 QC Test Setup",
            "caution_title": "⚠️ QC Test Precautions",
            "insert_title": "📋 Insert QC Test Device",
            "insert_instruction": """Please insert the QC test device into the designated slot.

Ensure the device is properly aligned and fully inserted.
The device should click into place when correctly positioned.

Press "Next" when the device is properly inserted.""",
            "check_title": "🔍 Checking QC Test Device",
            "check_steps": [
                "Device connection check",
                "Device ID recognition",
                "QC test check", 
                "QC validation"
            ],
            "eject_title": "📤 Remove QC Test Device",
            "eject_instruction": """QC test is complete. Please remove the QC test device.

Gently pull the device out of the slot.
Store the device in a safe location for future use.

Press "Next" when the device has been removed.""",
            "result_title": "✓ QC TEST PASSED",
            "result_message": "QC test completed successfully. The device quality has been verified.",
            "complete_title": "🎉 QC Test Complete!",
            "complete_message": """The QC test process has been completed successfully.

Your device has passed all quality control tests and is ready for use.
All QC test data has been saved and the next QC test date has been scheduled.

Thank you for following the QC test procedure.""",
            "kit_names": ['Control 1', 'Control 2', 'Control 3'],
            "total_kits": 3,
            "button_text": "Complete QC",
            "window_title_suffix": "QC Test"
        }
    }
    
    @classmethod
    def get_config(cls, pretest_type: str) -> dict:
        """지정된 Pre-Testing 타입의 설정을 반환"""
        return cls.PRETEST_CONFIGS.get(pretest_type, cls.PRETEST_CONFIGS[cls.TYPE_CALIBRATION])
    
    @classmethod
    def get_title(cls, pretest_type: str) -> str:
        """지정된 타입의 제목을 반환"""
        return cls.get_config(pretest_type).get("title", "PRE-TESTING")
    
    @classmethod
    def get_kit_names(cls, pretest_type: str) -> list:
        """지정된 타입의 키트 이름 목록을 반환"""
        return cls.get_config(pretest_type).get("kit_names", [])
    
    @classmethod
    def get_total_kits(cls, pretest_type: str) -> int:
        """지정된 타입의 총 키트 수를 반환"""
        return cls.get_config(pretest_type).get("total_kits", 1)
