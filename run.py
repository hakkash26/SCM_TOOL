"""
One-Click Launcher for AI-Based Medicine Reminder and Prescription Management System
Initializes database, starts background scheduler, and boots web app on http://127.0.0.1:5000
"""
import os
import sys
import webbrowser
from threading import Timer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from backend.models import DB_PATH
from backend.seed_data import seed_database
from backend.app import app, scheduler_engine

def open_browser():
    try:
        webbrowser.open_new("http://127.0.0.1:5000")
    except Exception:
        pass

def main():
    print("=" * 70)
    print(" MedRemind AI: Medicine Reminder & Prescription Management System")
    print(" Software Configuration Management - Academic Project (SCORE / VIT)")
    print("=" * 70)

    # If database file does not exist, seed it automatically
    if not os.path.exists(DB_PATH):
        print("[Setup] Database not found. Initializing and seeding...")
        seed_database()
    else:
        print("[Setup] SQLite Database verified at database/medicine_reminder.db")

    # Start the background reminder scheduler
    scheduler_engine.start()

    # Automatically open browser after 1.2 seconds
    Timer(1.2, open_browser).start()

    print("\n🚀 Server is running live at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the application.\n")

    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    main()
