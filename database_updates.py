from application import db, User, Job, Application
from datetime import datetime

# Run this script to update the database schema with new models and fields

# Add employer-specific fields to User model
db.engine.execute('ALTER TABLE user ADD COLUMN is_employer BOOLEAN DEFAULT 0')
db.engine.execute('ALTER TABLE user ADD COLUMN company_name VARCHAR(100)')
db.engine.execute('ALTER TABLE user ADD COLUMN company_description TEXT')

# Create InterviewSlot model
class InterviewSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

# Create Interview model
class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('interview_slot.id'))
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'))
    status = db.Column(db.String(20), default='Scheduled')  # Scheduled, Completed, Cancelled
    notes = db.Column(db.Text)
    meeting_link = db.Column(db.String(200))

# Create SkillEndorsement model
class SkillEndorsement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    skill = db.Column(db.String(100), nullable=False)
    endorser_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    endorser_name = db.Column(db.String(100))
    endorser_email = db.Column(db.String(120))
    endorser_title = db.Column(db.String(100))
    date_endorsed = db.Column(db.DateTime, default=datetime.utcnow)
    verified = db.Column(db.Boolean, default=False)

# Create the new tables
db.create_all()

print("Database schema updated successfully!")