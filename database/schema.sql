-- SQLite Schema for AI-Based Medicine Reminder and Prescription Management System
-- Matches SCM configuration baselines for entities and relationships

PRAGMA foreign_keys = ON;

-- 1. Users Table (Patients, Doctors, Caregivers, Pharmacies)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    role TEXT CHECK(role IN ('patient', 'doctor', 'caregiver', 'pharmacy')) NOT NULL,
    doctor_id INTEGER,
    caregiver_id INTEGER,
    age INTEGER,
    conditions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(doctor_id) REFERENCES users(id),
    FOREIGN KEY(caregiver_id) REFERENCES users(id)
);

-- 2. Prescriptions Table
CREATE TABLE IF NOT EXISTS prescriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_code TEXT UNIQUE NOT NULL,
    doctor_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    diagnosis TEXT NOT NULL,
    notes TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(doctor_id) REFERENCES users(id),
    FOREIGN KEY(patient_id) REFERENCES users(id)
);

-- 3. Prescription Items (Medications under a prescription)
CREATE TABLE IF NOT EXISTS prescription_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    frequency TEXT NOT NULL,              -- e.g. 'Once Daily', 'Twice Daily', 'Three Times Daily'
    scheduled_times TEXT NOT NULL,        -- JSON array e.g. ["08:00", "20:00"]
    timing_instruction TEXT NOT NULL,     -- 'After Food', 'Before Food', 'With Food'
    duration_days INTEGER NOT NULL,
    total_quantity INTEGER NOT NULL,
    remaining_quantity INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'active',         -- 'active', 'completed', 'discontinued'
    FOREIGN KEY(prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
);

-- 4. Medicine Reminders Table
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prescription_item_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    reminder_time TEXT NOT NULL,          -- Format 'HH:MM' (24-hour)
    timing_instruction TEXT NOT NULL,
    scheduled_date DATE NOT NULL,
    status TEXT CHECK(status IN ('pending', 'taken', 'snoozed', 'skipped')) DEFAULT 'pending',
    action_timestamp TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(prescription_item_id) REFERENCES prescription_items(id) ON DELETE CASCADE,
    FOREIGN KEY(patient_id) REFERENCES users(id)
);

-- 5. Refill Requests Table
CREATE TABLE IF NOT EXISTS refill_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_code TEXT UNIQUE NOT NULL,
    patient_id INTEGER NOT NULL,
    prescription_item_id INTEGER NOT NULL,
    pharmacy_id INTEGER NOT NULL,
    medicine_name TEXT NOT NULL,
    requested_quantity INTEGER NOT NULL,
    status TEXT CHECK(status IN ('requested', 'in_review', 'approved', 'dispensed', 'rejected')) DEFAULT 'requested',
    requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_date TIMESTAMP,
    notes TEXT,
    FOREIGN KEY(patient_id) REFERENCES users(id),
    FOREIGN KEY(prescription_item_id) REFERENCES prescription_items(id),
    FOREIGN KEY(pharmacy_id) REFERENCES users(id)
);

-- 6. Caregiver Alerts Table (Escalation system)
CREATE TABLE IF NOT EXISTS caregiver_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caregiver_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    reminder_id INTEGER,
    alert_type TEXT NOT NULL,             -- 'missed_dose', 'low_refill', 'drug_interaction_warning'
    message TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('info', 'warning', 'critical')) DEFAULT 'warning',
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(caregiver_id) REFERENCES users(id),
    FOREIGN KEY(patient_id) REFERENCES users(id),
    FOREIGN KEY(reminder_id) REFERENCES reminders(id)
);

-- 7. Adherence Analytics Logs Table
CREATE TABLE IF NOT EXISTS adherence_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    reminder_id INTEGER NOT NULL,
    scheduled_time TEXT NOT NULL,
    action TEXT CHECK(action IN ('taken', 'snoozed', 'skipped')) NOT NULL,
    delay_minutes INTEGER DEFAULT 0,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(patient_id) REFERENCES users(id),
    FOREIGN KEY(reminder_id) REFERENCES reminders(id)
);
