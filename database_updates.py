from application import db, User, Job, Application, Activity, InterviewSlot, Interview
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random


def add_sample_data():
    """Add sample data to the database for testing purposes"""
    print("Adding sample data to the database...")

    # Clear existing data
    db.session.query(Interview).delete()
    db.session.query(InterviewSlot).delete()
    db.session.query(Activity).delete()
    db.session.query(Application).delete()
    db.session.query(Job).delete()
    db.session.query(User).delete()
    db.session.commit()

    # Create employer accounts
    employer1 = User(
        name="TechCorp Inc.",
        email="employer@techcorp.com",
        is_employer=True,
        company="TechCorp Inc.",
        phone="555-123-4567",
        location="San Francisco, CA"
    )
    employer1.set_password("password123")

    employer2 = User(
        name="Creative Solutions",
        email="employer@creativesolutions.com",
        is_employer=True,
        company="Creative Solutions",
        phone="555-987-6543",
        location="New York, NY"
    )
    employer2.set_password("password123")

    db.session.add_all([employer1, employer2])
    db.session.commit()

    # Create job seeker accounts
    seeker1 = User(
        name="John Smith",
        email="john@example.com",
        is_employer=False,
        title="Senior Software Engineer",
        phone="555-111-2222",
        location="San Francisco, CA",
        skills="Python, JavaScript, React, SQL, AWS"
    )
    seeker1.set_password("password123")

    seeker2 = User(
        name="Sarah Johnson",
        email="sarah@example.com",
        is_employer=False,
        title="UX/UI Designer",
        phone="555-333-4444",
        location="Remote",
        skills="UI Design, Figma, Sketch, User Research, Prototyping"
    )
    seeker2.set_password("password123")

    db.session.add_all([seeker1, seeker2])
    db.session.commit()

    # Create job listings
    job1 = Job(
        title="Senior Full Stack Developer",
        company="TechCorp Inc.",
        description="""
        We're looking for a talented Full Stack Developer to join our team.

        Responsibilities:
        - Design and develop web applications using modern technologies
        - Work with product and design teams to implement new features
        - Optimize applications for performance and scalability
        - Write clean, testable code with appropriate documentation

        Requirements:
        - 5+ years of experience in full stack development
        - Proficiency in Python, JavaScript, and React
        - Experience with SQL databases and AWS
        - Strong problem-solving skills and attention to detail
        """,
        required_skills="Python, JavaScript, React, SQL, AWS",
        location="San Francisco, CA",
        salary="$120,000 - $150,000",
        employer_id=employer1.id
    )

    job2 = Job(
        title="UX/UI Designer",
        company="Creative Solutions",
        description="""
        Join our creative team as a UX/UI Designer and help shape the future of our products.

        Responsibilities:
        - Create user-centered designs for web and mobile applications
        - Conduct user research and usability testing
        - Develop wireframes, prototypes, and visual designs
        - Collaborate with developers to implement designs

        Requirements:
        - 3+ years of experience in UX/UI design
        - Proficiency in design tools such as Figma and Sketch
        - Strong portfolio showcasing your design process
        - Experience with user research and prototyping
        """,
        required_skills="UI Design, Figma, Sketch, User Research, Prototyping",
        location="Remote",
        salary="$90,000 - $110,000",
        employer_id=employer2.id
    )

    job3 = Job(
        title="Data Scientist",
        company="TechCorp Inc.",
        description="""
        We are seeking a skilled Data Scientist to help us extract insights from our data.

        Responsibilities:
        - Analyze large datasets to identify trends and patterns
        - Develop machine learning models and algorithms
        - Create visualizations and reports to communicate findings
        - Collaborate with cross-functional teams to implement data-driven solutions

        Requirements:
        - Master's or PhD in a quantitative field
        - Experience with Python, R, and SQL
        - Knowledge of machine learning and statistical analysis
        - Strong communication and problem-solving skills
        """,
        required_skills="Python, R, SQL, Machine Learning, Statistics",
        location="San Francisco, CA",
        salary="$130,000 - $160,000",
        employer_id=employer1.id
    )

    db.session.add_all([job1, job2, job3])
    db.session.commit()

    # Create applications
    application1 = Application(
        user_id=seeker1.id,
        job_id=job1.id,
        status="Reviewing",
        cover_letter="I am excited to apply for the Senior Full Stack Developer position at TechCorp Inc. With 7 years of experience in full stack development, I believe I would be a great fit for your team.",
        date_applied=datetime.utcnow() - timedelta(days=5)
    )

    application2 = Application(
        user_id=seeker2.id,
        job_id=job2.id,
        status="Interview Scheduled",
        cover_letter="As a UX/UI Designer with 5 years of experience, I am thrilled to apply for the position at Creative Solutions. I am passionate about creating user-centered designs and would love to contribute to your team.",
        date_applied=datetime.utcnow() - timedelta(days=10),
        interview_date=datetime.utcnow() + timedelta(days=2)
    )

    db.session.add_all([application1, application2])
    db.session.commit()

    # Create interview slots
    for i in range(5):
        slot = InterviewSlot(
            employer_id=employer1.id,
            start_time=datetime.utcnow() + timedelta(days=i + 1, hours=10),
            end_time=datetime.utcnow() + timedelta(days=i + 1, hours=11),
            is_booked=False
        )
        db.session.add(slot)

    for i in range(5):
        slot = InterviewSlot(
            employer_id=employer2.id,
            start_time=datetime.utcnow() + timedelta(days=i + 1, hours=14),
            end_time=datetime.utcnow() + timedelta(days=i + 1, hours=15),
            is_booked=(i == 1)  # Make one slot booked
        )
        db.session.add(slot)

    db.session.commit()

    # Create an interview
    booked_slot = InterviewSlot.query.filter_by(employer_id=employer2.id, is_booked=True).first()
    if booked_slot:
        interview = Interview(
            slot_id=booked_slot.id,
            application_id=application2.id,
            status="Scheduled",
            meeting_link="https://zoom.us/j/123456789",
            notes="Candidate has a strong portfolio. Focus on team collaboration experience."
        )
        db.session.add(interview)

    # Create activities
    activities = [
        Activity(user_id=employer1.id, job_id=job1.id, message="Posted new job: Senior Full Stack Developer",
                 date=datetime.utcnow() - timedelta(days=7)),
        Activity(user_id=employer2.id, job_id=job2.id, message="Posted new job: UX/UI Designer",
                 date=datetime.utcnow() - timedelta(days=14)),
        Activity(user_id=employer1.id, job_id=job3.id, message="Posted new job: Data Scientist",
                 date=datetime.utcnow() - timedelta(days=3)),
        Activity(user_id=seeker1.id, job_id=job1.id, message="Applied for Senior Full Stack Developer at TechCorp Inc.",
                 date=datetime.utcnow() - timedelta(days=5)),
        Activity(user_id=seeker2.id, job_id=job2.id, message="Applied for UX/UI Designer at Creative Solutions",
                 date=datetime.utcnow() - timedelta(days=10)),
        Activity(user_id=employer1.id, job_id=job1.id, message="Application from John Smith is now being reviewed",
                 date=datetime.utcnow() - timedelta(days=3)),
        Activity(user_id=employer2.id, job_id=job2.id, message="Scheduled interview with Sarah Johnson",
                 date=datetime.utcnow() - timedelta(days=5)),
        Activity(user_id=seeker2.id, job_id=job2.id, message="Interview scheduled for UX/UI Designer position",
                 date=datetime.utcnow() - timedelta(days=5))
    ]
    db.session.add_all(activities)
    db.session.commit()

    print("Sample data added successfully.")


if __name__ == "__main__":
    # Create database tables if they don't exist
    db.create_all()

    # Add sample data
    add_sample_data()