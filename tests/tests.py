import unittest
from unittest.mock import patch
from flask import json
from flaskr.app import app, mongo


class AddBookTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

        self.test_db = mongo.db.books
        self.test_db.delete_many({})

    def tearDown(self):
        self.test_db.delete_many({})

    @patch("flaskr.app.requests_add.get")
    def test_add_book_no_api_results(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"items": []}

        data = {"title": "Nonexistent Book", "author": "Test Author"}

        response = self.client.post("/add", data=data)

        self.assertEqual(response.status_code, 404)
        self.assertIn(b"No book found in API.", response.data)

    @patch("flaskr.app.requests_add.get")
    def test_add_book_api_failure(self, mock_get):
        mock_get.return_value.status_code = 500

        data = {"title": "Some Book", "author": "Test Author"}

        response = self.client.post("/add", data=data)

        self.assertEqual(response.status_code, 500)
        self.assertIn(b"Failed to fetch data from Google Books API.", response.data)

    @patch("flaskr.app.requests_add.get")
    def test_add_book_success(self, mock_get):
        mock_response_data = {
            "items": [
                {
                    "volumeInfo": {
                        "title": "Learning Python",
                        "authors": ["Mark Lutz"],
                        "publisher": "O'Reilly Media",
                        "publishedDate": "2013",
                        "description": "A comprehensive introduction to Python.",
                    }
                }
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response_data

        data = {"title": "Learning Python", "author": "Mark Lutz"}

        response = self.client.post("/add", data=data)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Book added to DB!", response.data)

        book = self.test_db.find_one({"title": data["title"], "author": data["author"]})
        self.assertIsNotNone(book)
        self.assertEqual(book["title"], data["title"])
        self.assertEqual(book["author"], data["author"])

    def test_add_book_missing_data(self):
        data = {"author": "Test Author"}

        response = self.client.post("/add", data=data)

        self.assertEqual(response.status_code, 400)


class ListBooksTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        self.test_db = mongo.db.books
        self.test_db.delete_many({})

    def tearDown(self):
        self.test_db.delete_many({})

    def test_get_books_with_data(self):
        sample_books = [
            {"title": "Joyland", "author": "Stephen King"},
            {"title": "Harry Potter", "author": "J.K. Rowling"},
        ]
        self.test_db.insert_many(sample_books)

        response = self.client.get("/list")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Joyland")
        self.assertEqual(data[1]["title"], "Harry Potter")

    def test_get_books_no_data(self):
        response = self.client.get("/list")

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "No books found in the database.")


class SearchBooksTestCase(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    @patch("flaskr.app.requests_search.get")
    def test_search_books_success(self, mock_get):
        mock_response_data = {
            "items": [
                {
                    "volumeInfo": {
                        "title": "Learning Python",
                        "authors": ["Mark Lutz"],
                        "publisher": "O'Reilly Media",
                        "publishedDate": "2013",
                        "description": "A comprehensive introduction to Python.",
                    }
                },
                {
                    "volumeInfo": {
                        "title": "Python Crash Course",
                        "authors": ["Eric Matthes"],
                        "publisher": "No Starch Press",
                        "publishedDate": "2015",
                        "description": "A fast-paced introduction to Python programming.",
                    }
                },
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response_data

        response = self.client.get("/search?query=python")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["title"], "Learning Python")
        self.assertEqual(data[1]["title"], "Python Crash Course")

    @patch("flaskr.app.requests_search.get")
    def test_search_books_no_results(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"items": []}

        response = self.client.get("/search?query=nonexistentbook")

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "No books found.")

    @patch("flaskr.app.requests_search.get")
    def test_search_books_api_failure(self, mock_get):
        mock_get.return_value.status_code = 500

        response = self.client.get("/search?query=python")
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Failed to fetch data from Google Books API.")

    def test_search_books_missing_query(self):
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data["message"], "Please provide a search query.")


if __name__ == "__main__":
    unittest.main()
