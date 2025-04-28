# database_updates.py
from application import db, User, Job, Application, Activity, InterviewSlot, Interview
from datetime import datetime

def update_database():
    # Add any new columns if they don't exist
    try:
        db.engine.execute('ALTER TABLE user ADD COLUMN IF NOT EXISTS is_employer BOOLEAN DEFAULT 0')
        db.engine.execute('ALTER TABLE user ADD COLUMN IF NOT EXISTS company VARCHAR(100)')
        db.engine.execute('ALTER TABLE application ADD COLUMN IF NOT EXISTS interview_date DATETIME')
    except Exception as e:
        print(f"Error adding columns: {e}")

    # Create new tables if they don't exist
    db.create_all()
    print("Database schema updated successfully!")

if __name__ == '__main__':
    update_database()