"""
Database helper and model access layer.
Handles SQLite connection, queries, and transactions.
"""
import sqlite3
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'medicine_reminder.db')

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(schema_path: Optional[str] = None):
    """Initializes the database using schema.sql"""
    if not schema_path:
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')
    
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    with get_db_connection() as conn:
        conn.executescript(schema_sql)
        conn.commit()

# --- User Queries ---
def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

def get_users_by_role(role: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM users WHERE role = ?", (role,)).fetchall()
        return [dict(r) for r in rows]

def get_all_users() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM users ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]

# --- Prescription Queries ---
def create_prescription(doctor_id: int, patient_id: int, diagnosis: str, notes: str, items: List[Dict[str, Any]]) -> int:
    import json
    code = f"RX-{datetime.now().strftime('%y%m%d')}-{os.urandom(2).hex().upper()}"
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO prescriptions (prescription_code, doctor_id, patient_id, diagnosis, notes) VALUES (?, ?, ?, ?, ?)",
            (code, doctor_id, patient_id, diagnosis, notes)
        )
        rx_id = cur.lastrowid
        
        today = date.today().isoformat()
        for item in items:
            times_json = json.dumps(item.get('scheduled_times', ["09:00"]))
            cur.execute("""
                INSERT INTO prescription_items 
                (prescription_id, medicine_name, dosage, frequency, scheduled_times, timing_instruction, 
                 duration_days, total_quantity, remaining_quantity, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rx_id,
                item['medicine_name'],
                item['dosage'],
                item['frequency'],
                times_json,
                item.get('timing_instruction', 'After Food'),
                item.get('duration_days', 30),
                item.get('total_quantity', 30),
                item.get('total_quantity', 30),
                item.get('start_date', today),
                item.get('end_date', today)
            ))
            item_id = cur.lastrowid
            
            # Generate initial reminders for today and upcoming schedule
            for sched_time in item.get('scheduled_times', ["09:00"]):
                cur.execute("""
                    INSERT INTO reminders (prescription_item_id, patient_id, medicine_name, dosage, reminder_time, timing_instruction, scheduled_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                """, (item_id, patient_id, item['medicine_name'], item['dosage'], sched_time, item.get('timing_instruction', 'After Food'), today))

        conn.commit()
        return rx_id

def get_patient_prescriptions(patient_id: int) -> List[Dict[str, Any]]:
    import json
    with get_db_connection() as conn:
        rx_rows = conn.execute("""
            SELECT p.*, d.full_name as doctor_name
            FROM prescriptions p
            JOIN users d ON p.doctor_id = d.id
            WHERE p.patient_id = ?
            ORDER BY p.created_at DESC
        """, (patient_id,)).fetchall()
        
        results = []
        for rx in rx_rows:
            rx_dict = dict(rx)
            items = conn.execute("""
                SELECT * FROM prescription_items WHERE prescription_id = ?
            """, (rx['id'],)).fetchall()
            rx_dict['items'] = []
            for it in items:
                it_dict = dict(it)
                try:
                    it_dict['scheduled_times'] = json.loads(it_dict['scheduled_times'])
                except Exception:
                    it_dict['scheduled_times'] = []
                rx_dict['items'].append(it_dict)
            results.append(rx_dict)
        return results

# --- Reminder Queries ---
def get_patient_reminders(patient_id: int, target_date: Optional[str] = None) -> List[Dict[str, Any]]:
    if not target_date:
        target_date = date.today().isoformat()
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT r.*, pi.remaining_quantity
            FROM reminders r
            JOIN prescription_items pi ON r.prescription_item_id = pi.id
            WHERE r.patient_id = ? AND r.scheduled_date = ?
            ORDER BY r.reminder_time ASC
        """, (patient_id, target_date)).fetchall()
        return [dict(r) for r in rows]

def update_reminder_status(reminder_id: int, status: str, notes: str = "") -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        now_str = datetime.now().isoformat()
        conn.execute("""
            UPDATE reminders
            SET status = ?, action_timestamp = ?, notes = ?
            WHERE id = ?
        """, (status, now_str, notes, reminder_id))
        
        # If taken, decrement remaining quantity in prescription_items
        if status == 'taken':
            conn.execute("""
                UPDATE prescription_items
                SET remaining_quantity = MAX(0, remaining_quantity - 1)
                WHERE id = (SELECT prescription_item_id FROM reminders WHERE id = ?)
            """, (reminder_id,))
        
        conn.commit()
        
        row = conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        return dict(row) if row else None

# --- Refill Queries ---
def create_refill_request(patient_id: int, prescription_item_id: int, pharmacy_id: int, medicine_name: str, quantity: int) -> int:
    code = f"REF-{datetime.now().strftime('%y%m%d')}-{os.urandom(2).hex().upper()}"
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO refill_requests (request_code, patient_id, prescription_item_id, pharmacy_id, medicine_name, requested_quantity, status)
            VALUES (?, ?, ?, ?, ?, ?, 'requested')
        """, (code, patient_id, prescription_item_id, pharmacy_id, medicine_name, quantity))
        conn.commit()
        return cur.lastrowid

def get_pharmacy_refill_requests(pharmacy_id: int) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT rf.*, u.full_name as patient_name, u.phone as patient_phone, pi.dosage, pi.remaining_quantity
            FROM refill_requests rf
            JOIN users u ON rf.patient_id = u.id
            JOIN prescription_items pi ON rf.prescription_item_id = pi.id
            WHERE rf.pharmacy_id = ?
            ORDER BY rf.requested_date DESC
        """, (pharmacy_id,)).fetchall()
        return [dict(r) for r in rows]

def update_refill_status(refill_id: int, status: str, notes: str = "") -> bool:
    with get_db_connection() as conn:
        now_str = datetime.now().isoformat()
        conn.execute("""
            UPDATE refill_requests
            SET status = ?, processed_date = ?, notes = ?
            WHERE id = ?
        """, (status, now_str, notes, refill_id))
        
        # If dispensed, replenish the remaining quantity
        if status == 'dispensed':
            row = conn.execute("SELECT prescription_item_id, requested_quantity FROM refill_requests WHERE id = ?", (refill_id,)).fetchone()
            if row:
                conn.execute("""
                    UPDATE prescription_items
                    SET remaining_quantity = remaining_quantity + ?
                    WHERE id = ?
                """, (row['requested_quantity'], row['prescription_item_id']))
        
        conn.commit()
        return True

# --- Caregiver Alerts ---
def create_caregiver_alert(caregiver_id: int, patient_id: int, alert_type: str, message: str, severity: str = 'warning', reminder_id: Optional[int] = None) -> int:
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO caregiver_alerts (caregiver_id, patient_id, reminder_id, alert_type, message, severity)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (caregiver_id, patient_id, reminder_id, alert_type, message, severity))
        conn.commit()
        return cur.lastrowid

def get_caregiver_alerts(caregiver_id: int) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT ca.*, p.full_name as patient_name
            FROM caregiver_alerts ca
            JOIN users p ON ca.patient_id = p.id
            WHERE ca.caregiver_id = ?
            ORDER BY ca.created_at DESC
        """, (caregiver_id,)).fetchall()
        return [dict(r) for r in rows]
