#!/usr/bin/env python3
"""
Test script to verify refactored view files can be imported without errors
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test importing refactored view classes"""
    try:
        print("Testing AdminLoginView import...")
        from views.AdminLoginView import AdminLoginView
        print("✓ AdminLoginView imported successfully")
        
        print("Testing LoginView import...")
        from views.LoginView import LoginView
        print("✓ LoginView imported successfully")
        
        print("Testing SettingsView import...")
        from views.SettingsView import SettingsView
        print("✓ SettingsView imported successfully")
        
        print("Testing Utils import...")
        from views.Utils import (update_date_time, start_date_time_update, stop_date_time_update,
                               update_battery_status, start_battery_update, stop_battery_update)
        print("✓ Utils functions imported successfully")
        
        print("\n🎉 All refactored views pass import test!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    test_imports()
