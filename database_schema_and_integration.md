# PostgreSQL Database Schema, Integration, and Queries

Note: This schema is a *generic example*. Since you plan to use an OpenAI API, you must analyze the specific data structure returned by the API endpoint you intend to use and adapt this schema and the corresponding SQLAlchemy models accordingly.

 1. Example PostgreSQL Schema (DDL)

Here's a possible schema using PostgreSQL Data Definition Language (DDL). Adjust data types and constraints based on your API data.

```sql
-- Users Table (Example)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,            -- Auto-incrementing integer primary key
    username VARCHAR(80) UNIQUE NOT NULL, -- Unique username, required
    email VARCHAR(120) UNIQUE NOT NULL, -- Unique email, required
    password_hash VARCHAR(128) NOT NULL, -- Store hashed passwords, required
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('applicant', 'employer')), -- e.g., 'applicant', 'employer'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- Timestamp of creation
);

-- Jobs Table (Example)
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    employer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Foreign key to users table
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    location VARCHAR(100),
    posted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Applications Table (Example)
CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    applicant_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_path VARCHAR(255), -- Path to the uploaded resume file
    cover_letter TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'Submitted' CHECK (status IN ('Submitted', 'Viewed', 'Interviewing', 'Offered', 'Rejected', 'Withdrawn'))
);

-- Interviews Table (Example)
CREATE TABLE interviews (
    id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    interviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Can be null if interviewer leaves
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    location VARCHAR(255), -- Could be a physical address or video call link
    notes TEXT
);

-- Add other tables as needed based on API data (e.g., profiles, messages)

```

 2. Flask Integration with SQLAlchemy

Your project seems to use Flask-SQLAlchemy. Here's how to configure it for PostgreSQL:

a. Install PostgreSQL Driver:
   You need a Python library to connect to PostgreSQL. `psycopg2` is common.

   ```bash
   pip install psycopg2-binary
   # or alternatively: pip install pg8000
   ```
   Make sure to add this to your `requirements.txt`.

b. Configure Database URI:
   In your Flask app configuration (likely in `app.py` or a config file), set the `SQLALCHEMY_DATABASE_URI`:

   ```python
   # Example configuration in your Flask app setup
   import os

   # Replace with your actual database credentials and details
   db_user = os.environ.get('DB_USER', 'your_db_user')
   db_password = os.environ.get('DB_PASSWORD', 'your_db_password')
   db_host = os.environ.get('DB_HOST', 'localhost') # Or your DB host
   db_port = os.environ.get('DB_PORT', '5432')      # Default PostgreSQL port
   db_name = os.environ.get('DB_NAME', 'your_db_name')

   # PostgreSQL connection string format
   app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

   # Disable modification tracking if not needed (recommended)
   app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

   # Initialize SQLAlchemy
   # db = SQLAlchemy(app) # If initializing directly
   # Or db.init_app(app) if using the factory pattern
   ```
   *   Security: Avoid hardcoding credentials. Use environment variables or a secure configuration management system.

c. Define Models:
   Your existing SQLAlchemy models (like the `User` example found in the Flask-SQLAlchemy metadata) should work with minor or no changes, as SQLAlchemy abstracts the underlying database. Ensure the column types map appropriately (e.g., `db.String` maps to `VARCHAR`, `db.Integer` to `INTEGER`, `db.Text` to `TEXT`, `db.DateTime` to `TIMESTAMP WITH TIME ZONE`).

   ```python
   from . import db # Assuming 'db' is your SQLAlchemy instance
   from datetime import datetime

   class User(db.Model):
       __tablename__ = 'users' # Explicitly set table name
       id = db.Column(db.Integer, primary_key=True)
       username = db.Column(db.String(80), unique=True, nullable=False)
       email = db.Column(db.String(120), unique=True, nullable=False)
       password_hash = db.Column(db.String(128), nullable=False)
       user_type = db.Column(db.String(20), nullable=False)
       created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())

       # Relationships (examples)
       jobs_posted = db.relationship('Job', backref='employer', lazy=True, foreign_keys='Job.employer_id')
       applications_submitted = db.relationship('Application', backref='applicant', lazy=True, foreign_keys='Application.applicant_id')

   class Job(db.Model):
       __tablename__ = 'jobs'
       id = db.Column(db.Integer, primary_key=True)
       employer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
       title = db.Column(db.String(150), nullable=False)
       description = db.Column(db.Text, nullable=False)
       location = db.Column(db.String(100))
       posted_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
       is_active = db.Column(db.Boolean, default=True)

       applications = db.relationship('Application', backref='job', lazy=True, cascade='all, delete-orphan')

   # ... Define Application, Interview models similarly ...

   ```

