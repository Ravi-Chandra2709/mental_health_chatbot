# Mental Health Chatbot

This is a Flask-based chatbot designed to help users track their moods and receive mental health support. The application integrates with MongoDB Atlas for data storage and provides a frontend interface using Chart.js to visualize mood trends.

## Features

- Chatbot with predefined intents and responses.
- Mood logging with timestamped entries.
- Visualization of mood trends over time using Chart.js.
- Email reminders via SendGrid.

## Prerequisites

Make sure you have the following installed:

- Python 3.12.4
- MongoDB Atlas account (or a local MongoDB installation)
- Frontend: yet to decide!

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/mental-health-chatbot.git
   cd mental-health-chatbot
   ```
2. Create a virtual environment using Conda:
   ```bash
   conda create --name mental_health_chatbot python=3.12.4 -y
   conda activate mental_health_chatbot
   ```
3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Setup Environment Variables

1. Create a `.env` file in the project root:
   ```bash
   touch .env
   ```
2. Add the following values (update with your credentials):
   ```plaintext
   MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
   SENDGRID_API_KEY=your_sendgrid_api_key
   ```

## Load Predefined Intents

The intents have already been loaded into MongoDB Atlas, so running this step is not necessary unless you want to reload or modify the intent data.

If you need to update the intents, run the following command:

```bash
python load_intents.py
```

This will repopulate the database with intent-response pairs for the chatbot.

## Seed Mood Data (For Testing)

### Existing Data

As of now, some sample data is already loaded into the database. If you need to add a **new user** or modify existing data, you can edit the `seed_data.py` file.

### Adding a New User

1. Open `seed_data.py`
2. Locate the following line:
   ```python
   user_id = "user123"
   ```
   Change `user123` to a unique identifier for the new user.
3. Run the script to insert new data:
   ```bash
   python seed_data.py
   ```

This generates randomized mood entries over the past 14 days for the specified user.

## Running the Application

1. Start the Flask backend:
   ```bash
   python app.py
   ```
2. Open `http://127.0.0.1:5000` in your browser to access the chatbot.

## Running the Frontend

1. Serve the frontend using Flask by ensuring `index.html` is inside the `templates/` folder.
2. Alternatively, serve it separately:
   ```bash
   python -m http.server 8080
   ```
   Then, visit `http://127.0.0.1:8080/index.html` in your browser.

## API Endpoints and Testing Guide

### Chatbot Interaction

**POST** `/chat`

Send a message to the chatbot.

```json
{
    "message": "Hi"
}
```

**Response:**

```json
{
    "response": "Hello there. Tell me how you are feeling today?"
}
```

**Test Using cURL:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"message": "Hi"}' http://127.0.0.1:5000/chat
```

---

### Log Mood

**POST** `/log_mood`

Log a user's mood.

```json
{
    "mood": "happy",
    "user_id": "user123"
}
```

**Response:**

```json
{
    "message": "Mood logged successfully!"
}
```

**Test Using cURL:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"mood": "happy", "user_id": "user123"}' http://127.0.0.1:5000/log_mood
```

---

### Retrieve Logged Moods

**GET** `/get_moods?user_id=user123`

Retrieve all logged moods for a user.

**Response (Example Data):**
```json
{
    "moods": [
        {
            "user_id": "user123",
            "mood": "happy",
            "timestamp": "2025-01-24T12:45:00"
        },
        {
            "user_id": "user123",
            "mood": "stressed",
            "timestamp": "2025-01-25T14:30:00"
        }
    ]
}
```

**Test Using cURL:**
```bash
curl -X GET "http://127.0.0.1:5000/get_moods?user_id=user123"
```

---

### Get Mood Trends

**GET** `/mood_trends?user_id=user123`

Retrieve mood data for visualization.

**Response (Example Data):**
```json
{
    "labels": ["2025-01-24", "2025-01-25"],
    "datasets": [
        {
            "label": "happy",
            "data": [1, 2],
            "borderColor": "rgba(120, 200, 150, 1)"
        }
    ]
}
```

**Test Using cURL:**
```bash
curl -X GET "http://127.0.0.1:5000/mood_trends?user_id=user123"
```

---

### Send Email Reminder

**POST** `/send_reminder`

Send a daily mood logging reminder via email.

```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "message": "Reminder sent!"
}
```

**Test Using cURL:**
```bash
curl -X POST -H "Content-Type: application/json" -d '{"email": "user@example.com"}' http://127.0.0.1:5000/send_reminder
```


This README provides everything needed to set up, run, and test the Mental Health Chatbot locally. Let us know if you encounter any issues!

