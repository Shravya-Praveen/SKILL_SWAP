from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import emit, join_room, leave_room
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'skillswap_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///skillswap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Configure SocketIO engine safely for Render deployment
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    skill_offer = db.Column(db.String(100), nullable=False)
    skill_seek = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)

with app.app_context():
    db.create_all()
    # If the database is empty, let's pre-populate it with your users
    if UserProfile.query.count() == 0:
        u1 = UserProfile(name="Alex Johnson", skill_offer="Python Programming", skill_seek="UI/UX Design", bio="Experienced backend developer.")
        u2 = UserProfile(name="Priya Sharma", skill_offer="Graphic Design", skill_seek="Web Development", bio="Creative designer eager to build.")
        u3 = UserProfile(name="Soujanya", skill_offer="Dance", skill_seek="Music", bio="Looking to trade dance choreography.")
        db.session.add_all([u1, u2, u3])
        db.session.commit()

@app.route('/')
def index():
    profiles = UserProfile.query.all()
    return render_template('index.html', title="Skill Swap Platform", profiles=profiles)

# Core Chat Handler: Matches the sender profile and receiver profile together
@app.route('/chat/<int:sender_id>/<int:receiver_id>')
def private_chat(sender_id, receiver_id):
    sender = UserProfile.query.get_or_404(sender_id)
    receiver = UserProfile.query.get_or_404(receiver_id)
    return render_template('chat.html', sender=sender, receiver=receiver)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Grab data submitted from the registration form
        name = request.form.get('name')
        skill_offer = request.form.get('skill_offer')
        skill_seek = request.form.get('skill_seek')
        bio = request.form.get('bio')
        
        # Save the new user to your SQLite database
        new_user = UserProfile(name=name, skill_offer=skill_offer, skill_seek=skill_seek, bio=bio)
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('index'))
        
    return render_template('register.html')


@socketio.on('join')
def on_join(data):
    # Dynamically create a unique room name for these two specific users
    sender = min(int(data['sender_id']), int(data['receiver_id']))
    receiver = max(int(data['sender_id']), int(data['receiver_id']))
    room = f"room_{sender}_{receiver}"
    
    join_room(room)
    print(f"User joined private room: {room}")

@socketio.on('private_message')
def handle_private_message(data):
    sender = min(int(data['sender_id']), int(data['receiver_id']))
    receiver = max(int(data['sender_id']), int(data['receiver_id']))
    room = f"room_{sender}_{receiver}"
    
    payload = {
        'sender_name': data['sender_name'],
        'message': data['message']
    }
    # Send the message ONLY to users inside this private room
    emit('new_message', payload, to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
