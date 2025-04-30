from application import app, db
import os


def initialize_database():
    """Initialize the database and create necessary folders"""
    with app.app_context():
        # Create all database tables
        db.drop_all()  # First drop all existing tables
        db.create_all()  # Then create all tables fresh

        # Create uploads folder if it doesn't exist
        uploads_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
        if not os.path.exists(uploads_folder):
            os.makedirs(uploads_folder)
            print(f"Created uploads folder: {uploads_folder}")

        print("Database initialized successfully.")


if __name__ == "__main__":
    initialize_database()