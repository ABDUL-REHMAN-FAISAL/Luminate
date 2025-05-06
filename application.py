from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
app.debug = True

# PostgreSQL database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin123@localhost:5432/luminate'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-very-secure-secret-key-12345'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)


# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_employer = db.Column(db.Boolean, default=False)
    company = db.Column(db.String(100))
    title = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    location = db.Column(db.String(100))
    skills = db.Column(db.String(500))
    resume_path = db.Column(db.String(200))
    profile_image = db.Column(db.String(200))  # Added for profile image
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
    application = db.relationship('Application', backref='interviews')
    slot = db.relationship('InterviewSlot', backref='interviews')


# Helper Functions
def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = app.config['ALLOWED_EXTENSIONS']
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


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
        is_employer = 'role' in request.form and request.form.get('role') == 'employer'

        if not email or not password:
            flash('Email and password are required', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))

        if user.is_employer != is_employer:
            flash('Please select the correct account type', 'danger')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        session['is_employer'] = user.is_employer
        flash('Login successful!', 'success')

        return redirect(url_for('employer_dashboard' if user.is_employer else 'dashboard'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            is_employer = 'is_employer' in request.form and request.form.get('is_employer') == 'on'
            company = request.form.get('company_name') if is_employer else None

            if not all([name, email, password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('register'))

            user = User(
                name=name,
                email=email,
                is_employer=is_employer,
                company=company
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            session['is_employer'] = is_employer
            flash('Registration successful!', 'success')

            return redirect(url_for('employer_dashboard' if is_employer else 'dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('register'))

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

    # Get total applications across all jobs
    total_applications = 0
    for job in jobs:
        total_applications += len(job.applications)

    # Get number of scheduled interviews
    interviews_scheduled = Application.query.filter(
        Application.job.has(employer_id=employer.id),
        Application.status == 'Interview Scheduled'
    ).count()
    
    # Get scheduled interview details for employer's jobs
    scheduled_interviews = db.session.query(Interview, Application, Job, User).\
        join(Application, Interview.application_id == Application.id).\
        join(Job, Application.job_id == Job.id).\
        join(User, Application.user_id == User.id).\
        filter(Job.employer_id == employer.id).all()
    
    # Get counts for analytics section
    pending_count = Application.query.join(Job).filter(
        Job.employer_id == employer.id,
        Application.status == 'Pending'
    ).count()
    
    reviewing_count = Application.query.join(Job).filter(
        Job.employer_id == employer.id,
        Application.status == 'Reviewing'
    ).count()

    # Get recent activities
    activities = Activity.query.filter_by(user_id=employer.id).order_by(Activity.date.desc()).limit(4).all()
    
    today = datetime.utcnow()

    return render_template('employer_dashboard.html',
                           employer=employer,
                           jobs=jobs,
                           total_applications=total_applications,
                           interviews=interviews_scheduled,
                           scheduled_interviews=scheduled_interviews,
                           activities=activities,
                           today=today,
                           pending_count=pending_count,
                           reviewing_count=reviewing_count)


@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        employer = User.query.get(session['user_id'])

        job = Job(
            title=request.form.get('title'),
            company=employer.company or "Company Name",
            description=request.form.get('description'),
            required_skills=request.form.get('required_skills'),
            location=request.form.get('location', ''),
            salary=request.form.get('salary_range', ''),
            employer_id=employer.id
        )

        db.session.add(job)
        create_activity(employer.id, f"Posted new job: {job.title}")
        db.session.commit()

        flash('Job posted successfully!', 'success')
        return redirect(url_for('employer_dashboard'))

    return render_template('post_job.html')


@app.route('/view_applications/<int:job_id>')
def view_applications(job_id):
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    job = Job.query.get_or_404(job_id)

    # Ensure the employer owns this job
    if job.employer_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('employer_dashboard'))

    applications = Application.query.filter_by(job_id=job.id).all()
    return render_template('view_applications.html', job=job, applications=applications)


@app.route('/analytics')
def analytics():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    employer = User.query.get(session['user_id'])
    jobs = Job.query.filter_by(employer_id=employer.id).all()

    # Get total applications across all jobs
    total_applications = 0
    for job in jobs:
        total_applications += len(job.applications)

    return render_template('analytics.html',
                           employer=employer,
                           jobs=jobs,
                           total_applications=total_applications)


@app.route('/all_applications')
def all_applications():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    employer_id = session['user_id']
    applications = Application.query.join(Job).filter(Job.employer_id == employer_id).order_by(Application.date_applied.desc()).all()
    
    return render_template('all_applications.html', applications=applications)


@app.route('/update_application_status/<int:application_id>', methods=['POST'])
def update_application_status(application_id):
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))
    
    application = Application.query.get_or_404(application_id)
    job = Job.query.get(application.job_id)
    
    # Ensure the employer owns this job
    if job.employer_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('employer_dashboard'))
    
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Reviewing', 'Accepted', 'Rejected']:
        application.status = new_status
        db.session.commit()
        flash('Application status updated successfully', 'success')
    
    return redirect(url_for('all_applications'))


@app.route('/all_activities')
def all_activities():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))

    user_id = session['user_id']
    activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.date.desc()).all()
    
    today = datetime.utcnow()
    
    return render_template('all_activities.html', activities=activities, today=today)


