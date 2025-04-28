from app import db

# Create all database tables
db.create_all()
print("Database initialized successfully!")