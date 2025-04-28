from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

from app import Job, Application, Activity, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a real secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB file size limit
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)

# ... (keep your existing models) ...

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def home():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Add authentication logic here
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/submit_skills', methods=['POST'])
def submit_skills():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_skills = [skill.strip().lower() for skill in request.form.get('skills').split(',')]
    
    jobs = Job.query.all()
    matches = []
    
    for job in jobs:
        required_skills = [skill.strip().lower() for skill in job.required_skills.split(',')]
        matching_skills = set(user_skills) & set(required_skills)
        match_percentage = len(matching_skills) / len(required_skills) * 100 if required_skills else 0
        
        matches.append({
            'job': job,
            'match_percentage': round(match_percentage, 2),
            'matching_skills': list(matching_skills),
            'missing_skills': list(set(required_skills) - set(user_skills))
        })
    
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return render_template('results.html', matches=matches)

@app.route('/submit_application/<int:job_id>', methods=['POST'])
def submit_application(job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'resume' not in request.files:
        flash('No resume file uploaded')
        return redirect(request.url)
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        application = Application(
            user_id=session['user_id'],
            job_id=job_id,
            resume_path=filename,
            cover_letter=request.form.get('coverLetter'),
            portfolio_url=request.form.get('portfolio')
        )
        
        db.session.add(application)
        db.session.commit()
        
        activity = Activity(
            user_id=session['user_id'],
            message=f'Applied for {application.job.title} at {application.job.company}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Application submitted successfully!', 'success')
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid file type. Allowed types: PDF, DOC, DOCX', 'error')
        return redirect(request.url)

# ... (update other routes to use session['user_id'] instead of hardcoded 1) ...

def create_sample_data():
    # Only run this once to create sample data
    if not User.query.first():
        user = User(
            name="John Doe",
            email="john@example.com",
            title="Software Developer",
            phone="123-456-7890",
            location="New York",
            skills="python,javascript,html,css"
        )
        db.session.add(user)
        
        jobs = [
            Job(
                title="Python Developer",
                company="Tech Corp",
                required_skills="python,django,postgresql"
            ),
            Job(
                title="Frontend Developer",
                company="Web Solutions",
                required_skills="javascript,react,html,css"
            )
        ]
        db.session.add_all(jobs)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        db.create_all()
        create_sample_data()  # Add this line to create sample data
    app.run(debug=True)