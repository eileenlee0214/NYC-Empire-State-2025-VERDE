from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'dev_secret_change_me')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ph_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# server-side API key for serial uploader
SERVER_API_KEY = os.getenv('PH_API_KEY', 'CHANGE_ME_TO_A_SECRET_KEY')

db = SQLAlchemy(app)

# ------- Models -------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Reading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    ph = db.Column(db.Float, nullable=False)

# ------- Routes -------
@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

# Register / Login (very minimal)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'warning')
        else:
            user = User(email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('Account created. Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out', 'info')
    return redirect(url_for('login'))

def login_required(fn):
    from functools import wraps
    @wraps(fn)
    def wrapped(*a, **kw):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return fn(*a, **kw)
    return wrapped

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# API endpoint for POSTing readings
@app.route('/api/data', methods=['POST'])
def api_data():
    """
    Accept JSON: { 'timestamp': 'ISO8601', 'ph': 7.12, 'api_key': '...' }
    Or allow basic auth in future.
    """
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'invalid json'}), 400

    api_key = data.get('api_key')
    if api_key != SERVER_API_KEY:
        return jsonify({'error': 'unauthorized'}), 401

    ts = data.get('timestamp')
    ph = data.get('ph')
    try:
        if ts:
            timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        else:
            timestamp = datetime.utcnow()
        ph = float(ph)
    except Exception as e:
        return jsonify({'error': 'bad payload', 'detail': str(e)}), 400

    r = Reading(timestamp=timestamp, ph=ph)
    db.session.add(r)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': r.id})

# API endpoint to get readings (for frontend Chart.js)
@app.route('/api/readings', methods=['GET'])
def api_readings():
    limit = int(request.args.get('limit', 500))
    rows = Reading.query.order_by(Reading.timestamp.asc()).limit(limit).all()
    result = [{'timestamp': r.timestamp.isoformat(), 'ph': r.ph} for r in rows]
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)