from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    title = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    skills = db.Column(db.String(500))
    resume_path = db.Column(db.String(200))
    applications = db.relationship('Application', backref='user', lazy=True)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    required_skills = db.Column(db.String(500), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship('Application', backref='job', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    resume_path = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)
    portfolio_url = db.Column(db.String(200))
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit_skills', methods=['POST'])
def submit_skills():
    user_skills = request.form.get('skills').split(',')
    user_skills = [skill.strip().lower() for skill in user_skills]
    
    jobs = Job.query.all()
    matches = []
    
    for job in jobs:
        required_skills = job.required_skills.lower().split(',')
        required_skills = [skill.strip() for skill in required_skills]
        
        matching_skills = set(user_skills) & set(required_skills)
        match_percentage = len(matching_skills) / len(required_skills) * 100
        
        matches.append({
            'job': job,
            'match_percentage': round(match_percentage, 2),
            'matching_skills': list(matching_skills),
            'missing_skills': list(set(required_skills) - set(user_skills))
        })
    
    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return render_template('results.html', matches=matches)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    job = Job.query.get_or_404(job_id)
    return render_template('apply.html', job=job)

@app.route('/submit_application/<int:job_id>', methods=['POST'])
def submit_application(job_id):
    if 'resume' not in request.files:
        flash('No resume file uploaded')
        return redirect(request.url)
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        application = Application(
            user_id=1,  # Replace with actual user ID from session
            job_id=job_id,
            resume_path=filename,
            cover_letter=request.form.get('coverLetter'),
            portfolio_url=request.form.get('portfolio')
        )
        
        db.session.add(application)
        db.session.commit()
        
        activity = Activity(
            user_id=1,  # Replace with actual user ID from session
            message=f'Applied for {application.job.title} at {application.job.company}'
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Application submitted successfully!')
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    # Replace with actual user ID from session
    user_id = 1
    applications = Application.query.filter_by(user_id=user_id).all()
    
    stats = {
        'total': len(applications),
        'reviewing': len([a for a in applications if a.status == 'Reviewing']),
        'accepted': len([a for a in applications if a.status == 'Accepted']),
        'rejected': len([a for a in applications if a.status == 'Rejected'])
    }
    
    recent_activities = Activity.query.filter_by(user_id=user_id)\
        .order_by(Activity.date.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         applications=applications,
                         stats=stats,
                         recent_activities=recent_activities)

@app.route('/profile')
def profile():
    # Replace with actual user ID from session
    user = User.query.get_or_404(1)
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user = User.query.get_or_404(1)  # Replace with actual user ID from session
    user.name = request.form.get('name')
    user.title = request.form.get('title')
    user.email = request.form.get('email')
    user.phone = request.form.get('phone')
    user.location = request.form.get('location')
    
    db.session.commit()
    flash('Profile updated successfully!')
    return redirect(url_for('profile'))

@app.route('/add_skill', methods=['POST'])
def add_skill():
    user = User.query.get_or_404(1)  # Replace with actual user ID from session
    new_skill = request.form.get('skill')
    
    if user.skills:
        skills = user.skills.split(',')
        if new_skill not in skills:
            skills.append(new_skill)
            user.skills = ','.join(skills)
    else:
        user.skills = new_skill
    
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/remove_skill', methods=['POST'])
def remove_skill():
    user = User.query.get_or_404(1)  # Replace with actual user ID from session
    skill_to_remove = request.json.get('skill')
    
    if user.skills:
        skills = user.skills.split(',')
        skills.remove(skill_to_remove)
        user.skills = ','.join(skills)
        db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        db.create_all()
    app.run(debug=True)