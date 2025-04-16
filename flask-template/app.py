from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with the app
db = SQLAlchemy()
db.init_app(app)

# Initialize LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'doctor', 'staff'

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    bills = db.relationship('Bill', backref='patient', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='scheduled')  # scheduled, completed, cancelled

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, paid

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def home():
    return render_template('home.html')

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # In production, use proper password hashing
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Patient Management Routes
@app.route('/patients')
@login_required
def patients():
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

@app.route('/patient/add', methods=['POST'])
@login_required
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        address = request.form['address']
        
        new_patient = Patient(name=name, age=age, gender=gender, phone=phone, address=address)
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))

@app.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.phone = request.form['phone']
        patient.address = request.form['address']
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('patients'))
    return render_template('edit_patient.html', patient=patient)

@app.route('/patient/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    flash('Patient deleted successfully!', 'success')
    return jsonify({'success': True})

# Appointment Routes
@app.route('/appointments')
@login_required
def appointments():
    appointments = Appointment.query.all()
    doctors = Doctor.query.all()
    patients = Patient.query.all()
    return render_template('appointments.html', appointments=appointments, doctors=doctors, patients=patients)

@app.route('/appointment/add', methods=['POST'])
@login_required
def add_appointment():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        date_str = request.form['date']
        time_str = request.form['time']
        
        # Combine date and time strings
        date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        new_appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            date=date_time,
            status='scheduled'
        )
        db.session.add(new_appointment)
        db.session.commit()
        flash('Appointment scheduled successfully!', 'success')
        return redirect(url_for('appointments'))

# Billing Routes
@app.route('/billing')
@login_required
def billing():
    bills = Bill.query.all()
    patients = Patient.query.all()
    return render_template('billing.html', bills=bills, patients=patients)

@app.route('/bill/add', methods=['POST'])
@login_required
def add_bill():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        amount = request.form['amount']
        description = request.form['description']
        
        new_bill = Bill(
            patient_id=patient_id,
            amount=float(amount),
            description=description,
            date=datetime.utcnow(),
            status='pending'
        )
        db.session.add(new_bill)
        db.session.commit()
        flash('Bill added successfully!', 'success')
        return redirect(url_for('billing'))

@app.route('/bill/<int:id>/update', methods=['POST'])
@login_required
def update_bill_status(id):
    bill = Bill.query.get_or_404(id)
    bill.status = request.form['status']
    db.session.commit()
    flash('Bill status updated successfully!', 'success')
    return redirect(url_for('billing'))

# Updated dashboard route with statistics
@app.route('/dashboard')
@login_required
def dashboard():
    total_patients = Patient.query.count()
    today_appointments = Appointment.query.filter(
        db.func.date(Appointment.date) == date.today()
    ).count()
    pending_bills = Bill.query.filter_by(status='pending').count()
    
    recent_appointments = Appointment.query.order_by(Appointment.date.desc()).limit(5).all()
    recent_bills = Bill.query.order_by(Bill.date.desc()).limit(5).all()
    
    return render_template('dashboard.html',
                         total_patients=total_patients,
                         today_appointments=today_appointments,
                         pending_bills=pending_bills,
                         recent_appointments=recent_appointments,
                         recent_bills=recent_bills)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
