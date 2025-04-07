import os
import requests
from flask import Flask, json, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import bcrypt
import jwt
import datetime
import uuid
from dotenv import load_dotenv
from flask_cors import CORS
from mongo_client import users, images_collection



load_dotenv(dotenv_path="./.env.local")


UNSPLASH_URL = "https://api.unsplash.com/photos/random"
UNSPLASH_KEY = os.environ.get("UNSPLASH_KEY", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "")

DEBUG = bool(os.environ.get("DEBUG", True))


if not UNSPLASH_KEY:
    raise EnvironmentError(
        "Please create .env.local file and insert there UNSPLASH_KEY"
    )


app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

app.config["DEBUG"] = DEBUG




@app.route("/")
def hello():
    return "hello"

@app.route("/new-image-demo")
def new_image_demo():
    word = request.args.get("query")
    headers = {"Accept-Version": "v1", "Authorization": "Client-ID " + UNSPLASH_KEY}
    params = {"query": word}
    response = requests.get(url=UNSPLASH_URL, headers=headers, params=params)

    data = response.json()
    return data

@app.route("/new-image")
def new_image():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401
    
    word = request.args.get("query")
    headers = {"Accept-Version": "v1",
               "Authorization": "Client-ID " + UNSPLASH_KEY}
    params = {"query": word}
    response = requests.get(url=UNSPLASH_URL, headers=headers, params=params)

    data = response.json()
    return data

@app.route("/images", methods=["GET", "POST"])
def images():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"message": "Unauthorized"}), 401
    
    if request.method == "GET":
        # read images from the database
        images = images_collection.find({"user_id": user_id})
        result = []
        for img in images:
            img.pop("_id", None)
            result.append(img)
        return jsonify(result)

    if request.method == "POST":
        # save images im the database
        image = request.get_json()
        image["_id"] = image.get("id")
        image["user_id"] = user_id
        result = images_collection.insert_one(image)
       
        return {"inserted_id": str(result.inserted_id)}

@app.route("/images/<image_id>", methods=["DELETE"])
def image(image_id):
    if request.method == "DELETE":
        user_id = get_user_id()  
        if not user_id:
            return jsonify({"message": "Unauthorized"}), 401
        # delete image from the database
        result = images_collection.delete_one({
            "_id": image_id,
            "user_id": user_id        
        })
        if not result:
            return {"error": "Image wasn't deleted. Please try again"}, 500
        if result and not result.deleted_count:
            return {"error": "Image not found"}, 404
        return {"deleted_id": image_id}
    
def get_user_id():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        try:
            token = auth.split(" ")[1]
            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            return decoded["user_id"]
        except:
            pass
    return None

# registration
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Username and password required"}), 400

    if users.find_one({"username": username}):
        return jsonify({"message": "User already exists"}), 409

    user_id = str(uuid.uuid4())  # user_id
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    result = users.insert_one({
        "user_id": user_id,
        "username": username,
        "password": hashed_pw
    })

    return jsonify({"message": "User registered successfully"}), 201


# Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    print(username)
    print(password)
    user = users.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
        payload = {
            "user_id": user['user_id'],
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30)}
            # "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)}

        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        return jsonify({"token": token}), 200

    return jsonify({"message": "Invalid username or password"}), 401

    

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
