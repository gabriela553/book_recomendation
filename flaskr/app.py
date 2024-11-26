import requests as requests_add
import requests as requests_search
from bson import ObjectId
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_pymongo import PyMongo
from flask_restful import Api
from flask_login import (
    LoginManager,
    UserMixin,
    login_required,
    logout_user,
    current_user,
)
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
api = Api(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SESSION_COOKIE_SECURE"] = False
app.config["SESSION_PERMANENT"] = False
app.config["MONGO_URI"] = "mongodb://mongo:27017/book_recommendation"

login_manager = LoginManager()
login_manager.init_app(app)

bcrypt = Bcrypt(app)

mongo = PyMongo(app)


class User(UserMixin):
    def __init__(self, username, password, id):
        self.username = username
        self.password = password
        self.id = id

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if user:
        return User(user["username"], user["password"], str(user["_id"]))
    return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/auth")
def auth():
    return render_template("auth.html")


@app.route("/add", methods=["POST"])
def add_book():
    title = request.form["title"]
    author = request.form["author"]
    if not title or not author:
        return jsonify({"message": "Title and author are required."}), 400

    mongo.db.books.insert_one({"title": title, "author": author})

    google_books_api_url = f"https://www.googleapis.com/books/v1/volumes?q={title}"

    response = requests_add.get(google_books_api_url)
    if response.status_code != 200:
        return jsonify({"message": "Failed to fetch data from Google Books API."}), 500

    data = response.json()
    book_info = {}

    if not data.get("items"):
        return jsonify({"message": "No book found in API."}), 404

    if "items" in data:
        item = data["items"][0]
        volume_info = item.get("volumeInfo", {})
        book_info = {
            "title": volume_info.get("title"),
            "authors": volume_info.get("authors", []),
            "publisher": volume_info.get("publisher"),
            "publishedDate": volume_info.get("publishedDate"),
            "description": volume_info.get("description"),
        }

        mongo.db.books.update_one(
            {"title": title, "author": author}, {"$set": book_info}
        )

    return jsonify({"message": "Book added to DB!"}), 200


@app.route("/list", methods=["GET"])
def list_books():
    books = mongo.db.books.find()
    books_list = [{"title": book["title"], "author": book["author"]} for book in books]

    if not books_list:
        return jsonify({"message": "No books found in the database."}), 404

    return jsonify(books_list)


@app.route("/search", methods=["GET"])
def search_books():
    query = request.args.get("query")
    if not query:
        return jsonify({"message": "Please provide a search query."}), 400

    google_books_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}"

    response = requests_search.get(google_books_api_url)
    if response.status_code != 200:
        return jsonify({"message": "Failed to fetch data from Google Books API."}), 500

    data = response.json()
    books = []
    for item in data.get("items", []):
        book_info = item.get("volumeInfo", {})
        books.append(
            {
                "title": book_info.get("title"),
                "authors": book_info.get("authors", []),
                "publisher": book_info.get("publisher"),
                "publishedDate": book_info.get("publishedDate"),
                "description": book_info.get("description"),
            }
        )

    if not books:
        return jsonify({"message": "No books found."}), 404

    return jsonify(books), 200


@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        if data is None:
            raise ValueError("No JSON data provided")

        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        user = mongo.db.users.find_one({"username": username})
        if user:
            return jsonify({"error": "Username already exists"}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        mongo.db.users.insert_one({"username": username, "password": hashed_password})

        return jsonify({"message": "User registered successfully"}), 201
    except ValueError as ve:
        print("Error:", ve)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print("Unexpected error:", e)
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        if data is None:
            raise ValueError("No JSON data provided")

        username = data.get("username")
        password = data.get("password")

        user = mongo.db.users.find_one({"username": username})
        if not user or not bcrypt.check_password_hash(user["password"], password):
            return jsonify({"error": "Invalid username or password"}), 401
        session["user_id"] = str(user["_id"])
        return jsonify({"message": "Logged in successfully"}), 200
    except ValueError as ve:
        print("Error:", ve)
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        print("Unexpected error:", e)
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully!"}), 200


@app.route("/profile")
@login_required
def profile():
    user = mongo.db.users.find_one({"username": current_user.username})
    if user:
        favorite_books = user.get("favorite_books", [])
        return render_template("profile.html", favorite_books=favorite_books)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
