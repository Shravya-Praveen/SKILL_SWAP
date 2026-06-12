import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key_12345')

# Auto-correct Render's postgres:// prefix to postgresql://
database_url = os.getenv("DATABASE_URL", "sqlite:///skill_swap.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    offering = db.Column(db.String(200), nullable=False)
    seeking = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, nullable=True)

# --- ROUTES ---
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    if search_query:
        profiles = User.query.filter(
            (User.name.ilike(f"%{search_query}%")) | 
            (User.offering.ilike(f"%{search_query}%")) | 
            (User.seeking.ilike(f"%{search_query}%"))
        ).all()
    else:
        profiles = User.query.all()
    return render_template('index.html', profiles=profiles, search_query=search_query)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        offering = request.form.get('offering')
        seeking = request.form.get('seeking')
        bio = request.form.get('bio')
        
        if name and offering and seeking:
            new_user = User(name=name, offering=offering, seeking=seeking, bio=bio)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
            
    return render_template('register.html')

@app.route('/chat/<int:profile_id>')
def chat(profile_id):
    target_user = User.query.get_or_404(profile_id)
    return render_template('chat.html', target_user=target_user)

# --- SOCKET EVENTS ---
@socketio.on('send_message')
def handle_message(data):
    # Broadcasts the message to everyone in the chat room
    emit('receive_message', data, broadcast=True)

# --- AUTO-CREATE TABLES ON STARTUP ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    socketio.run(app, debug=True)
