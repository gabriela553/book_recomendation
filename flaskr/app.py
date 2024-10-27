import requests as requests_add
import requests as requests_search
from flask import Flask, render_template, request, jsonify
from flask_pymongo import PyMongo
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

app.config["MONGO_URI"] = "mongodb://localhost:27017/book_recommendation"

mongo = PyMongo(app)


@app.route("/")
def index():
    return render_template("index.html")


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


if __name__ == "__main__":
    app.run(debug=True)
