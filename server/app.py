# server/app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from the frontend

# Configure SQLite database for simplicity
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ----- MODELS -----
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user' or 'organizer'


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    price = db.Column(db.Float, default=0.0)
    organizer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    registrations = db.relationship('Registration', backref='event', lazy=True)


class Registration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attendee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    registration_type = db.Column(db.String(50))  # "general" or "VIP"


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # 'pending', 'successful', 'failed'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Create the database tables before the first request
@app.before_first_request
def create_tables():
    db.create_all()


# ----- API ENDPOINTS -----

# User Registration
@app.route('/api/users/register', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # default to "user"

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})


# User Login (for demo purposes; in a real app, use password hashing/tokens)
@app.route('/api/users/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user.id, 'username': user.username, 'role': user.role}
        })
    return jsonify({'error': 'Invalid credentials'}), 400


# Get All Events
@app.route('/api/events', methods=['GET'])
def get_events():
    events = Event.query.all()
    event_list = []
    for event in events:
        event_list.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.date.isoformat() if event.date else None,
            'location': event.location,
            'price': event.price,
            'organizer_id': event.organizer_id
        })
    return jsonify(event_list)


# Get a Specific Event by ID
@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    event_detail = {
        'id': event.id,
        'title': event.title,
        'description': event.description,
        'date': event.date.isoformat() if event.date else None,
        'location': event.location,
        'price': event.price,
        'organizer_id': event.organizer_id
    }
    return jsonify(event_detail)


# Create a New Event (restricted to organizers)
@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    date_str = data.get('date')  # expect ISO string
    location = data.get('location')
    price = data.get('price', 0.0)
    organizer_id = data.get('organizer_id')

    try:
        event_date = datetime.fromisoformat(date_str) if date_str else None
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    new_event = Event(
        title=title,
        description=description,
        date=event_date,
        location=location,
        price=price,
        organizer_id=organizer_id
    )
    db.session.add(new_event)
    db.session.commit()
    return jsonify({'message': 'Event created successfully'})


# Event Registration Endpoint
@app.route('/api/registrations', methods=['POST'])
def register_to_event():
    data = request.get_json()
    attendee_id = data.get('attendee_id')
    event_id = data.get('event_id')
    registration_type = data.get('registration_type', 'general')
    if not attendee_id or not event_id:
        return jsonify({'error': 'Missing attendee_id or event_id'}), 400

    new_reg = Registration(attendee_id=attendee_id, event_id=event_id, registration_type=registration_type)
    db.session.add(new_reg)
    db.session.commit()
    return jsonify({'message': 'Registration successful'})


# Payment Processing Endpoint (simulation)
@app.route('/api/payment', methods=['POST'])
def process_payment():
    data = request.get_json()
    user_id = data.get('user_id')
    event_id = data.get('event_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method')

    # You might also collect fields like card number details or PayPal email.
    # This demo simply simulates a successful payment.
    if not (user_id and event_id and amount and payment_method):
        return jsonify({'error': 'Missing payment details'}), 400

    # Simulate processing...
    new_payment = Payment(
        user_id=user_id,
        event_id=event_id,
        amount=amount,
        payment_method=payment_method,
        status='successful'
    )
    db.session.add(new_payment)
    db.session.commit()
    return jsonify({'message': 'Payment processed successfully', 'paymentStatus': new_payment.status})


if __name__ == '__main__':
    app.run(debug=True)
