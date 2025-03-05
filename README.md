###  Mental Health Chatbot v2
A Flask-based chatbot designed to support mental health awareness by tracking moods and engaging in mental health-related conversations. This chatbot logs user moods, detects distress signals, and provides sentiment-based responses using Sentence Transformers and VADER Sentiment Analysis. 

The application stores data securely in MongoDB Atlas and uses Flask sessions for authentication. An admin dashboard provides trends and insights, and email reminders are sent using SendGrid.

---

##  Features
AI-powered Chatbot - Uses NLP-based embeddings for user intent detection.  
Mood Logging & Trends - Users can log moods and view graphical trends.  
Sentiment Analysis - Detects negative sentiment and triggers distress alerts.  
Secure User Authentication - Uses Flask sessions, password hashing, and email validation.  
Admin Dashboard - Allows admins to visualize anonymous user trends.  
Email Reminders - Uses SendGrid to send daily/weekly mood check-in emails.  
MongoDB Atlas - Secure cloud database for storing user chats and logs.  

---

##  Prerequisites
Ensure you have the following installed:
- Python 3.12.4
- MongoDB Atlas Account (or a running local MongoDB instance)
- A SendGrid API Key (for email notifications)
- Chart.js (for frontend visualizations)

---

##  Folder Structure
```
mental-health-chatbot-v2/
│── templates/                   # HTML Frontend Files
│   ├── index.html                # Landing Page
│   ├── signup.html                # User Signup
│   ├── login.html                 # User Login
│   ├── chat.html                  # Chat Page
│   ├── admin_dashboard.html        # Admin Dashboard
│   ├── settings.html               # User Settings
│── static/                      # Static Assets (JS, CSS)
│   ├── script.js                  # Handles User Authentication & Requests
│   ├── chat.js                    # Chat functionality
│   ├── style.css                  # Styling
│── app.py                        # Main Flask Application
│── requirements.txt              # Python dependencies
│── intents.json                  # Chatbot Intent Patterns
│── .env                          # Secret Environment Variables
│── load_intents.py               # Load Chatbot Responses into MongoDB
│── seed_data.py                  # Seed Sample Mood Data
│── README.md                     # Documentation
```

---

##  Installation
1 Clone the Repository
```bash
git clone https://github.com/your-repo/mental-health-chatbot-v2.git
cd mental-health-chatbot-v2
```

2 Create & Activate a Virtual Environment
```bash
conda create --name mental_health_chatbot python=3.12.4 -y
conda activate mental_health_chatbot
```

3 Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Setup Environment Variables
1 Create a `.env` file in the project root:
```bash
touch .env
```
2 Add the following values (Update with your credentials):
```plaintext
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
SENDGRID_API_KEY=your_sendgrid_api_key
SECRET_KEY=your_super_secret_key
FROM_EMAIL=your_verified_sendgrid_email
```
3 Whitelist your IP Address in MongoDB Atlas > Network Access.

---

## 🛠️ Load Chatbot Intents (Optional)
If the chatbot intents need to be reloaded or modified, run:
```bash
python load_intents.py
```
This will reset and populate the chatbot responses in MongoDB.

---

##  Seed Mood Data (For Testing)
To generate random mood entries for a test user, run:
```bash
python seed_data.py
```
This will simulate a user's mood logs for the past 14 days.

---

##  Running the Application
1 Start the Flask Server
```bash
python app.py
```
2 Open the Web App
Visit [`http://127.0.0.1:5000`](http://127.0.0.1:5000) in your browser.

---

## 📡 API Endpoints
### 🔹 User Authentication
User Signup `POST /signup`
```json
{
    "username": "JohnDoe",
    "email": "john@example.com",
    "password": "StrongPass123",
    "consent": "yes"
}
```
User Login `POST /login`
```json
{
    "email": "john@example.com",
    "password": "StrongPass123"
}
```
User Logout `GET /logout`

---

###  Chatbot Interaction
POST `/chat`  
Send a message to the chatbot.
```json
{
    "message": "Hi"
}
```
Response:
```json
{
    "response": "Hello! How are you feeling today?",
    "intent": "greeting",
    "similarity": 0.89,
    "sentiment_compound": 0.5
}
```
Test Using cURL
```bash
curl -X POST -H "Content-Type: application/json" -d '{"message": "Hi"}' http://127.0.0.1:5000/chat
```

---

###  Mood Logging
POST `/log_mood`  
```json
{
    "mood": "happy"
}
```
Response:
```json
{
    "message": "Mood logged successfully!"
}
```
Test Using cURL
```bash
curl -X POST -H "Content-Type: application/json" -d '{"mood": "happy"}' http://127.0.0.1:5000/log_mood
```

---

###  Retrieve Mood Data
GET `/get_moods`  
Returns mood trends for a logged-in user.
```json
{
    "moods": [
        {"mood": "happy", "timestamp": "2025-01-24"},
        {"mood": "stressed", "timestamp": "2025-01-25"}
    ]
}
```

---

###  Send Email Reminder
POST `/send_reminder`
```json
{
    "email": "user@example.com"
}
```
Response
```json
{
    "message": "Reminder sent!"
}
```

---

##  Admin Dashboard
View Trends: `GET /admin`  
Admins can view user trends anonymously.

Features:
-  Mood Graphs  
-  User Activity Trends  
-  Distress Alert Reports  

---

##  Next Steps
 Enhancements Coming Soon:
- 🔹 Better NLP Responses
- 🔹 Advanced Sentiment Analysis
- 🔹 More Mood Trend Visualizations
- 🔹 Mobile-Friendly UI

---

##  Summary
This guide provides everything needed to set up, run, and deploy the Mental Health Chatbot v2.  
 If you face any issues, let us know! 
