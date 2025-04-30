# application.py (main Flask application)
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import random

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False) # Renamed password to password_hash and increased length
    is_employer = db.Column(db.Boolean, default=False)
    company = db.Column(db.String(100))
    title = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    skills = db.Column(db.String(500))
    resume_path = db.Column(db.String(200))
    jobs = db.relationship('Job', backref='employer', lazy=True)
    applications = db.relationship('Application', backref='applicant', lazy=True)
    activities = db.relationship('Activity', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(100))
    salary = db.Column(db.String(50))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    applications = db.relationship('Application', backref='job', lazy=True)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    resume_path = db.Column(db.String(200))
    cover_letter = db.Column(db.Text)
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    interview_date = db.Column(db.DateTime)


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    message = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)


class InterviewSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)


class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('interview_slot.id'), nullable=False)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    status = db.Column(db.String(20), default='Scheduled')
    notes = db.Column(db.Text)
    meeting_link = db.Column(db.String(200))


# Helper Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def create_activity(user_id, message, job_id=None):
    activity = Activity(
        user_id=user_id,
        job_id=job_id,
        message=message
    )
    db.session.add(activity)
    db.session.commit()


def calculate_match_percentage(user_skills, job_skills):
    user_skill_list = [skill.strip().lower() for skill in user_skills.split(',')] if user_skills else []
    job_skill_list = [skill.strip().lower() for skill in job_skills.split(',')] if job_skills else []

    if not job_skill_list:
        return 0

    matching_skills = set(user_skill_list) & set(job_skill_list)
    return (len(matching_skills) / len(job_skill_list)) * 100


# Routes
@app.route('/')
def home():
    return render_template('landing.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password): # Use check_password method
            session['user_id'] = user.id
            session['is_employer'] = user.is_employer
            flash('Login successful!', 'success')

            if user.is_employer:
                return redirect(url_for('employer_dashboard'))
            return redirect(url_for('dashboard'))

        flash('Invalid email or password', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        is_employer = 'is_employer' in request.form

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        user = User(
            name=name,
            email=email,
            is_employer=is_employer,
            company=request.form.get('company') if is_employer else None
        )
        user.set_password(password) # Use set_password method

        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        session['is_employer'] = is_employer
        flash('Registration successful!', 'success')

        if is_employer:
            return redirect(url_for('employer_dashboard'))
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# Employer Routes
@app.route('/employer/dashboard')
def employer_dashboard():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    employer = User.query.get(session['user_id'])
    jobs = Job.query.filter_by(employer_id=employer.id).all()

    # Get recent activities
    activities = Activity.query.filter_by(user_id=employer.id).order_by(Activity.date.desc()).limit(5).all()

    # Count interviews scheduled
    interviews = Application.query.filter(
        Application.job.has(employer_id=employer.id),
        Application.status == 'Interview Scheduled'
    ).count()

    return render_template('employer_dashboard.html',
                           employer=employer,
                           jobs=jobs,
                           activities=activities,
                           interviews=interviews)


@app.route('/employer/post-job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        employer = User.query.get(session['user_id'])

        job = Job(
            title=request.form.get('title'),
            company=employer.company,
            description=request.form.get('description'),
            required_skills=request.form.get('skills'),
            location=request.form.get('location'),
            salary=request.form.get('salary'),
            employer_id=employer.id
        )

        db.session.add(job)
        db.session.commit()

        create_activity(employer.id, f"Posted new job: {job.title}")
        flash('Job posted successfully!', 'success')
        return redirect(url_for('employer_dashboard'))

    return render_template('post_job.html')


# Job Seeker Routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('is_employer'):
        flash('Please login as job seeker', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    applications = Application.query.filter_by(user_id=user.id).all()

    # Calculate stats
    stats = {
        'total': len(applications),
        'reviewing': len([a for a in applications if a.status == 'Reviewing']),
        'accepted': len([a for a in applications if a.status == 'Accepted']),
        'rejected': len([a for a in applications if a.status == 'Rejected'])
    }

    activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.date.desc()).limit(5).all()

    # Corrected template name to match existing file
    return render_template('job_search_home.html',
                           user=user,
                           applications=applications,
                           stats=stats,
                           activities=activities)


@app.route('/jobs')
def job_listings():
    jobs = Job.query.order_by(Job.date_posted.desc()).all()
    return render_template('jobs.html', jobs=jobs)


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    if 'user_id' not in session or session.get('is_employer'):
        flash('Please login as job seeker', 'danger')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No resume uploaded', 'danger')
            return redirect(request.url)

        file = request.files['resume']
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            application = Application(
                user_id=user.id,
                job_id=job.id,
                resume_path=filename,
                cover_letter=request.form.get('cover_letter')
            )

            db.session.add(application)
            db.session.commit()

            create_activity(user.id, f"Applied for {job.title} at {job.company}", job.id)
            flash('Application submitted!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid file type', 'danger')

    return render_template('apply.html', job=job)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login to view profile', 'danger')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        user.name = request.form.get('name')
        user.title = request.form.get('title')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.location = request.form.get('location')
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))

    # Convert skills string to list
    skills = user.skills.split(',') if user.skills else []
    return render_template('profile.html', user=user, skills=skills)


@app.route('/add_skill', methods=['POST'])
def add_skill():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    new_skill = request.form.get('skill')

    if new_skill:
        current_skills = user.skills.split(',') if user.skills else []
        if new_skill not in current_skills:
            current_skills.append(new_skill)
            user.skills = ','.join(current_skills)
            db.session.commit()
            flash('Skill added successfully!', 'success')

    return redirect(url_for('profile'))


@app.route('/remove_skill', methods=['POST'])
def remove_skill():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})

    user = User.query.get(session['user_id'])
    data = request.get_json()
    skill_to_remove = data.get('skill')

    if skill_to_remove and user.skills:
        current_skills = user.skills.split(',')
        if skill_to_remove in current_skills:
            current_skills.remove(skill_to_remove)
            user.skills = ','.join(current_skills)
            db.session.commit()
            return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Skill not found'})


