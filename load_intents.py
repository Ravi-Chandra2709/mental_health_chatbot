import json
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
mongo_uri = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(mongo_uri)
db = client['mental_health_chatbot']
intents_collection = db['intents']

# Load intents.json
with open('intents.json') as file:
    data = json.load(file)

# Insert data into MongoDB
intents_collection.drop()  # Clear the collection first
intents_collection.insert_many(data['intents'])

print("Intents loaded into MongoDB!")
