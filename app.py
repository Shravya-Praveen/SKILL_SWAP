from flask import Flask, render_template, request, redirect, url_for

# 1. Initialize the Flask application
app = Flask(__name__)

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

# 3. Route for the Home/Browse Page
@app.route('/')
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

# 5. Start the local development server
if __name__ == '__main__':
    app.run(debug=True)