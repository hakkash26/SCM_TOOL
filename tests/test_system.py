"""
Automated Unit and Integration Test Suite (CI-09, CI-10)
Verifies database operations, AI modules, and Flask REST endpoints.
"""
import unittest
import json
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.models import get_all_users, get_patient_reminders, create_refill_request
from AI_Model.drug_interaction import check_drug_interactions
from AI_Model.adherence_predictor import predictor_instance
from backend.app import app

class TestMedicineReminderSystem(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    # 1. Database & User Tests
    def test_users_exist(self):
        users = get_all_users()
        self.assertGreaterEqual(len(users), 4, "Should have at least 4 seeded users across all roles")
        roles = {u['role'] for u in users}
        self.assertIn('patient', roles)
        self.assertIn('doctor', roles)
        self.assertIn('caregiver', roles)
        self.assertIn('pharmacy', roles)

    # 2. AI Drug Interaction Tests
    def test_ai_drug_interaction_high_risk(self):
        # Warfarin + Aspirin is a known severe interaction
        drugs = ["Warfarin 5mg", "Aspirin 81mg"]
        result = check_drug_interactions(drugs)
        self.assertFalse(result['is_safe'])
        self.assertGreaterEqual(result['interactions_count'], 1)
        self.assertIn("Severe", result['interactions'][0]['severity'])

    def test_ai_drug_interaction_safe(self):
        # Acetaminophen + Amoxicillin has no severe interaction
        drugs = ["Acetaminophen 500mg", "Amoxicillin 250mg"]
        result = check_drug_interactions(drugs)
        self.assertTrue(result['is_safe'])
        self.assertEqual(result['interactions_count'], 0)

    # 3. AI Adherence Predictor Tests
    def test_ai_adherence_predictor(self):
        result = predictor_instance.predict_adherence(age=68, num_drugs=3, doses_per_day=2, past_ratio=0.9)
        self.assertIn('adherence_probability', result)
        self.assertIn('risk_category', result)
        self.assertIn('ai_advice', result)
        self.assertGreaterEqual(result['adherence_probability'], 0.0)
        self.assertLessEqual(result['adherence_probability'], 100.0)

    # 4. REST API Endpoints Tests
    def test_health_endpoint(self):
        res = self.client.get('/api/v1/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['status'], 'healthy')

    def test_api_users(self):
        res = self.client.get('/api/v1/users')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])

    def test_api_check_interactions(self):
        res = self.client.post('/api/v1/ai/check-interactions',
            data=json.dumps({"medicines": ["Lisinopril", "Ibuprofen"]}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('Moderate', data['data']['status'])

    def test_api_reminders(self):
        res = self.client.get('/api/v1/reminders?patient_id=3')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])

if __name__ == '__main__':
    unittest.main()
