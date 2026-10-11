"""
Background Medicine Reminder & Caregiver Escalation Engine (replaces Celery/Redis).
Runs as a lightweight daemon thread, evaluating scheduled doses and logging escalation alerts.
"""
import threading
import time
from datetime import datetime, date
from typing import Optional
import sqlite3

from backend.models import get_db_connection, create_caregiver_alert

class ReminderScheduler:
    def __init__(self, check_interval_seconds: int = 45):
        self.interval = check_interval_seconds
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            print(f"[Scheduler] Background reminder engine started (check interval: {self.interval}s)")

    def stop(self):
        self.running = False

    def _loop(self):
        while self.running:
            try:
                self.check_overdue_reminders()
            except Exception as e:
                print(f"[Scheduler Error] {e}")
            time.sleep(self.interval)

    def check_overdue_reminders(self):
        """
        Scans for reminders where scheduled_time has elapsed today,
        remains in 'pending' status, and hasn't yet triggered a caregiver alert.
        """
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        today_str = date.today().isoformat()

        with get_db_connection() as conn:
            # Find pending reminders whose scheduled time has passed
            query = """
                SELECT r.*, u.full_name as patient_name, u.caregiver_id
                FROM reminders r
                JOIN users u ON r.patient_id = u.id
                WHERE r.scheduled_date = ? 
                  AND r.status = 'pending' 
                  AND r.reminder_time <= ?
                  AND u.caregiver_id IS NOT NULL
            """
            rows = conn.execute(query, (today_str, current_time_str)).fetchall()

            for row in rows:
                reminder_id = row['id']
                caregiver_id = row['caregiver_id']
                patient_name = row['patient_name']
                med_name = row['medicine_name']
                sched_time = row['reminder_time']

                # Check if alert already exists for this reminder
                existing = conn.execute(
                    "SELECT id FROM caregiver_alerts WHERE reminder_id = ? AND alert_type = 'missed_dose'",
                    (reminder_id,)
                ).fetchone()

                if not existing:
                    msg = f"Escalation Alert: {patient_name} has not confirmed taking {med_name} (scheduled at {sched_time}). Please verify adherence."
                    create_caregiver_alert(
                        caregiver_id=caregiver_id,
                        patient_id=row['patient_id'],
                        alert_type="missed_dose",
                        message=msg,
                        severity="critical",
                        reminder_id=reminder_id
                    )
                    print(f"[Scheduler Alert] Missed dose alert dispatched to Caregiver #{caregiver_id} for {patient_name}")

scheduler_engine = ReminderScheduler()
