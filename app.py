from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skillswap_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///skillswap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

socketio = SocketIO(app, cors_allowed_origins="*")

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skill_offer = db.Column(db.String(100), nullable=False)
    skill_seek = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        profiles = UserProfile.query.filter(
            (UserProfile.name.ilike(f'%{search_query}%')) |
            (UserProfile.skill_offer.ilike(f'%{search_query}%')) |
            (UserProfile.skill_seek.ilike(f'%{search_query}%'))
        ).all()
    else:
        profiles = UserProfile.query.all()
    return render_template('index.html', title="Skill Swap Platform", profiles=profiles, search_query=search_query)

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
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html')

# NEW: Route to launch a private chat window with a specific swapper
@app.route('/chat/<int:receiver_id>')
def private_chat(receiver_id):
    receiver = UserProfile.query.get_or_404(receiver_id)
    return render_template('chat.html', receiver=receiver)

# WebSocket Room Handlers
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)

@socketio.on('private_message')
def handle_private_message(data):
    room = data['room']
    sender = data['sender']
    message = data['message']
    payload = f"<strong>{sender}:</strong> {message}"
    # Broadcast exclusively inside the designated private room channel
    emit('new_message', payload, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
