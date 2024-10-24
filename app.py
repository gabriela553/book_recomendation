from flask import Flask, render_template, request
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/book_recommendation"

mongo = PyMongo(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']

    mongo.db.books.insert_one({"title": title, "author": author})
    return "Book added to DB!"


if __name__ == '__main__':
    app.run(debug=True)
