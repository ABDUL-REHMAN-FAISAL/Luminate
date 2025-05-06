import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-very-secure-secret-key-12345'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:abbi123@localhost:5432/luminate'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}