d. Create Database and Tables:
   You can create the database itself using PostgreSQL tools (`createdb your_db_name`). To create the tables defined by your models, use Flask-SQLAlchemy's commands, typically within a Flask application context:

   ```python
   # In a Python script or Flask shell:
   from your_app import app, db

   with app.app_context():
       db.create_all() # Creates tables based on models
   ```
   Your `init_db.py` script might need adjustment to use `db.create_all()` within an app context.

e. Integrating with OpenAI API:
   Fetching data from an external API like OpenAI requires additional steps:

   *   Install OpenAI Library:
       ```bash
       pip install openai
       # Add 'openai' to your requirements.txt
       ```

   *   API Call Logic (Conceptual Example):
       In your Flask application (e.g., in a dedicated service module or within your routes), you'll need code to interact with the OpenAI API. 

       ```python
       import os
       from openai import OpenAI

       # --- Security Best Practice: Use Environment Variables for API Key ---
       # Ensure your OPENAI_API_KEY is set in your environment
       # client = OpenAI()
       # Or if using older versions/different auth:
       # openai.api_key = os.getenv("OPENAI_API_KEY") 

       def fetch_data_from_openai(prompt_text):
           """Conceptual function to fetch data from OpenAI."""
           try:
               # This is a placeholder - replace with the actual OpenAI client usage 
               # based on the specific endpoint and parameters you need.
               # Example using the newer OpenAI client (v1.x+):
               client = OpenAI() # Assumes OPENAI_API_KEY is set in env
               response = client.chat.completions.create(
                   model="gpt-3.5-turbo", # Or your desired model
                   messages=[{"role": "user", "content": prompt_text}]
                   # Add other parameters as needed (temperature, max_tokens, etc.)
               )
               # Process the response - the structure depends on the API endpoint used
               # Example: accessing chat completion content
               if response.choices:
                   api_data = response.choices[0].message.content 
                   # You'll likely need to parse this data further (e.g., if it's JSON)
                   return api_data 
               else:
                   print("OpenAI API call succeeded but returned no choices.")
                   return None
           except Exception as e:
               print(f"Error calling OpenAI API: {e}")
               # Handle errors appropriately (logging, user feedback)
               return None

       def process_and_store_data(api_data):
           """Parses API data and stores it using SQLAlchemy models."""
           if not api_data:
               return

           # 1. Parse the api_data: The structure depends entirely on what the 
           #    OpenAI API returns for your specific request. It might be text, JSON, etc.
           #    You might need json.loads() or custom parsing logic.
           parsed_data = api_data # Placeholder - Replace with actual parsing

           # 2. Map to SQLAlchemy Models: Create instances of your models 
           #    (User, Job, etc.) and populate them with the parsed_data.
           #    Example (highly dependent on your models and parsed_data structure):
           # with app.app_context(): # Ensure you're in an app context
           #    new_entry = YourModel(field1=parsed_data.get('key1'), ...)
           #    db.session.add(new_entry)
           #    try:
           #        db.session.commit()
           #    except Exception as e:
           #        db.session.rollback()
           #        print(f"Database error: {e}")

           print("Data processing and storage logic needs implementation based on API response.")

       # --- Example Usage ---
       # prompt = "Generate a job description for a Python developer."
       # data = fetch_data_from_openai(prompt)
       # process_and_store_data(data)
       ```

   *   Data Mapping: Carefully map the fields from the OpenAI API response to the columns in your database tables (defined by your SQLAlchemy models).
   *   Error Handling: Implement robust error handling for API calls (network issues, API errors) and database operations.
   *   Asynchronous Operations: For potentially long-running API calls, consider using asynchronous tasks (e.g., with Celery) to avoid blocking your web server.

 3. Data Integrity

