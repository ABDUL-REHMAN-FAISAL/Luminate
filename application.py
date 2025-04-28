from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a real secret key
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB file size limit
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/job_search')
def job_search_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('job_search_home.html')

@app.route('/')
def home():
    # Check if user is logged in
    if 'user_id' not in session:
        return render_template('landing.html')
    
    # Redirect based on role
    role = session.get('role')
    if role == 'employee':
        # Redirect employee to their main dashboard
        return redirect(url_for('dashboard')) 
    elif role == 'employer':
        return redirect(url_for('employer_dashboard'))
    else:
        # Default or error case, maybe redirect to login
        flash('User role not found. Please login again.', 'warning')
        return redirect(url_for('logout'))

@app.route('/dashboard') # Renamed from /applications
def dashboard(): # Renamed from applications
    app.logger.info("Accessed /dashboard route")
    if 'user_id' not in session:
        app.logger.warning("User ID not found in session, redirecting to login")
        return redirect(url_for('login'))
    user_id = session['user_id']
    app.logger.info(f"User ID from session: {user_id}")
    user = User.query.get_or_404(user_id)
    
    # Get user applications
    applications = Application.query.filter_by(user_id=user_id).all()
    
    # Calculate application statistics
    stats = {
        'total': len(applications),
        'reviewing': len([a for a in applications if a.status == 'Reviewing']),
        'accepted': len([a for a in applications if a.status == 'Accepted']),
        'rejected': len([a for a in applications if a.status == 'Rejected'])
    }
    
    # Get recent activities
    recent_activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.date.desc()).limit(5).all()
    
    # Parse user skills and add ratings and market demand
    user_skills = []
    if user and user.skills:
        skill_list = [skill.strip() for skill in user.skills.split(',')]
        
        # Sample market demand data (in a real app, this would come from a database or API)
        market_demand = {
            'python': 'High',
            'javascript': 'High',
            'react': 'High',
            'django': 'Medium',
            'html': 'Medium',
            'css': 'Medium',
            'postgresql': 'Medium',
            'flask': 'Medium'
        }
        
        # Generate skill ratings (in a real app, these would be stored in the database)
        for skill in skill_list:
            # Generate a sample rating between 6 and 9
            import random
            rating = random.randint(6, 9)
            
            user_skills.append({
                'name': skill,
                'rating': rating,
                'demand': market_demand.get(skill.lower(), 'Low')
            })
    
    # Calculate market standing statistics
    market_stats = {
        'profile_completeness': 85,  # Sample value
        'job_match_rate': 72  # Sample value
    }
    
    return render_template('employee_dashboard.html', 
                           applications=applications, 
                           stats=stats, 
                           recent_activities=recent_activities,
                           user_skills=user_skills,
                           market_stats=market_stats)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # Get the specific job
    job = Job.query.get_or_404(job_id)
    return render_template('apply.html', job=job)

@app.route('/profile')
def profile():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user data from database
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email') # Changed from username to email
        password = request.form.get('password')
        role = request.form.get('role', 'employee')
        # Check for default credentials
        if email == 'abdulrehman@gmail.com' and password == 'kamli':
            session['user_id'] = 1 # Replace with actual user ID
            session['role'] = role # Store role in session
            flash('Login successful!', 'success')
            # Redirect based on role
            if role == 'employer':
                return redirect(url_for('employer_dashboard'))
            else:
                return redirect(url_for('dashboard')) # Redirect employee to the main employee dashboard
        flash('Invalid username or password.', 'danger')
        return redirect(url_for('login'))
    # If GET request or failed POST, render login page
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None) # Clear role on logout
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')  # In a real app, hash this password
        is_employer = 'is_employer' in request.form
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        # Determine role based on checkbox
        role = 'employer' if is_employer else 'employee'

        # Create new user (removed non-existent fields)
        new_user = User(
            name=name,
            email=email,
            password=password # In a real app, HASH this password!
            # Removed is_employer, company_name, company_description as they are not in the model
        )
        
        # Placeholder for handling employer-specific data if needed later
        # if is_employer:
        #     company_name = request.form.get('company_name')
        #     company_description = request.form.get('company_description')
        #     # Add logic to store company details, perhaps in a separate EmployerProfile model
        
        db.session.add(new_user)
        db.session.commit()
        
        # Log in the new user
        session['user_id'] = new_user.id
        session['role'] = 'employer' if is_employer else 'employee' # Set role based on registration
        
        flash('Registration successful!', 'success')
        # Redirect based on role
        if is_employer:
            return redirect(url_for('employer_dashboard'))
        else:
            return redirect(url_for('dashboard')) # Redirect employee to the main employee dashboard
    
    return render_template('register.html')

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    new_skill = request.form.get('skill')
    
    if new_skill:
        # Get current skills as a list
        current_skills = user.skills.split(',') if user.skills else []
        # Add new skill if not already present
        if new_skill not in current_skills:
            current_skills.append(new_skill)
            user.skills = ','.join(current_skills)
            db.session.commit()
            flash('Skill added successfully!')
    
    return redirect(url_for('profile'))

@app.route('/remove_skill', methods=['POST'])
def remove_skill():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    skill_to_remove = data.get('skill')
    
    if skill_to_remove and user.skills:
        current_skills = user.skills.split(',')
        if skill_to_remove in current_skills:
            current_skills.remove(skill_to_remove)
            user.skills = ','.join(current_skills)
            db.session.commit()
    
    return jsonify({'success': True})

