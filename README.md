# MedRemind AI: AI-Based Medicine Reminder and Prescription Management System

**Academic Project**: Software Configuration Management (SCM) – Review 1 & Review 2  
**School**: School of Computer Science Engineering and Information Systems (SCORE), VIT  
**Authors**: 
- Naveen R (23MIS0040)
- Hakkash U (23MIS0652)

---

## 📌 Project Overview
MedRemind AI is a centralized healthcare web platform connecting **Patients, Doctors, Caregivers, and Pharmacies**, powered by an AI engine to:
1. **Automate Medication Intake Tracking**: Daily reminder schedules with interactive `Take`, `Snooze`, and `Skip` dose actions.
2. **AI Drug-Drug Interaction Detection**: Real-time evaluation of concurrent medications against pharmacological conflict matrices (e.g., Warfarin + Aspirin, Lisinopril + Potassium) with clinical warnings and override safeguards.
3. **AI Predictive Adherence Score**: A Scikit-learn Machine Learning model that predicts adherence probabilities (0–100%) and categorizes risk tiers (`High Risk`, `Moderate Risk`, `Low Risk`) with tailored clinical advice.
4. **Caregiver Escalation Alerts**: Automatic escalation alerts when doses are missed by patients.
5. **Pharmacy Refill Management**: Low-stock detection and one-click patient refill requests fulfilled by pharmacies.

---

## 📂 Project Architecture

```
medicine_remainder_scm/
├── SCM_Review1_NH (1).pdf    # Review 1 SCM specification document
├── SCM_2.docx                # Review 2 SCM status accounting & audit document
├── run.py                    # Main 1-click Python launcher
├── run.bat                   # Windows batch launcher (double-click to run)
│
├── backend/
│   ├── app.py                # Flask RESTful API server (/api/v1/...) & web controller
│   ├── models.py             # SQLite database models and query access layer
│   ├── scheduler.py          # Background reminder & caregiver escalation monitor
│   └── seed_data.py          # Initial database seeder for all 4 roles & sample clinical data
│
├── AI_Model/
│   ├── drug_interaction.py   # AI Drug-drug interaction risk checker
│   └── adherence_predictor.py# Scikit-learn predictive adherence ML model
│
├── database/
│   ├── schema.sql            # Relational database schema definition
│   └── medicine_reminder.db  # SQLite database instance
│
├── static/
│   ├── css/style.css         # Modern healthcare UI styling (glassmorphism & responsive cards)
│   └── js/app.js             # Frontend logic, persona switching & Web Audio chime alerts
│
├── templates/
│   └── index.html            # Unified portal for Patient, Doctor, Caregiver, and Pharmacy
│
└── tests/
    └── test_system.py        # Automated test suite (Database, AI modules & REST APIs)
```

---

## 🚀 How to Run the Project

### Prerequisites
* Python 3.10+ (Flask, scikit-learn, numpy)

### 1-Click Execution
Simply run the following command in the terminal:
```bash
python run.py
```
*(Or double-click `run.bat` on Windows)*

The application will automatically initialize the database, start the background reminder engine, and open the web dashboard in your browser at:
**`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests
To run the automated test suite verifying all CIs and endpoints:
```bash
python -m unittest tests/test_system.py
```

---

## 📋 SCM Configuration Items Traceability Matrix (CI-01 to CI-13)

| CI ID | Configuration Item Name | Current Version | Status | Owner |
| :--- | :--- | :--- | :--- | :--- |
| **CI-01** | Project Proposal | v1.0 | Approved | Naveen R |
| **CI-02** | Software Requirement Specification (SRS) | v1.0 | Baselined | Hakkash U |
| **CI-03** | SCM Plan | v1.0 | Approved | Naveen R |
| **CI-04** | System Design Document | v1.0 | Baselined | Hakkash U |
| **CI-05** | Database Design (SQLite Schema) | v1.0 | Baselined | Naveen R |
| **CI-06** | Source Code (Backend & Frontend) | Git v1.0.0 | Release Baseline | Hakkash U |
| **CI-07** | AI Reminder & Interaction Module | v1.0 | Verified | Hakkash U |
| **CI-08** | User Interface Designs | v1.0 | Approved | Naveen R |
| **CI-09** | Test Plan | v1.0 | Baselined | Hakkash U |
| **CI-10** | Test Cases (Functional & FCA) | v1.0 | Verified | Naveen R |
| **CI-11** | User Manual | v1.0 | Completed | Hakkash U |
| **CI-12** | Deployment Guide | v1.0 | Completed | Naveen R |
| **CI-13** | Release Package | v1.0.0 | Released | Naveen R |
