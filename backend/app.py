"""
Main Flask Application for AI-Based Medicine Reminder and Prescription Management System.
Implements RESTful API endpoints (/api/v1/...) matching SCM documentation and serves the unified web dashboard.
"""
import os
import sys
from datetime import datetime, date
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS

# Add root directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from backend.models import (
    get_all_users, get_user_by_id, get_users_by_role,
    create_prescription, get_patient_prescriptions,
    get_patient_reminders, update_reminder_status,
    create_refill_request, get_pharmacy_refill_requests, update_refill_status,
    get_caregiver_alerts, create_caregiver_alert, get_db_connection
)
from backend.scheduler import scheduler_engine
from AI_Model.drug_interaction import check_drug_interactions
from AI_Model.adherence_predictor import predict_patient_adherence

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'templates'),
    static_folder=os.path.join(BASE_DIR, 'static')
)
CORS(app)

# Active session user (default is Patient Robert Davis ID: 3)
current_session_user_id = 3

# ----------------- UI Pages -----------------
@app.route('/')
def index():
    return render_template('index.html')

# ----------------- User & Session APIs -----------------
@app.route('/api/v1/users', methods=['GET'])
def get_users():
    users = get_all_users()
    return jsonify({"success": True, "users": users})

@app.route('/api/v1/session', methods=['GET', 'POST'])
def manage_session():
    global current_session_user_id
    if request.method == 'POST':
        data = request.get_json() or {}
        new_id = data.get('user_id')
        if new_id and get_user_by_id(int(new_id)):
            current_session_user_id = int(new_id)
            return jsonify({"success": True, "active_user": get_user_by_id(current_session_user_id)})
        return jsonify({"success": False, "error": "Invalid user ID"}), 400
    
    user = get_user_by_id(current_session_user_id)
    return jsonify({"success": True, "active_user": user})

# ----------------- AI Modules APIs -----------------
@app.route('/api/v1/ai/check-interactions', methods=['POST'])
def api_check_interactions():
    data = request.get_json() or {}
    medicines = data.get('medicines', [])
    if not medicines or not isinstance(medicines, list):
        return jsonify({"success": False, "error": "Please provide a list of medicines."}), 400
    
    result = check_drug_interactions(medicines)
    return jsonify({"success": True, "data": result})

@app.route('/api/v1/ai/adherence-prediction', methods=['GET'])
def api_predict_adherence():
    patient_id = request.args.get('patient_id', type=int) or current_session_user_id
    patient = get_user_by_id(patient_id)
    if not patient or patient['role'] != 'patient':
        return jsonify({"success": False, "error": "Invalid patient"}), 400

    # Calculate statistics from database
    with get_db_connection() as conn:
        # Total active medicines
        items_cnt = conn.execute("""
            SELECT COUNT(DISTINCT pi.id) as cnt
            FROM prescription_items pi
            JOIN prescriptions p ON pi.prescription_id = p.id
            WHERE p.patient_id = ? AND p.is_active = 1
        """, (patient_id,)).fetchone()['cnt']

        # Doses scheduled per day
        reminders_cnt = conn.execute("""
            SELECT COUNT(*) as cnt
            FROM reminders
            WHERE patient_id = ? AND scheduled_date = ?
        """, (patient_id, date.today().isoformat())).fetchone()['cnt']
        doses_per_day = max(1, reminders_cnt or 2)

        # Historical adherence ratio
        total_doses = conn.execute("SELECT COUNT(*) as cnt FROM reminders WHERE patient_id = ?", (patient_id,)).fetchone()['cnt']
        taken_doses = conn.execute("SELECT COUNT(*) as cnt FROM reminders WHERE patient_id = ? AND status = 'taken'", (patient_id,)).fetchone()['cnt']
        ratio = (taken_doses / total_doses) if total_doses > 0 else 0.85

    age = patient.get('age') or 60
    prediction = predict_patient_adherence(
        age=age,
        num_drugs=max(1, items_cnt),
        doses_per_day=doses_per_day,
        past_ratio=ratio
    )
    return jsonify({"success": True, "prediction": prediction})

# ----------------- Prescription APIs -----------------
@app.route('/api/v1/prescriptions', methods=['GET', 'POST'])
def handle_prescriptions():
    if request.method == 'POST':
        data = request.get_json() or {}
        doctor_id = data.get('doctor_id', 1)
        patient_id = data.get('patient_id')
        diagnosis = data.get('diagnosis', 'Routine Consultation')
        notes = data.get('notes', '')
        items = data.get('items', [])

        if not patient_id or not items:
            return jsonify({"success": False, "error": "Missing patient or medicine items."}), 400

        # AI Drug Interaction Pre-Check
        med_names = [it.get('medicine_name') for it in items if it.get('medicine_name')]
        # Also check with patient's existing active prescriptions
        existing_rx = get_patient_prescriptions(patient_id)
        for rx in existing_rx:
            for it in rx.get('items', []):
                med_names.append(it['medicine_name'])

        interaction_check = check_drug_interactions(med_names)
        force_save = data.get('force_override', False)

        # If high risk interaction found and doctor did not explicitly override
        if not force_save and interaction_check['status'].startswith('High Risk'):
            return jsonify({
                "success": False,
                "requires_confirmation": True,
                "interaction_warning": interaction_check,
                "message": "AI Alert: High Risk Drug-Drug Interaction detected! Please review and confirm to override."
            }), 409

        rx_id = create_prescription(doctor_id, patient_id, diagnosis, notes, items)
        return jsonify({
            "success": True,
            "prescription_id": rx_id,
            "interaction_result": interaction_check,
            "message": "Prescription successfully created and reminders scheduled!"
        })

    # GET Prescriptions
    patient_id = request.args.get('patient_id', type=int) or current_session_user_id
    prescriptions = get_patient_prescriptions(patient_id)
    return jsonify({"success": True, "prescriptions": prescriptions})

