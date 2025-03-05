from pymongo import MongoClient

# Update with your MongoDB connection string
mongo_url = "mongodb+srv://cis5372assign:KdzR3uOcxboruuwq@cluster0.hf2aj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(mongo_url)
db = client["mental_health_chatbot_db"]
users_col = db["users"]

# Set the email of the user you want to make admin
target_email = "ravi@gmail.com"

result = users_col.update_one(
    {"email": target_email},
    {"$set": {"is_admin": True}}
)

if result.modified_count == 1:
    print(f"User with email {target_email} has been updated to admin.")
else:
    print(f"No user found with email {target_email} or already an admin.")
