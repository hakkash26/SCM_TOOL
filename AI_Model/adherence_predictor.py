"""
AI Medication Adherence Prediction Module (CI-07)
Uses Scikit-learn to train and predict patient adherence probability and risk score.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from typing import Dict, Any, List

class AdherencePredictor:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.is_trained = False
        self._train_synthetic_baseline()

    def _train_synthetic_baseline(self):
        """
        Trains the classifier on clinical adherence behavioral patterns:
        Features: [age, num_active_drugs, doses_per_day, past_adherence_ratio, requires_food_coordination]
        Target: 1 (High Adherence / Compliant), 0 (Low Adherence / At Risk)
        """
        np.random.seed(42)
        n_samples = 400
        
        ages = np.random.randint(20, 85, size=n_samples)
        num_drugs = np.random.randint(1, 7, size=n_samples)
        doses_per_day = np.random.randint(1, 5, size=n_samples)
        past_ratios = np.random.uniform(0.4, 1.0, size=n_samples)
        requires_food = np.random.choice([0, 1], size=n_samples)

        # Behavioral adherence heuristic for ground truth
        scores = (
            (past_ratios * 50) +
            (10 - num_drugs * 2) +
            (10 - doses_per_day * 2) +
            (np.where(ages > 65, -5, 0)) +
            (np.where(requires_food == 1, -4, 2))
        )
        labels = (scores >= 45).astype(int)

        X = np.column_stack([ages, num_drugs, doses_per_day, past_ratios, requires_food])
        y = labels
        self.model.fit(X, y)
        self.is_trained = True

    def predict_adherence(self, age: int, num_drugs: int, doses_per_day: int, past_ratio: float = 0.85, requires_food: int = 1) -> Dict[str, Any]:
        """
        Predicts adherence probability, risk category, and generates personalized recommendations.
        """
        if not self.is_trained:
            self._train_synthetic_baseline()

        sample = np.array([[age, num_drugs, doses_per_day, past_ratio, requires_food]])
        prob_compliant = float(self.model.predict_proba(sample)[0][1])
        score_percent = round(prob_compliant * 100, 1)

        if score_percent >= 80.0:
            category = "High Adherence (Low Risk)"
            badge_color = "success"
            ai_advice = "Patient demonstrates high adherence consistency. Standard reminder schedule is optimal."
        elif score_percent >= 60.0:
            category = "Moderate Adherence (Medium Risk)"
            badge_color = "warning"
            ai_advice = "Occasional dose friction likely due to midday schedule. Consider synchronizing doses with meal times."
        else:
            category = "Low Adherence (High Risk of Missed Doses)"
            badge_color = "danger"
            ai_advice = "High risk of omission! Recommend enabling Caregiver escalation alerts and audio chime reminders."

        return {
            "adherence_probability": score_percent,
            "risk_category": category,
            "badge_color": badge_color,
            "ai_advice": ai_advice,
            "features_evaluated": {
                "patient_age": age,
                "active_medications": num_drugs,
                "daily_frequency": doses_per_day,
                "past_adherence_ratio": past_ratio
            }
        }

# Global singleton instance for quick imports
predictor_instance = AdherencePredictor()

def predict_patient_adherence(age: int, num_drugs: int, doses_per_day: int, past_ratio: float = 0.85) -> Dict[str, Any]:
    return predictor_instance.predict_adherence(age, num_drugs, doses_per_day, past_ratio)

if __name__ == "__main__":
    # Test on a senior patient taking multiple drugs
    result = predictor_instance.predict_adherence(age=68, num_drugs=3, doses_per_day=3, past_ratio=0.75)
    print("Test Adherence Prediction:")
    print(f"Adherence Score: {result['adherence_probability']}%")
    print(f"Risk Category: {result['risk_category']}")
    print(f"AI Advice: {result['ai_advice']}")
