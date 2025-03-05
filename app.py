import os
import random
import datetime
from datetime import datetime
import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from sentence_transformers import SentenceTransformer, util
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from apscheduler.schedulers.background import BackgroundScheduler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from bson.objectid import ObjectId
import atexit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
MONGODB_URL = os.getenv("MONGODB_URL")
SECRET_KEY = os.getenv("SECRET_KEY")

app.secret_key = SECRET_KEY

# ---------------------
# Load Intents Data
# ---------------------
with open('intents.json', 'r') as f:
    intents_data = f.read()
intents = json.loads(intents_data)["intents"]

# ---------------------
# Initialize Models
# ---------------------
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embed_model = SentenceTransformer(model_name)
analyzer = SentimentIntensityAnalyzer()

# Precompute embeddings for intent patterns
pattern_embeddings = []
tag_to_responses = {}
for intent in intents:
    tag = intent["tag"]
    responses = intent["responses"]
    tag_to_responses[tag] = responses
    for pattern in intent["patterns"]:
        embedding = embed_model.encode(pattern, convert_to_tensor=True)
        pattern_embeddings.append((embedding, tag))

# ---------------------
# Connect to MongoDB
# ---------------------
# try:
#     client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
#     client.server_info()  # This will trigger a connection attempt
#     print("Successfully connected to MongoDB!")
# except Exception as e:
#     print("Error connecting to MongoDB:", e)

mongo_client = MongoClient(MONGODB_URL)
db = mongo_client["mental_health_chatbot_db"]

user_messages_col = db["user_messages"]  # Chat messages and sentiment scores
moods_col = db["moods"]                  # Self-reported moods
users_col = db["users"]                  # User credentials and notification settings

# ---------------------
# Helper Decorators
# ---------------------
def login_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "is_admin" not in session or not session["is_admin"]:
            return "Access denied: Admins only", 403
        return func(*args, **kwargs)
    return wrapper

# ---------------------
# Auth Routes
# ---------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    
    data = request.form
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    consent = data.get("consent")
    if not username or not email or not password or not consent:
        return "All fields including consent are required", 400

    if users_col.find_one({"email": email}):
        return "User with this email already exists!", 400
    
    hashed_pw = generate_password_hash(password)
    new_user = {
        "username": username,
        "email": email,
        "password": hashed_pw,
        "created_at": datetime.utcnow(),
        "is_admin": False,  # Default non-admin
        # Default notification settings
        "notification_opt_in": False,
        "notification_frequency": "daily",
        "notification_time": "08:00"
    }
    users_col.insert_one(new_user)
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    data = request.form
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return "Missing email or password", 400
    
    user = users_col.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return "Invalid credentials", 401

    session["user_id"] = str(user["_id"])
    session["username"] = user["username"]
    session["email"] = user["email"]
    session["is_admin"] = user.get("is_admin", False)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------------
