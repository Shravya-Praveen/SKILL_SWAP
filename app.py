import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'secret_skill_swap_key_123')

# Database configuration (Defaults to local sqlite if DATABASE_URL isn't set on Render)
DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = 'sqlite:////tmp/skill_swap.db'

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

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
    search_query = request.args.get('search', '').strip()
    if search_query:
        users = User.query.filter(
            db.or_(
                User.name.ilike(f'%{search_query}%'),
                User.offering.ilike(f'%{search_query}%'),
                User.seeking.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        users = User.query.all()
    return render_template('index.html', users=users, search_query=search_query, title='Skill Swap Platform')

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
    # FIX: my_id is passed via query param so the room can be deterministic
    my_id = request.args.get('my_id', 0, type=int)
    target_user = User.query.get_or_404(user_id)
    my_user = User.query.get(my_id) if my_id else None
    # Build a stable room name from sorted IDs so both users land in the same room
    if my_id and my_id != user_id:
        room = f"room_{min(my_id, user_id)}_{max(my_id, user_id)}"
    else:
        room = f"room_user_{user_id}"
    return render_template('chat.html', target_user=target_user, my_user=my_user, room=room)

# --- WEBSOCKET EVENT HANDLERS ---

@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    # Send past chat history to the joining user only
    past_messages = Message.query.filter_by(room=room).all()
    for msg in past_messages:
        emit('message_response', {'sender': msg.sender, 'content': msg.content}, to=request.sid)

@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    sender = data['sender']
    content = data['content']

    # Save to database
    new_msg = Message(room=room, sender=sender, content=content)
    db.session.add(new_msg)
    db.session.commit()

    # Broadcast to everyone in the room
    emit('message_response', {'sender': sender, 'content': content}, to=room)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