# ----------------- Reminder APIs -----------------
@app.route('/api/v1/reminders', methods=['GET'])
def get_reminders():
    patient_id = request.args.get('patient_id', type=int) or current_session_user_id
    target_date = request.args.get('date', date.today().isoformat())
    reminders = get_patient_reminders(patient_id, target_date)
    return jsonify({"success": True, "reminders": reminders})

@app.route('/api/v1/reminders/<int:reminder_id>/status', methods=['POST'])
def set_reminder_status(reminder_id):
    data = request.get_json() or {}
    status = data.get('status')
    notes = data.get('notes', '')
    if status not in ['taken', 'snoozed', 'skipped']:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    updated = update_reminder_status(reminder_id, status, notes)
    if not updated:
        return jsonify({"success": False, "error": "Reminder not found"}), 404

    return jsonify({"success": True, "reminder": updated, "message": f"Dose marked as {status}!"})

# ----------------- Refill APIs -----------------
@app.route('/api/v1/refills', methods=['GET', 'POST'])
def handle_refills():
    if request.method == 'POST':
        data = request.get_json() or {}
        patient_id = data.get('patient_id') or current_session_user_id
        pi_id = data.get('prescription_item_id')
        pharmacy_id = data.get('pharmacy_id', 5)
        med_name = data.get('medicine_name', 'Medication')
        quantity = data.get('quantity', 30)

        if not pi_id:
            return jsonify({"success": False, "error": "Prescription item required"}), 400

        refill_id = create_refill_request(patient_id, pi_id, pharmacy_id, med_name, quantity)
        return jsonify({"success": True, "refill_id": refill_id, "message": "Refill request sent to pharmacy!"})

    pharmacy_id = request.args.get('pharmacy_id', type=int) or 5
    refills = get_pharmacy_refill_requests(pharmacy_id)
    return jsonify({"success": True, "refills": refills})

@app.route('/api/v1/refills/<int:refill_id>/status', methods=['POST'])
def update_refill(refill_id):
    data = request.get_json() or {}
    status = data.get('status')
    notes = data.get('notes', '')
    if status not in ['in_review', 'approved', 'dispensed', 'rejected']:
        return jsonify({"success": False, "error": "Invalid status"}), 400

    success = update_refill_status(refill_id, status, notes)
    return jsonify({"success": success, "message": f"Refill status updated to {status}!"})

# ----------------- Caregiver Alert APIs -----------------
@app.route('/api/v1/caregiver/alerts', methods=['GET'])
def get_alerts():
    caregiver_id = request.args.get('caregiver_id', type=int) or 2
    alerts = get_caregiver_alerts(caregiver_id)
    return jsonify({"success": True, "alerts": alerts})

# ----------------- Adherence Analytics API -----------------
@app.route('/api/v1/analytics', methods=['GET'])
def get_analytics():
    patient_id = request.args.get('patient_id', type=int) or current_session_user_id
    with get_db_connection() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM reminders WHERE patient_id = ?", (patient_id,)).fetchone()['c']
        taken = conn.execute("SELECT COUNT(*) as c FROM reminders WHERE patient_id = ? AND status = 'taken'", (patient_id,)).fetchone()['c']
        snoozed = conn.execute("SELECT COUNT(*) as c FROM reminders WHERE patient_id = ? AND status = 'snoozed'", (patient_id,)).fetchone()['c']
        skipped = conn.execute("SELECT COUNT(*) as c FROM reminders WHERE patient_id = ? AND status = 'skipped'", (patient_id,)).fetchone()['c']
        pending = conn.execute("SELECT COUNT(*) as c FROM reminders WHERE patient_id = ? AND status = 'pending'", (patient_id,)).fetchone()['c']

    pct = round((taken / total * 100), 1) if total > 0 else 100.0
    return jsonify({
        "success": True,
        "metrics": {
            "total_doses": total,
            "taken": taken,
            "snoozed": snoozed,
            "skipped": skipped,
            "pending": pending,
            "adherence_percentage": pct
        }
    })

# ----------------- Health Check -----------------
@app.route('/api/v1/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "AI Medicine Reminder & Prescription Management System",
        "version": "1.0.0",
        "database": "SQLite",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    scheduler_engine.start()
    print("AI Medicine Reminder System starting on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=False)
