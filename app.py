from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, send
from flask_sqlalchemy import SQLAlchemy
import os

# 1. Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] ='skillswap_secret_key_123'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Allow CORS for all origins (for development purposes)
# 2. Temporary Data Store (Using a list of dictionaries to act as a database)
profiles = [
    {
        "name": "Alex Johnson",
        "skill_offer": "Python Programming",
        "skill_seek": "UI/UX Design",
        "bio": "Experienced backend developer looking to learn design basics."
    },
    {
        "name": "Priya Sharma",
        "skill_offer": "Graphic Design",
        "skill_seek": "Web Development",
        "bio": "Creative designer eager to build my own portfolio website."
    }
]
# 1. Define the User Profile Table Structure
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)         # Automatic unique ID for each user
    name = db.Column(db.String(100), nullable=False)     # Name string (Max 100 characters)
    skill_offer = db.Column(db.String(100), nullable=False) # Skill they teach
    skill_seek = db.Column(db.String(100), nullable=False)  # Skill they want to learn
    bio = db.Column(db.Text, nullable=True)              # Paragraph description

# 2. Tell Python to automatically build this table inside your cloud database
with app.app_context():
    db.create_all()
# 3. Route for the Home/Browse Page

@app.route('/')

def index():
    # 1. Grab what the user typed in the search input box
    search_query = request.args.get('search', '').strip().lower()
    
    # 2. If the user actually searched for something...
    if search_query:
        filtered_profiles = []
        for p in profiles:
            # Check if the search text matches their name, offer skill, or seek skill
            if (search_query in p['name'].lower() or 
                search_query in p['skill_offer'].lower() or 
                search_query in p['skill_seek'].lower()):
                filtered_profiles.append(p)
    else:
        # 3. If no search was made, show all profiles like normal
        filtered_profiles = profiles

    # 4. Send the filtered list and the search text back to the HTML page
    return render_template('index.html', profiles=filtered_profiles, search_query=request.args.get('search', ''))
@app.route('/')
def index():
    search_query = request.args.get('search', '')

    if search_query:
        # Professional filter logic querying the database directly
        profiles = UserProfile.query.filter(
            (UserProfile.name.ilike(f'%{search_query}%')) |
            (UserProfile.skill_offer.ilike(f'%{search_query}%')) |
            (UserProfile.skill_seek.ilike(f'%{search_query}%'))
        ).all()
    else:
        # Pull absolutely every registered profile saved in the cloud
        profiles = UserProfile.query.all()

    return render_template('index.html', title="Skill Swap Platform", profiles=profiles, search_query=search_query)
# 4. Route for the Registration Form (Handles both viewing and submitting the form)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Extract data from the submitted HTML form fields
        new_profile = {
            "name": request.form.get('name'),
            "skill_offer": request.form.get('skill_offer'),
            "skill_seek": request.form.get('skill_seek'),
            "bio": request.form.get('bio')
        }
        # Append the new profile to our temporary "database"
        profiles.append(new_profile)
        
        # Redirect back to the browse page to view the updated list
        return redirect(url_for('index'))
    
    # If it's a GET request, just display the empty form page
    return render_template('register.html')

@socketio.on('message')
def handle_message(msg):
    print('Message received: ' + msg)
    # This sends the message out to everyone currently connected to the chat
    send(msg, broadcast=True)

# 5. Start the local development server
if __name__ == '__main__':
    socketio.run(app, debug=True)


