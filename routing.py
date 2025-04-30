from flask import Flask, render_template, redirect, url_for, request, session

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for session handling

# ---- PUBLIC ROUTES ----
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Dummy login (replace with real auth later)
        role = request.form.get('role')  # 'employer' or 'employee'
        session['user_role'] = role
        return redirect(url_for(f'{role}_dashboard'))
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

# ---- EMPLOYEE ROUTES ----
@app.route('/employee/dashboard')
def employee_dashboard():
    return render_template('employee_dashboard.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/jobs')
def jobs():
    return render_template('jobs.html')

@app.route('/job/<int:job_id>')
def job_info(job_id):
    return render_template('job_info.html', job_id=job_id)

@app.route('/apply/<int:job_id>')
def apply(job_id):
    return render_template('apply.html', job_id=job_id)

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/interviews')
def interviews():
    return render_template('interviews.html')

@app.route('/interview/slots')
def interview_slots():
    return render_template('interview_slots.html')

# ---- EMPLOYER ROUTES ----
@app.route('/employer/dashboard')
def employer_dashboard():
    return render_template('employer_dashboard.html')

@app.route('/post_job')
def post_job():
    return render_template('post_job.html')

@app.route('/view_applications')
def view_applications():
    return render_template('view_applications.html')

@app.route('/schedule_interview/<int:application_id>')
def schedule_interview(application_id):
    return render_template('schedule_interview.html', application_id=application_id)

# ---- LOGOUT ----
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

# ---- RUN ----
if __name__ == '__main__':
    app.run(debug=True)