# Job Seeker Routes
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login', 'danger')
        return redirect(url_for('login'))

    if session.get('is_employer'):
        return redirect(url_for('employer_dashboard'))

    user = User.query.get(session['user_id'])
    applications = Application.query.filter_by(user_id=user.id).all()

    stats = {
        'total': len(applications),
        'reviewing': len([a for a in applications if a.status == 'Reviewing']),
        'accepted': len([a for a in applications if a.status == 'Accepted']),
        'rejected': len([a for a in applications if a.status == 'Rejected']),
        'interviews_scheduled': len([a for a in applications if a.status == 'Interview Scheduled']),
        'saved_jobs': 0  # Placeholder for future feature
    }

    recent_activities = Activity.query.filter_by(user_id=user.id).order_by(Activity.date.desc()).limit(4).all()
    
    today = datetime.utcnow()

    return render_template('employee_dashboard.html',
                           user=user,
                           applications=applications,
                           stats=stats,
                           recent_activities=recent_activities,
                           today=today)


@app.route('/jobs')
def jobs():
    query = request.args.get('q', '')

    if query:
        # Simple search implementation
        search = f"%{query}%"
        jobs = Job.query.filter(
            (Job.title.ilike(search)) |
            (Job.company.ilike(search)) |
            (Job.required_skills.ilike(search))
        ).order_by(Job.date_posted.desc()).all()
    else:
        jobs = Job.query.order_by(Job.date_posted.desc()).all()

    return render_template('jobs.html', jobs=jobs)


@app.route('/job/<int:job_id>')
def job_detail(job_id):
    job = Job.query.get_or_404(job_id)
    
    # Calculate match percentage if user is logged in
    match_percentage = 0
    if 'user_id' in session and not session.get('is_employer'):
        user = User.query.get(session['user_id'])
        match_percentage = calculate_match_percentage(user.skills, job.required_skills)
    
    return render_template('job_detail.html', job=job, match_percentage=match_percentage)


@app.route('/apply/<int:job_id>', methods=['GET', 'POST'])
def apply(job_id):
    if 'user_id' not in session:
        flash('Please login to apply for jobs', 'info')
        return redirect(url_for('login'))
    
    if session.get('is_employer'):
        flash('Employer accounts cannot apply for jobs', 'warning')
        return redirect(url_for('jobs'))
    
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            
            # Check if already applied
            existing_application = Application.query.filter_by(user_id=user_id, job_id=job_id).first()
            if existing_application:
                flash('You have already applied for this job', 'info')
                return redirect(url_for('jobs'))
            
            # Resume upload
            resume_path = None
            if 'resume' in request.files:
                resume_file = request.files['resume']
                if resume_file and allowed_file(resume_file.filename):
                    filename = secure_filename(f"{user_id}_{job_id}_{resume_file.filename}")
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    resume_path = os.path.join('uploads', filename)
                    resume_file.save(os.path.join('static', resume_path))
            
            # Create application
            application = Application(
                user_id=user_id,
                job_id=job_id,
                status='Pending',
                resume_path=resume_path,
                cover_letter=request.form.get('coverLetter', '')
            )
            
            db.session.add(application)
            
            # Create activity for both user and employer
            create_activity(user_id, f"Applied for {job.title} at {job.company}")
            create_activity(job.employer_id, f"New application for {job.title}", job_id)
            
            db.session.commit()
            flash('Your application was submitted successfully!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('apply', job_id=job_id))
    
    return render_template('apply.html', job=job)


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please login', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        try:
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            user.phone = request.form.get('phone')
            user.location = request.form.get('location')
            
            if session.get('is_employer'):
                user.company = request.form.get('company')
            else:
                user.title = request.form.get('title')
                user.skills = request.form.get('skills')
            
            # Profile image upload
            if 'profile_image' in request.files:
                profile_image = request.files['profile_image']
                if profile_image and allowed_file(profile_image.filename, {'jpg', 'jpeg', 'png'}):
                    filename = secure_filename(f"profile_{user.id}_{profile_image.filename}")
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    profile_image.save(file_path)
                    user.profile_image = filename
            
            # Resume upload
            if 'resume' in request.files:
                resume = request.files['resume']
                if resume and allowed_file(resume.filename):
                    filename = secure_filename(f"resume_{user.id}_{resume.filename}")
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    resume.save(file_path)
                    user.resume_path = filename
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')
            return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)