@app.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'resume' not in request.files:
        flash('No file part')
        return redirect(url_for('profile'))
    
    file = request.files['resume']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        user_id = session['user_id']
        user = User.query.get_or_404(user_id)
        user.resume_path = filename
        db.session.commit()
        
        flash('Resume uploaded successfully!')
    else:
        flash('Invalid file type. Allowed types: PDF, DOC, DOCX')
    
    return redirect(url_for('profile'))

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
        flash('Please login to apply for jobs', 'warning')
        return redirect(url_for('login'))
    
    # Get the job details
    job = Job.query.get_or_404(job_id)
    
    if 'resume' not in request.files:
        flash('No resume file uploaded', 'danger')
        return redirect('/jobs')
    
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
        return redirect(url_for('employer_dashboard'))
    else:
        flash('Invalid file type. Allowed types: PDF, DOC, DOCX', 'error')
        return redirect(request.url)



@app.route('/interviews') # Employee interviews page
def interviews():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    user = User.query.get_or_404(user_id)
    try:
        # user_interviews = Interview.query.filter_by(user_id=user_id).all()
        user_interviews = [] # Using empty list as placeholder
    except Exception as e:
        app.logger.error(f"Error fetching interviews for user {user_id}: {e}")
        flash('Could not load interviews.', 'error')
        user_interviews = [] # Pass empty list on error
    return render_template('interviews.html', interviews=user_interviews, user=user)

@app.route('/jobs') # Employee jobs page (placeholder)
def jobs():
     if 'user_id' not in session or session.get('role') != 'employee':
        return redirect(url_for('login'))
     # Fetch all available job listings
     # Assuming a Job model exists
     try:
        # Placeholder: Replace with actual Job model query if available
        # all_jobs = Job.query.all()
        all_jobs = [] # Using empty list as placeholder
     except Exception as e:
        app.logger.error(f"Error fetching jobs: {e}")
        flash('Could not load job listings.', 'error')
        all_jobs = [] # Pass empty list on error
     return render_template('jobs.html', jobs=all_jobs) # Assuming jobs.html exists

@app.route('/employer_dashboard') # Employer dashboard page
def employer_dashboard():
    if 'user_id' not in session or session.get('role') != 'employer':
        return redirect(url_for('login'))
    employer_id = session['user_id']
    # Fetch data relevant to the employer, e.g., jobs posted by them
    # Assuming a Job model exists with an employer_id relationship
    try:
        # Placeholder: Replace with actual Job model query if available
        # posted_jobs = Job.query.filter_by(employer_id=employer_id).all()
        posted_jobs = [] # Using empty list as placeholder
        # You might want to fetch applications for those jobs too
        # applications = Application.query.filter(Application.job_id.in_([job.id for job in posted_jobs])).all()
    except Exception as e:
        app.logger.error(f"Error fetching employer dashboard data for employer {employer_id}: {e}")
        flash('Could not load dashboard data.', 'error')
        posted_jobs = []
        # applications = []
    # Pass necessary data to the template
    return render_template('employer_dashboard.html', posted_jobs=posted_jobs)

@app.route('/landing')
def landing():
    return render_template('landing.html')

@app.route('/post_job', methods=['GET', 'POST'])
def post_job():
    if 'user_id' not in session or session.get('role') != 'employer':
        flash('Access denied. Please login as an employer.', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # Logic to handle job posting form submission
        title = request.form.get('title')
        company = request.form.get('company') # Or get from employer profile
        required_skills = request.form.get('required_skills')
        # Add more fields as needed (description, location, etc.)
        
        if not title or not company or not required_skills:
            flash('Please fill out all required fields.', 'warning')
            return render_template('post_job.html')
            
        new_job = Job(
            title=title,
            company=company, 
            required_skills=required_skills
            # Add employer_id if your Job model supports it
        )
        db.session.add(new_job)
        db.session.commit()
        
        flash(f'Job "{title}" posted successfully!', 'success')
        return redirect(url_for('employer_dashboard'))
        
    # If GET request, render the form
    return render_template('post_job.html')

@app.route('/view_application/<int:application_id>')
def view_application(application_id):
    if 'user_id' not in session:
        flash('Please login to view applications.', 'warning')
        return redirect(url_for('login'))

    application = Application.query.get_or_404(application_id)
    
    # Ensure the logged-in user owns this application or is an employer viewing it
    # (Add employer logic later if needed)
    if application.user_id != session['user_id'] and session.get('role') != 'employer':
         flash('You do not have permission to view this application.', 'danger')
         # Redirect employee to their dashboard, employer to theirs
         if session.get('role') == 'employee':
             return redirect(url_for('applications'))
         else:
             return redirect(url_for('employer_dashboard')) 

    # Pass application and related job/user data to the template
    return render_template('view_application.html', application=application)

def create_sample_data():
    # Only run this once to create sample data
    if not User.query.filter_by(email='abdulrehman@gmail.com').first():
        # Create the user expected by the hardcoded login
        login_user = User(
            id=1, # Explicitly set ID to 1 for the hardcoded login
            name="Abdul Rehman",
            email="abdulrehman@gmail.com",
            password="kamli", # Use the password expected by login (NOTE: Store hashed passwords in real apps!)
            title="Default User",
            phone="",
            location="",
            skills="",
            resume_path=None
        )
        db.session.add(login_user)

    # Add other sample data if needed and if no users exist at all
    if not User.query.filter(User.id != 1).first() and not User.query.get(1): # Check if ONLY user 1 exists or no users exist
        # Add the original sample user if no other users exist
        other_user = User(
            name="John Doe",
            email="john@example.com",
            password="testpassword",
            title="Software Developer",
            phone="123-456-7890",
            location="New York",
            skills="python,javascript,html,css",
            resume_path=None
        )
        db.session.add(other_user)
        
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

# Add more routes and logic as needed

if __name__ == '__main__':
    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Note: db.create_all() and sample data creation moved inside app_context
    with app.app_context():
        db.create_all()
        create_sample_data()
    app.run(debug=True) # Added debug=True for development