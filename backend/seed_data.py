"""
Seeds the SQLite database with realistic initial data for all 4 roles:
- Doctors
- Patients
- Caregivers
- Pharmacies
Also populates active prescriptions, reminders for today, refill requests, and initial alerts.
"""
import os
import sys
from datetime import date, datetime, timedelta

# Ensure parent directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.models import init_db, get_db_connection, create_prescription, create_refill_request, create_caregiver_alert

def seed_database():
    print("Initializing database schema...")
    init_db()

    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Clear existing data for fresh seed
        cur.execute("DELETE FROM adherence_logs")
        cur.execute("DELETE FROM caregiver_alerts")
        cur.execute("DELETE FROM refill_requests")
        cur.execute("DELETE FROM reminders")
        cur.execute("DELETE FROM prescription_items")
        cur.execute("DELETE FROM prescriptions")
        cur.execute("DELETE FROM users")
        conn.commit()

        print("Seeding Users (4 Roles)...")
        # 1. Doctor (ID: 1)
        cur.execute("""
            INSERT INTO users (id, username, full_name, email, phone, role, age, conditions)
            VALUES (1, 'dr_sarah', 'Dr. Sarah Johnson, MD', 'dr.sarah@hospital.org', '+1-555-0101', 'doctor', 42, 'Specialist: Cardiology & Internal Medicine')
        """)

        # 2. Caregiver (ID: 2)
        cur.execute("""
            INSERT INTO users (id, username, full_name, email, phone, role, age, conditions)
            VALUES (2, 'mary_davis', 'Mary Davis', 'mary.caregiver@email.com', '+1-555-0202', 'caregiver', 38, 'Caregiver for Robert Davis (Father)')
        """)

        # 3. Patient 1: Robert Davis (ID: 3) - Associated with Dr. Sarah and Caregiver Mary
        cur.execute("""
            INSERT INTO users (id, username, full_name, email, phone, role, doctor_id, caregiver_id, age, conditions)
            VALUES (3, 'robert_davis', 'Robert Davis', 'robert.davis@email.com', '+1-555-0303', 'patient', 1, 2, 68, 'Hypertension, Mild Type 2 Diabetes, High Cholesterol')
        """)

        # 4. Patient 2: Emily Chen (ID: 4) - Associated with Dr. Sarah
        cur.execute("""
            INSERT INTO users (id, username, full_name, email, phone, role, doctor_id, caregiver_id, age, conditions)
            VALUES (4, 'emily_chen', 'Emily Chen', 'emily.chen@email.com', '+1-555-0404', 'patient', 1, NULL, 45, 'Type 2 Diabetes')
        """)

        # 5. Pharmacy (ID: 5)
        cur.execute("""
            INSERT INTO users (id, username, full_name, email, phone, role, age, conditions)
            VALUES (5, 'healthplus_pharmacy', 'HealthPlus Pharmacy (Metro Branch)', 'dispensary@healthplus.org', '+1-555-0505', 'pharmacy', NULL, 'Licensed Dispensary #4829')
        """)

        conn.commit()

    print("Seeding Prescriptions for Patients...")
    today = date.today().isoformat()
    end_date_30 = (date.today() + timedelta(days=30)).isoformat()

    # Prescription 1 for Robert Davis (Senior patient)
    items_robert = [
        {
            "medicine_name": "Lisinopril",
            "dosage": "10 mg",
            "frequency": "Once Daily (Morning)",
            "scheduled_times": ["08:30"],
            "timing_instruction": "After Food",
            "duration_days": 30,
            "total_quantity": 30,
            "remaining_quantity": 8, # Low supply, triggers refill need!
            "start_date": today,
            "end_date": end_date_30
        },
        {
            "medicine_name": "Metformin",
            "dosage": "500 mg",
            "frequency": "Twice Daily",
            "scheduled_times": ["09:00", "20:00"],
            "timing_instruction": "With Food",
            "duration_days": 30,
            "total_quantity": 60,
            "remaining_quantity": 42,
            "start_date": today,
            "end_date": end_date_30
        },
        {
            "medicine_name": "Atorvastatin",
            "dosage": "20 mg",
            "frequency": "Once Daily (Night)",
            "scheduled_times": ["21:30"],
            "timing_instruction": "Before Bed",
            "duration_days": 30,
            "total_quantity": 30,
            "remaining_quantity": 25,
            "start_date": today,
            "end_date": end_date_30
        }
    ]
    rx1_id = create_prescription(
        doctor_id=1,
        patient_id=3,
        diagnosis="Essential Hypertension & Type 2 Diabetes Management",
        notes="Take Lisinopril regularly in morning with water. Maintain low-sodium diet.",
        items=items_robert
    )

    # Prescription 2 for Emily Chen
    items_emily = [
        {
            "medicine_name": "Glipizide",
            "dosage": "5 mg",
            "frequency": "Once Daily (Morning)",
            "scheduled_times": ["08:00"],
            "timing_instruction": "30 mins Before Breakfast",
            "duration_days": 30,
            "total_quantity": 30,
            "remaining_quantity": 28,
            "start_date": today,
            "end_date": end_date_30
        }
    ]
    rx2_id = create_prescription(
        doctor_id=1,
        patient_id=4,
        diagnosis="Glycemic Regulation",
        notes="Check fasting blood glucose weekly.",
        items=items_emily
    )

    print("Seeding Refill Requests for Pharmacy...")
    # Refill request from Robert for Lisinopril (since quantity is 8 left)
    with get_db_connection() as conn:
        pi_row = conn.execute("SELECT id FROM prescription_items WHERE medicine_name = 'Lisinopril' AND prescription_id = ?", (rx1_id,)).fetchone()
        if pi_row:
            create_refill_request(
                patient_id=3,
                prescription_item_id=pi_row['id'],
                pharmacy_id=5,
                medicine_name="Lisinopril 10 mg",
                quantity=30
            )

    print("Seeding Initial Caregiver Alerts...")
    create_caregiver_alert(
        caregiver_id=2,
        patient_id=3,
        alert_type="low_refill",
        message="Robert Davis has only 8 doses remaining for Lisinopril 10 mg. Refill request sent to HealthPlus Pharmacy.",
        severity="warning"
    )

    print("Seed complete! Database created at database/medicine_reminder.db")

if __name__ == "__main__":
    seed_database()
