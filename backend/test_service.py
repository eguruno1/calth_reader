class TestService:
    def __init__(self):
        self.current_test = None
        self.test_types = {
            "Type A": {"name": "Type A", "description": "Basic test type"},
            "Type B": {"name": "Type B", "description": "Advanced test type"},
            "Type C": {"name": "Type C", "description": "Special test type"}
        }
    
    def get_test_types(self):
        """Return available test types"""
        return list(self.test_types.keys())
    
    def get_test_info(self, test_type):
        """Get information for a specific test type"""
        return self.test_types.get(test_type, None)
    
    def save_test_info(self, test_data):
        """Save test information"""
        self.current_test = test_data
        # Here you would typically save to a database
        return True
    
    def validate_test_data(self, test_data):
        """Validate test data before saving"""
        required_fields = ['patient_id', 'test_type', 'operator']
        return all(field in test_data for field in required_fields) 