# Chat & Mood Routes
# ---------------------
@app.route('/')
@login_required
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    if "user_id" not in session:
        return jsonify({"response": "Please log in first."})

    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Please type something to start chatting."})
    
    # Intent detection
    user_embedding = embed_model.encode(user_message, convert_to_tensor=True)
    best_tag = "fallback"
    best_score = 0.0
    for (embed, tag) in pattern_embeddings:
        sim_score = float(util.pytorch_cos_sim(user_embedding, embed))
        if sim_score > best_score:
            best_score = sim_score
            best_tag = tag

    threshold = 0.6
    if best_score < threshold:
        best_tag = "fallback"

    # By default, pick a random response from the matched tag
    possible_responses = tag_to_responses.get(best_tag, ["I'm not sure I understand."])
    bot_response = random.choice(possible_responses)

    # 1) CRISIS CHECK (same as your existing logic)
    sentiment_scores = analyzer.polarity_scores(user_message)
    compound_score = sentiment_scores["compound"]
    CRISIS_THRESHOLD = -0.5
    CRISIS_KEYWORDS = ["suicide", "kill myself", "end my life", "i want to die", "self-harm", "hurt myself"]
    crisis_detected = (compound_score < CRISIS_THRESHOLD) or any(keyword in user_message.lower() for keyword in CRISIS_KEYWORDS)
    if crisis_detected:
        crisis_message = (
            "\n\n⚠️ It appears you might be in severe distress. "
            "If you feel unsafe or are in immediate danger, please call 911 or your local emergency number immediately. "
            "You might also consider reaching out to a trusted friend or mental health professional."
        )
        bot_response += crisis_message

    # 2) CONTEXT HANDLING
    # If user matched "stressed", set context
    if best_tag == "stressed":
        # Instead of using the random response from the dataset,
        # we might override it to ensure it ends with the question:
        bot_response = "I'm sorry you're feeling overwhelmed. Would you like some quick stress-relief tips?"
        session["conversation_context"] = "offer_stress_tips"

    # If user matched "affirmation" AND we have "offer_stress_tips" in context => Provide tips
    elif best_tag == "affirmation" and session.get("conversation_context") == "offer_stress_tips":
        bot_response = (
            "Here are some quick stress-relief tips:\n"
            "1. Practice deep breathing for a few minutes.\n"
            "2. Take a short walk or stretch break.\n"
            "3. Try journaling or talking to a friend.\n"
            "4. Listen to calming music.\n\n"
            "I hope these help! Let me know if you'd like more suggestions."
        )
        # Clear or change the context so we don't repeat
        session["conversation_context"] = None

    # 3) Store message in DB
    doc = {
        "user_id": session["user_id"],
        "message": user_message,
        "intent": best_tag,
        "similarity_score": best_score,
        "bot_response": bot_response,
        "sentiment_compound": compound_score,
        "crisis_detected": crisis_detected,
        "timestamp": datetime.utcnow()
    }
    user_messages_col.insert_one(doc)

    return jsonify({
        "response": bot_response,
        "intent": best_tag,
        "similarity": best_score,
        "sentiment_compound": compound_score,
        "crisis_detected": crisis_detected
    })

@app.route('/mood', methods=['POST'])
@login_required
def log_mood():
    data = request.get_json()
    mood = data.get("mood")
    if mood is None:
        return jsonify({"error": "No mood provided"}), 400
    mood_doc = {
        "user_id": session["user_id"],
        "mood": mood,
        "timestamp": datetime.utcnow()
    }
    moods_col.insert_one(mood_doc)
    return jsonify({"message": "Mood logged successfully"}), 200

@app.route('/moods', methods=['GET'])
@login_required
def get_moods():
    user_id = session["user_id"]
    user_moods = list(moods_col.find({"user_id": user_id}, {"_id": 0, "user_id": 0}))
    return jsonify(user_moods)

# ---------------------
# Admin Dashboard Route
# ---------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_users = users_col.count_documents({})
    total_messages = user_messages_col.count_documents({})
    crisis_messages = user_messages_col.count_documents({"crisis_detected": True})
    total_moods = moods_col.count_documents({})

    # Calculate average mood (numeric only)
    mood_cursor = moods_col.find({}, {"mood": 1})
    mood_sum = 0
    mood_count = 0
    for mood_doc in mood_cursor:
        try:
            mood_val = float(mood_doc["mood"])
            mood_sum += mood_val
            mood_count += 1
        except:
            continue
    average_mood = mood_sum / mood_count if mood_count > 0 else "N/A"

    return render_template("admin_dashboard.html", total_users=total_users, total_messages=total_messages,
                           crisis_messages=crisis_messages, total_moods=total_moods, average_mood=average_mood)

