import os
import re
import sendgrid
from flask import Flask, request, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from sendgrid.helpers.mail import Mail
from sendgrid import SendGridAPIClient
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS


# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['mental_health_chatbot']
intents_collection = db['intents']

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
CORS(app)

@app.route("/")
def home():
    return render_template("index.html")

def match_intent(user_input):
    """Match user input with an intent in the database."""
    intents = intents_collection.find()
    for intent in intents:
        for pattern in intent['patterns']:
            if re.search(pattern, user_input, re.IGNORECASE):
                return intent['responses']
    return ["I'm sorry, I didn't quite understand that. Can you elaborate?"]

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint to handle user messages."""
    user_input = request.json.get('message', '')
    responses = match_intent(user_input)
    return jsonify({"response": responses[0]})

# Endpoint to log mood
@app.route('/log_mood', methods=['POST'])
def log_mood():
    """Log user mood with a timestamp."""
    data = request.json
    mood = data.get('mood', '')
    user_id = data.get('user_id', 'default_user')  # Default user for simplicity

    if not mood:
        return jsonify({"error": "Mood is required"}), 400

    # Insert mood into MongoDB
    db.moods.insert_one({
        "user_id": user_id,
        "mood": mood,
        "timestamp": datetime.now()
    })

    return jsonify({"message": "Mood logged successfully!"})

# Endpoint to retrieve moods
@app.route('/get_moods', methods=['GET'])
def get_moods():
    """Retrieve all logged moods."""
    user_id = request.args.get('user_id', 'default_user')  # Default user for simplicity
    moods = list(db.moods.find({"user_id": user_id}, {"_id": 0}))

    return jsonify({"moods": moods})

def send_email(to_email, subject, content):
    """Send an email notification."""
    try:
        message = Mail(
            from_email='cis5372assign@gmail.com',  # Use your verified email
            to_emails=to_email,
            subject=subject,
            html_content=content
        )
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        return response.status_code
    except Exception as e:
        print(e)
        return None

@app.route('/send_reminder', methods=['POST'])
def send_reminder():
    """Send a reminder to log mood."""
    data = request.json
    email = data.get('email', '')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    status_code = send_email(
        email,
        "Daily Mood Reminder",
        "<strong>Hi! How are you feeling today? Don’t forget to log your mood!</strong>"
    )

    if status_code == 202:  # SendGrid returns 202 for success
        return jsonify({"message": "Reminder sent!"})
    else:
        return jsonify({"error": "Failed to send reminder"}), 500

@app.route('/mood_trends', methods=['GET'])
def mood_trends():
    """Get mood trends for visualization."""
    user_id = request.args.get('user_id', 'default_user')
    moods = list(db.moods.find({"user_id": user_id}, {"_id": 0, "mood": 1, "timestamp": 1}))

    # Process data for trends
    mood_counts = {}
    for mood in moods:
        mood_date = mood['timestamp'].strftime('%Y-%m-%d')  # Group by date
        if mood_date not in mood_counts:
            mood_counts[mood_date] = {}
        if mood['mood'] not in mood_counts[mood_date]:
            mood_counts[mood_date][mood['mood']] = 0
        mood_counts[mood_date][mood['mood']] += 1

    # Format the data for Chart.js
    formatted_data = {
        "labels": list(mood_counts.keys()),
        "datasets": []
    }
    unique_moods = set(mood['mood'] for mood in moods)
    for mood in unique_moods:
        dataset = {
            "label": mood,
            "data": [mood_counts[date].get(mood, 0) for date in mood_counts],
            "fill": False,
            "borderColor": f"rgba({hash(mood)%255}, {hash(mood)%100 + 100}, {hash(mood)%200 + 55}, 1)",
            "tension": 0.1
        }
        formatted_data["datasets"].append(dataset)

    return jsonify(formatted_data)

if __name__ == '__main__':
    app.run(debug=True)
