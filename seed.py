from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import random

# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['mental_health_chatbot']

# Clear existing moods collection
db.moods.drop()

# Define sample moods and users
moods = ["happy", "sad", "stressed", "relaxed", "anxious"]
user_id = "user123"

# Generate sample data for the past 14 days
seed_data = []
for i in range(14):
    date = datetime.now() - timedelta(days=i)
    for _ in range(random.randint(1, 3)):  # Add 1-3 mood entries per day
        seed_data.append({
            "user_id": user_id,
            "mood": random.choice(moods),
            "timestamp": date.replace(hour=random.randint(8, 20))  # Random hour
        })

# Insert data into MongoDB
db.moods.insert_many(seed_data)

print(f"Seeded {len(seed_data)} mood entries!")
