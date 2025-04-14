# Luminate - Job Matching Platform

## Overview
Luminate is a modern job matching platform that connects job seekers with relevant opportunities based on their skills and qualifications. The platform uses an intelligent matching algorithm to recommend jobs that align with users' skill sets, helping them find positions where they're most likely to succeed.

## Key Features

### Smart Job Matching
- Skills-based matching algorithm that compares user skills with job requirements
- Percentage match calculation to prioritize the most relevant opportunities
- Identification of matching and missing skills to help users understand their fit

### User Profiles
- Comprehensive profile management for job seekers
- Skill tracking and management
- Resume upload and storage
- Professional information management (title, contact details, location)

### Application Management
- Streamlined job application process
- Application tracking dashboard
- Status monitoring (Pending, Reviewing, Accepted, Rejected)
- Activity history and notifications

### Employer Features
- Job posting capabilities
- Candidate review interface
- Application status management

## Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask session management

### Frontend
- **UI Framework**: Bootstrap 5
- **Styling**: Custom CSS with Space Grotesk font family
- **Icons**: Bootstrap Icons

### Data Models
- User (profile information, skills)
- Job (job listings with required skills)
- Application (job applications with status tracking)
- Activity (user activity logging)

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```
   python app.py
   ```
4. Access the application at http://127.0.0.1:5000/

## Usage

1. **Create a profile**: Add your professional information and skills
2. **Search for jobs**: Enter your skills to find matching opportunities
3. **Apply to jobs**: Submit applications with your resume and cover letter
4. **Track applications**: Monitor the status of your applications in the dashboard
5. **Improve your profile**: Add skills based on job requirements to increase match percentages

## Project Structure

- `app.py`: Main application file with routes and business logic
- `templates/`: HTML templates for the web interface
- `uploads/`: Storage for user-uploaded files (resumes)
- `jobs.db`: SQLite database file

## Future Enhancements

- Enhanced authentication system
- Advanced skill matching algorithms
- Employer dashboard
- Interview scheduling
- Messaging system between employers and candidates
