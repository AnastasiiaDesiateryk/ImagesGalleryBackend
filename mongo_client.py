import os
from pymongo import MongoClient
from dotenv import load_dotenv
import certifi
load_dotenv(dotenv_path="./.env.local")

MONGO_URL = os.environ.get("MONGO_URL", "")
print(MONGO_URL)

mongo_client = MongoClient(MONGO_URL, tlsCAFile=certifi.where())

db = mongo_client["images_db"]

users = db["users"]
images_collection = db["saved_photos"]


# test
# def insert_test_document():
#      db = mongo_client.test
#      test_collection = db.test_collection
#      res = test_collection.insert_one({"name": "Bohdan", "Instructor": True})
#      print(res)
