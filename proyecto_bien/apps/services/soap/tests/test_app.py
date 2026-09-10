from apps.services.soap.app import create_app


class FakeRepository:
    def check_health(self):
        return True

    def list_books(self, isbn=None):
        books = [{
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
        return [book for book in books if isbn is None or isbn == book["isbn"]]

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
