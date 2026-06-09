from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skillswap_secret_key_123'

# Connect to Render's live PostgreSQL database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///skillswap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Real-time WebSocket configuration
socketio = SocketIO(app, cors_allowed_origins="*")

# 1. Structural Database Model
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skill_offer = db.Column(db.String(100), nullable=False)
    skill_seek = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)

# Generate the cloud database table layout
with app.app_context():
    db.create_all()

# 2. Main Dashboard Page Route
@app.route('/')
def index():
    search_query = request.args.get('search', '')
    
    if search_query:
        # Search filter querying the cloud database directly
        profiles = UserProfile.query.filter(
            (UserProfile.name.ilike(f'%{search_query}%')) |
            (UserProfile.skill_offer.ilike(f'%{search_query}%')) |
            (UserProfile.skill_seek.ilike(f'%{search_query}%'))
        ).all()
    else:
        # Pull every profile saved in the cloud database
        profiles = UserProfile.query.all()
        
    return render_template('index.html', title="Skill Swap Platform", profiles=profiles, search_query=search_query)

# 3. Permanent Registration Submission Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_profile = UserProfile(
            name=request.form.get('name'),
            skill_offer=request.form.get('skill_offer'),
            skill_seek=request.form.get('skill_seek'),
            bio=request.form.get('bio')
        )
        db.session.add(new_profile)
        db.session.commit()  # Lock it into the cloud database permanently
        return redirect(url_for('index'))
    return render_template('register.html')

# 4. Real-Time Chat Listener
@socketio.on('message')
def handle_message(msg):
    print('Message received: ' + msg)
    send(msg, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, debug=True)
