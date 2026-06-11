import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
# ... (Keep the rest of your app.py code exactly the same as provided before) ...
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret_skill_swap_key_123')

# Database configuration (Defaults to local sqlite if DATABASE_URL isn't set on Render)
# --- DATABASE CONNECTION ---
# Fallback to an absolute SQLite path if DATABASE_URL doesn't exist
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:////tmp/skill_swap.db' # Uses temporary writeable memory folder

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    offering = db.Column(db.String(100), nullable=False)
    seeking = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room = db.Column(db.String(100), nullable=False)
    sender = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)

# --- ROUTES ---

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        profiles = User.query.filter(
            (User.name.ilike(f'%{search_query}%')) |
            (User.offering.ilike(f'%{search_query}%')) |
            (User.seeking.ilike(f'%{search_query}%'))
        ).all()
    else:
        profiles = User.query.all()
    return render_template('index.html', profiles=profiles, title='Skill Swap Platform', search_query=search_query)

# Fix for the 404 error shown in image 5fdfab0d-6578-47fa-bbd9-a4b34016834f
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        offering = request.form.get('offering')
        seeking = request.form.get('seeking')
        bio = request.form.get('bio', '')
        
        if name and offering and seeking:
            new_user = User(name=name, offering=offering, seeking=seeking, bio=bio)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
            
    return render_template('register.html')

@app.route('/chat/<int:user_id>')
def chat(user_id):
    target_user = User.query.get_or_404(user_id)
    return render_template('chat.html', target_user=target_user)

# --- WEBSOCKET EVENT HANDLERS ---

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    # Optional: Fetch past chat history from database and send it back to the single user
    past_messages = Message.query.filter_by(room=room).all()
    for msg in past_messages:
        emit('message_response', {'sender': msg.sender, 'content': msg.content}, room=request.sid)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    sender = data['sender']
    content = data['content']
    
    # Save the conversation to the database
    new_msg = Message(room=room, sender=sender, content=content)
    db.session.add(new_msg)
    db.session.commit()
    
    # Broadcast message to everyone in the chat room room
    emit('message_response', {'sender': sender, 'content': content}, room=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
    #abc
