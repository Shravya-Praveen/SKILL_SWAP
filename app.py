from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skillswap_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///skillswap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Explicitly configuration for Render deployment to handle fallback streaming
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

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
    profiles = UserProfile.query.all()
    return render_template('index.html', title="Skill Swap Platform", profiles=profiles)

# BACKEND CHANGE: Accept both sender and receiver IDs to build a true peer-to-peer room
@app.route('/chat/<int:sender_id>/<int:receiver_id>')
def private_chat(sender_id, receiver_id):
    sender = UserProfile.query.get_or_404(sender_id)
    receiver = UserProfile.query.get_or_404(receiver_id)
    return render_template('chat.html', sender=sender, receiver=receiver)

# WebSocket Room Engine Manager
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    print(join_room(room)) # Server logs verification line

@socketio.on('private_message')
def handle_private_message(data):
    room = data['room']
    sender_name = data['sender']
    message = data['message']
    payload = f"<strong>{sender_name}:</strong> {message}"
    # Secure broadcast directly inside the room matrix
    emit('new_message', payload, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
