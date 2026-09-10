from api import create_app


class FakeRepository:
    def check_health(self):
        return True

    def list_books(self, isbn=None):
        books = [{
            "isbn": "978-test",
            "title": "Libro",
            "author": "Autor",
            "publisher": "Editorial",
            "publicationYear": 2026,
            "price": 100,
            "stock": 2,
            "description": "Descripción",
            "format": "Digital",
            "imageUrl": "https://example.test/book.png",
        }]
        return [book for book in books if isbn is None or book["isbn"] == isbn]

    def list_cloud_concepts(self):
        return [{"conceptId": 1, "concept": "Cloud", "definition": "x"}]


def test_create_app_keeps_http_contract_and_supports_injected_repository():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    client = app.test_client()

    root = client.get("/?format=json")
    assert root.status_code == 200
    assert root.get_json()["status"] == "running"

    books = client.get("/books?format=json")
    assert books.status_code == 200
    assert books.get_json()["count"] == 1

    minimal = client.get("/books/minimal?format=json")
    assert minimal.status_code == 200
    assert minimal.get_json()["books"][0]["imageUrl"].endswith("book.png")


def test_database_failure_is_reported_as_service_unavailable():
    class BrokenRepository(FakeRepository):
        def check_health(self):
            raise RuntimeError("database unavailable")

    app = create_app({"TESTING": True}, repository=BrokenRepository())
    response = app.test_client().get("/health?format=json")

    assert response.status_code == 500
    assert response.get_json() == {"error": "Ocurrió un error interno."}


def test_wsdl_is_served_from_configuration():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    response = app.test_client().get("/library-classifier.wsdl")

    assert response.status_code == 200
    assert b"LibraryClassifier" in response.data
    assert b'location="http://localhost/soap"' in response.data
