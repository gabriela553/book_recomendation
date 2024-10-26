import requests
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

    mongo.db.books.insert_one({"title": title, "author": author})
    return "Book added to DB!"


@app.route("/list", methods=["GET"])
def list_books():
    books = mongo.db.books.find()
    books_list = [{"title": book["title"], "author": book["author"]} for book in books]

    if not books_list:
        return jsonify({"message": "No books found in the database."}), 404

    return jsonify(books_list)


@app.route("/search", methods=["GET"])
def search_books():
    query = request.args.get("q")
    if not query:
        return jsonify({"message": "Please provide a search query."}), 400

    google_books_api_url = f"https://www.googleapis.com/books/v1/volumes?q={query}"

    response = requests.get(google_books_api_url)
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

    return jsonify(books)


if __name__ == "__main__":
    app.run(debug=True)