@app.route('/manage_slots', methods=['GET', 'POST'])
def manage_slots():
    if 'user_id' not in session or not session.get('is_employer'):
        flash('Please login as employer', 'danger')
        return redirect(url_for('login'))
    
    employer_id = session['user_id']
    
    if request.method == 'POST':
        start_time = datetime.strptime(request.form.get('start_time'), '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form.get('end_time'), '%Y-%m-%dT%H:%M')
        
        if start_time >= end_time:
            flash('End time must be after start time', 'danger')
            return redirect(url_for('manage_slots'))
        
        slot = InterviewSlot(
            employer_id=employer_id,
            start_time=start_time,
            end_time=end_time
        )
        
        db.session.add(slot)
        db.session.commit()
        flash('Interview slot added successfully', 'success')
        return redirect(url_for('manage_slots'))
    
    slots = InterviewSlot.query.filter_by(employer_id=employer_id).all()
    return render_template('interview_slots.html', slots=slots)


@app.route('/schedule_interview/<int:application_id>', methods=['GET', 'POST'])
def schedule_interview(application_id):
    if 'user_id' not in session:
        flash('Please login', 'danger')
        return redirect(url_for('login'))
    
    application = Application.query.get_or_404(application_id)
    
    # Check if user is the employer who posted the job
    if session.get('is_employer'):
        job = Job.query.get(application.job_id)
        if job.employer_id != session['user__id']:
            flash('Unauthorized access', 'danger')
            return redirect(url_for('employer_dashboard'))
    # Check if user is the applicant
    elif application.user_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        slot = InterviewSlot.query.get(slot_id)
        
        if slot.is_booked:
            flash('This slot is already booked', 'danger')
            return redirect(url_for('schedule_interview', application_id=application_id))
        
        interview = Interview(
            slot_id=slot_id,
            application_id=application_id,
            meeting_link=f"https://meet.luminate.com/{slot_id}",  # Placeholder
            notes=""
        )
        
        slot.is_booked = True
        application.status = 'Interview Scheduled'
        
        db.session.add(interview)
        
        # Create activities
        create_activity(application.user_id, f"Interview scheduled for {application.job.title}")
        create_activity(application.job.employer_id, f"Interview scheduled with {application.applicant.name}", application.job_id)
        
        db.session.commit()
        flash('Interview scheduled successfully', 'success')
        
        if session.get('is_employer'):
            return redirect(url_for('view_applications', job_id=application.job_id))
        else:
            return redirect(url_for('interviews'))
    
    # Get available slots
    if session.get('is_employer'):
        slots = InterviewSlot.query.filter_by(employer_id=session['user_id'], is_booked=False).all()
    else:
        job = Job.query.get(application.job_id)
        slots = InterviewSlot.query.filter_by(employer_id=job.employer_id, is_booked=False).all()
    
    # Get existing interview if any
    interview = Interview.query.filter_by(application_id=application_id).first()
    
    return render_template('schedule_interview.html', application=application, slots=slots, interview=interview)


@app.route('/interviews')
def interviews():
    if 'user_id' not in session:
        flash('Please login', 'danger')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    from sqlalchemy.orm import joinedload
    if session.get('is_employer'):
        # For employers - interviews for their jobs
        interviews = Interview.query.join(Application).join(Job)\
            .options(joinedload(Interview.slot), joinedload(Interview.application).joinedload(Application.job))\
            .filter(Job.employer_id == user_id).all()
    else:
        # For job seekers - interviews for their applications
        interviews = Interview.query.join(Application)\
            .options(joinedload(Interview.slot), joinedload(Interview.application).joinedload(Application.job))\
            .filter(Application.user_id == user_id).all()
    
    return render_template('interviews.html', interviews=interviews, user=User.query.get(user_id))


@app.route('/results')
def results():
    if 'user_id' not in session or session.get('is_employer'):
        flash('Please login as job seeker', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    user_skills = [skill.strip().lower() for skill in user.skills.split(',')] if user.skills else []
    
    # Only recommend jobs where we have at least one matching skill
    if user_skills:
        recommended_jobs = []
        all_jobs = Job.query.all()
        
        for job in all_jobs:
            job_skills = [skill.strip().lower() for skill in job.required_skills.split(',')] if job.required_skills else []
            match_percentage = calculate_match_percentage(user.skills, job.required_skills)
            
            if match_percentage > 0:
                matching_skills = list(set(user_skills) & set(job_skills))
                missing_skills = list(set(job_skills) - set(user_skills))
                
                recommended_jobs.append({
                    'job': job,
                    'match_percentage': round(match_percentage),
                    'matching_skills': matching_skills,
                    'missing_skills': missing_skills
                })
        
        # Sort by match percentage (highest first)
        recommended_jobs.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        return render_template('results.html', matches=recommended_jobs)
    else:
        flash('Please add skills to your profile to get job recommendations', 'info')
        return redirect(url_for('profile'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)