PostgreSQL and SQLAlchemy help maintain data integrity:

*   Primary Keys (`PRIMARY KEY` / `db.Column(primary_key=True)`): Uniquely identify each row in a table.
*   Foreign Keys (`REFERENCES` / `db.ForeignKey`): Ensure relationships between tables are valid. `ON DELETE CASCADE` automatically deletes related rows (e.g., delete a user, delete their jobs), while `ON DELETE SET NULL` sets the foreign key to null (use cautiously).
*   Unique Constraints (`UNIQUE` / `unique=True`): Prevent duplicate values in a column (e.g., usernames, emails).
*   Not Null Constraints (`NOT NULL` / `nullable=False`): Ensure a column must have a value.
*   Check Constraints (`CHECK` / `db.CheckConstraint`): Enforce specific conditions on data (e.g., `user_type` must be one of the allowed values).
*   Transactions (SQLAlchemy Sessions): SQLAlchemy manages sessions, which typically wrap operations in transactions. `db.session.commit()` saves changes, `db.session.rollback()` discards them, ensuring atomicity.

 4. Example SQL Queries

While SQLAlchemy provides an ORM to interact with the database using Python objects, here are the equivalent raw SQL queries for common operations:

```sql
-- Create (INSERT)
A new user:
INSERT INTO users (username, email, password_hash, user_type)
VALUES ('new_applicant', 'applicant@email.com', 'hashed_password_value', 'applicant');

A new job posting:
INSERT INTO jobs (employer_id, title, description, location)
VALUES (1, 'Software Engineer', 'Develop amazing software.', 'Remote'); -- Assuming user with id=1 is the employer

-- Read (SELECT)
Get a user by username:
SELECT id, username, email, user_type, created_at FROM users WHERE username = 'new_applicant';

Get all active jobs posted by a specific employer (id=1):
SELECT id, title, description, location, posted_at
FROM jobs
WHERE employer_id = 1 AND is_active = TRUE;

Get all applications for a specific job (id=5):
SELECT a.id, a.applied_at, a.status, u.username AS applicant_username
FROM applications a
JOIN users u ON a.applicant_id = u.id
WHERE a.job_id = 5;

-- Update (UPDATE)
Change an application status:
UPDATE applications SET status = 'Viewed' WHERE id = 10;

Deactivate a job posting:
UPDATE jobs SET is_active = FALSE WHERE id = 5;

-- Delete (DELETE)
Remove an application:
DELETE FROM applications WHERE id = 10;

Remove a job (will also remove related applications due to ON DELETE CASCADE):
DELETE FROM jobs WHERE id = 5;

```

Remember to use parameterized queries (which SQLAlchemy handles automatically) when executing raw SQL from your application to prevent SQL injection vulnerabilities.

 Conclusion

This guide provides a starting point for integrating PostgreSQL with your Flask app, especially when using an external API like OpenAI:

1.  Analyze the OpenAI API Response: Determine the exact structure and data types of the information returned by the specific OpenAI endpoint(s) you will use.
2.  Refine Schema & Models: Update the PostgreSQL schema (DDL) and SQLAlchemy models (`User`, `Job`, etc.) in this document and your code to accurately match the OpenAI data fields.
3.  Implement API Interaction: Write Python code using the `openai` library to call the API, handle authentication (API keys via environment variables), and parse the response.
4.  Develop Data Storage Logic: Create the application logic to take the parsed API data and use your SQLAlchemy models (`db.session.add()`, `db.session.commit()`) to store or update it in your PostgreSQL database.
5.  Ensure Robustness: Implement comprehensive error handling for both API calls and database transactions, and consider asynchronous processing for long API requests.