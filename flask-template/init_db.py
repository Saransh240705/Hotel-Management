from app import app, db, User, Doctor

def init_database():
    with app.app_context():
        # Create tables
        db.create_all()

        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123', role='admin')
            db.session.add(admin)

        # Add sample doctors if they don't exist
        sample_doctors = [
            {'name': 'Dr. John Smith', 'specialization': 'General Medicine'},
            {'name': 'Dr. Sarah Johnson', 'specialization': 'Pediatrics'},
            {'name': 'Dr. Michael Brown', 'specialization': 'Cardiology'},
            {'name': 'Dr. Emily Davis', 'specialization': 'Orthopedics'}
        ]

        for doctor_data in sample_doctors:
            if not Doctor.query.filter_by(name=doctor_data['name']).first():
                doctor = Doctor(**doctor_data)
                db.session.add(doctor)

        # Commit the changes
        db.session.commit()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_database()