@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        flash('Please login to upload resume', 'danger')
        return redirect(url_for('login'))

    if 'resume' not in request.files:
        flash('No file selected', 'danger')
        return redirect(url_for('profile'))

    file = request.files['resume']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('profile'))

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{session['user_id']}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        user = User.query.get(session['user_id'])
        user.resume_path = filename
        db.session.commit()

        flash('Resume uploaded successfully!', 'success')
    else:
        flash('Invalid file type. Allowed: PDF, DOC, DOCX', 'danger')

    return redirect(url_for('profile'))


@app.route('/submit_skills', methods=['POST'])
def submit_skills():
    if 'user_id' not in session:
        flash('Please login to search jobs', 'danger')
        return redirect(url_for('login'))

    user_skills = request.form.get('skills', '')
    jobs = Job.query.all()
    matches = []

    for job in jobs:
        match_percentage = calculate_match_percentage(user_skills, job.required_skills)
        user_skill_list = [skill.strip().lower() for skill in user_skills.split(',')] if user_skills else []
        job_skill_list = [skill.strip().lower() for skill in
                          job.required_skills.split(',')] if job.required_skills else []

        matching_skills = set(user_skill_list) & set(job_skill_list)
        missing_skills = set(job_skill_list) - set(user_skill_list)

        matches.append({
            'job': job,
            'match_percentage': round(match_percentage, 2),
            'matching_skills': list(matching_skills),
            'missing_skills': list(missing_skills)
        })

    matches.sort(key=lambda x: x['match_percentage'], reverse=True)
    return render_template('results.html', matches=matches)


# Initialize Database
def create_sample_data():
    with app.app_context():
        db.create_all()

        # Check if any user exists to prevent recreating sample data
        if not User.query.first():
            # Create sample employer
            employer = User(
                name="Tech Company",
                email="employer@example.com",
                is_employer=True,
                company="Tech Solutions Inc.",
                title="HR Manager"
            )
            employer.set_password("employer123") # Hash password
            db.session.add(employer)
            # db.session.flush() # Removed flush

            # Need employer ID for jobs, commit temporarily or adjust logic
            # For simplicity here, we'll commit before creating jobs that need the ID
            # A better approach might involve deferred foreign key constraints or session management
            db.session.commit() # Commit to get employer ID before creating jobs
            # Re-fetch employer if needed, or rely on the session having the ID
            employer = User.query.filter_by(email='employer@example.com').first()

            # Create sample jobs
            jobs = [
                Job(
                    title="Senior Frontend Developer",
                    company="Tech Solutions Inc.",
                    description="Looking for experienced frontend developer with React expertise.",
                    required_skills="JavaScript,React,HTML,CSS",
                    location="Remote",
                    salary="$90,000 - $120,000",
                    employer_id=employer.id
                ),
                Job(
                    title="Backend Engineer",
                    company="Tech Solutions Inc.",
                    description="Backend developer needed for API development.",
                    required_skills="Python,Django,PostgreSQL",
                    location="New York",
                    salary="$100,000 - $140,000",
                    employer_id=employer.id
                )
            ]
            db.session.add_all(jobs)
            # db.session.flush() # Removed flush

            # Create sample job seeker
            seeker = User(
                name="John Doe",
                email="seeker@example.com",
                is_employer=False,
                title="Software Developer",
                skills="Python,JavaScript,HTML,CSS",
                location="San Francisco",
                phone="555-123-4567"
            )
            seeker.set_password("seeker123") # Hash password
            db.session.add(seeker)
            # db.session.flush() # Removed flush

            # Commit again to get seeker and job IDs before creating applications/activities
            db.session.commit()
            # Re-fetch if necessary
            seeker = User.query.filter_by(email='seeker@example.com').first()
            job1 = Job.query.filter_by(title="Senior Frontend Developer", employer_id=employer.id).first()
            job2 = Job.query.filter_by(title="Backend Engineer", employer_id=employer.id).first()

            # Create sample applications
            applications = [
                Application(
                    user_id=seeker.id,
                    job_id=job1.id,
                    status="Reviewing",
                    cover_letter="I have 5 years of experience with React...",
                    date_applied=datetime.utcnow() - timedelta(days=2)
                ),
                Application(
                    user_id=seeker.id,
                    job_id=job2.id,
                    status="Pending",
                    cover_letter="I'm excited about this backend position...",
                    date_applied=datetime.utcnow() - timedelta(days=1)
                )
            ]
            db.session.add_all(applications)

            # Create sample activities
            activities = [
                Activity(
                    user_id=seeker.id,
                    job_id=job1.id,
                    message=f"Applied for {job1.title} at {job1.company}",
                    date=datetime.utcnow() - timedelta(days=2)
                ),
                Activity(
                    user_id=seeker.id,
                    job_id=job2.id,
                    message=f"Applied for {job2.title} at {job2.company}",
                    date=datetime.utcnow() - timedelta(days=1)
                ),
                Activity(
                    user_id=employer.id,
                    message="Posted new job: Senior Frontend Developer",
                    date=datetime.utcnow() - timedelta(days=3)
                )
            ]
            db.session.add_all(activities)

            db.session.commit() # Final commit for applications and activities


if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    create_sample_data()
    app.run(debug=True)