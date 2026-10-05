from apps.services.soap.app import create_app
from apps.services.login.security import create_jwt

import os

os.environ.setdefault("JWT_SECRET_KEY", "soap-test-secret")


class FakeRepository:
    def __init__(self):
        self.books = [{
            "isbn": "9786070001001",
            "title": "Libro",
            "author": "Autora",
            "publicationYear": 2026,
            "publisher": "Editorial",
            "price": 120,
            "stock": 4,
            "description": "Descripción",
            "format": "Impreso",
            "imageUrl": "image.png",
        }]

    def check_health(self):
        return True

    def list_books(self, isbn=None):
        return [book for book in self.books if isbn is None or isbn == book["isbn"]]

    def create_book(self, data):
        book = {**data, "author": data.get("author", ""), "imageUrl": ""}
        self.books.append(book)
        return book

    def update_book(self, isbn, data):
        book = next((item for item in self.books if item["isbn"] == isbn), None)
        if not book:
            return None
        book.update(data)
        return book

    def delete_book(self, isbn):
        book = next((item for item in self.books if item["isbn"] == isbn), None)
        if not book:
            return False
        self.books.remove(book)
        return True

    def list_minimal_books(self):
        return self.list_books()

    def list_cloud_concepts(self):
        return [{"conceptId": 1, "concept": "IaaS", "definition": "Infraestructura"}]


def test_catalog_routes_default_to_xml():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    client = app.test_client()

    response = client.get("/books")

    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    assert b"<title>Libro</title>" in response.data


def test_catalog_routes_support_json_without_changing_xml_default():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    client = app.test_client()

    response = client.get("/books?format=json")

    assert response.status_code == 200
    assert response.get_json()["count"] == 1


def test_legacy_cloud_concepts_alias_is_available():
    app = create_app({"TESTING": True}, repository=FakeRepository())

    response = app.test_client().get("/cloud-concepts")

    assert response.status_code == 200
    assert b"IaaS" in response.data


def test_swagger_ui_and_openapi_are_served_locally():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    client = app.test_client()

    docs = client.get("/docs/")
    specification = client.get("/openapi.yaml")

    assert docs.status_code == 200
    assert docs.mimetype == "text/html"
    assert b"SwaggerUIBundle" in docs.data
    assert b"/openapi.yaml" in docs.data
    assert specification.status_code == 200
    assert specification.mimetype in {"application/yaml", "text/yaml"}
    assert b"openapi: 3.0.3" in specification.data


def test_root_and_health_are_valid_xml():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    client = app.test_client()

    assert b"<service>library-classifier</service>" in client.get("/").data
    assert b"<status>ok</status>" in client.get("/health").data


def test_books_crud_requires_admin_jwt_and_invalidates_routes():
    app = create_app({"TESTING": True}, repository=FakeRepository())
    client = app.test_client()
    token = create_jwt({"user_id": 1, "role_id": 1}, expires_in=3600)
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"isbn": "9780000000001", "title": "Nuevo", "stock": 2, "author": "Autor Nuevo"}

    assert client.post("/books?format=json", json=payload).status_code == 401
    created = client.post("/books?format=json", json=payload, headers=headers)
    assert created.status_code == 201
    updated = client.put("/books/9780000000001?format=json", json={**payload, "title": "Actualizado"}, headers=headers)
    assert updated.status_code == 200
    assert updated.get_json()["title"] == "Actualizado"
    deleted = client.delete("/books/9780000000001?format=json", headers=headers)
    assert deleted.status_code == 200
    assert client.get("/books/9780000000001?format=json").status_code == 404