# ---------------------
# Notification Settings Routes
# ---------------------
@app.route('/settings', methods=["GET", "POST"])
@login_required
def settings():
    user_id = session["user_id"]
    user = users_col.find_one({"_id": ObjectId(user_id)})
    if request.method == "GET":
        return render_template("settings.html", user=user)
    else:
        notification_opt_in = request.form.get("notification_opt_in") == "on"
        notification_frequency = request.form.get("notification_frequency", "daily")
        notification_time = request.form.get("notification_time", "08:00")
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "notification_opt_in": notification_opt_in,
                "notification_frequency": notification_frequency,
                "notification_time": notification_time
            }}
        )
        return redirect(url_for("settings"))

# ---------------------
# Test Notification Endpoint (SendGrid)
# ---------------------
@app.route('/send_notification', methods=["GET"])
@login_required
def send_notification():
    user_email = session.get("email")
    if not user_email:
        user = users_col.find_one({"_id": ObjectId(session["user_id"])})
        user_email = user["email"]
    
    message = Mail(
        from_email=os.environ.get("FROM_EMAIL", "your_email@example.com"),
        to_emails=user_email,
        subject="Daily Mood Check-In Reminder",
        html_content="<strong>Hi there!</strong><br>Don't forget to log your mood today and check in with your Mental Health Chatbot."
    )
    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        return jsonify({"message": "Notification email sent!", "status": response.status_code})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------
# Scheduled Notifications via APScheduler
# ---------------------
def send_scheduled_notifications():
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    weekday = now.weekday()  # Monday=0, Sunday=6

    users = list(users_col.find({"notification_opt_in": True}))
    for user in users:
        frequency = user.get("notification_frequency", "daily")
        notif_time = user.get("notification_time", "08:00")
        send_email = False

        if frequency == "daily":
            if current_time == notif_time:
                send_email = True
        elif frequency == "weekly":
            # For weekly notifications, assume sending on Monday (weekday == 0)
            if weekday == 0 and current_time == notif_time:
                send_email = True

        if send_email:
            try:
                message = Mail(
                    from_email=os.environ.get("FROM_EMAIL", "your_email@example.com"),
                    to_emails=user["email"],
                    subject="Daily Mood Check-In Reminder",
                    html_content=f"<strong>Hi {user.get('username', 'there')}!</strong><br>Don't forget to log your mood today and check in with your Mental Health Chatbot."
                )
                sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
                response = sg.send(message)
                print(f"Notification sent to {user['email']} with status code {response.status_code}")
            except Exception as e:
                print(f"Error sending email to {user['email']}: {e}")

# For testing, the scheduler runs every minute
scheduler = BackgroundScheduler()
scheduler.add_job(func=send_scheduled_notifications, trigger="cron", minute="*")
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# ---------------------
# Privacy & Terms Endpoints
# ---------------------
@app.route('/privacy')
def privacy():
    return render_template("privacy.html")

@app.route('/terms')
def terms():
    return render_template("terms.html")

# ---------------------
# Account Deletion / Data Export Endpoint
# ---------------------
@app.route('/delete_account', methods=["GET", "POST"])
@login_required
def delete_account():
    user_id = session["user_id"]
    # Export user's data: account details, chat messages, and mood logs
    user_data = users_col.find_one({"_id": ObjectId(user_id)}, {"_id": 0, "password": 0})
    messages = list(user_messages_col.find({"user_id": user_id}, {"_id": 0, "user_id": 0}))
    moods = list(moods_col.find({"user_id": user_id}, {"_id": 0, "user_id": 0}))
    
    export_data = {
        "user": user_data,
        "chat_messages": messages,
        "moods": moods
    }
    
    if request.method == "GET":
        return render_template("delete_account.html", export_data=export_data)
    else:
        # POST: Confirm deletion
        users_col.delete_one({"_id": ObjectId(user_id)})
        user_messages_col.delete_many({"user_id": user_id})
        moods_col.delete_many({"user_id": user_id})
        session.clear()
        return "Your account and all associated data have been deleted."

if __name__ == '__main__':
    app.run(debug=True)
