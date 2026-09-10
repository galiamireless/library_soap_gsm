from apps.services.soap.xml_codec import serialize_library, serialize_minimal


def test_library_xml_contains_catalog_fields():
    payload = serialize_library([{
        "isbn": "9786070001001",
        "title": "Libro de prueba",
        "author": "Autora",
        "publicationYear": 2026,
        "price": 120,
        "stock": 4,
        "imageUrl": "https://example.test/image.png",
    }])

    assert payload.startswith(b"<?xml")
    assert b"<title>Libro de prueba</title>" in payload
    assert b"<imageUrl>https://example.test/image.png</imageUrl>" in payload


def test_minimal_xml_is_reduced_to_client_fields():
    payload = serialize_minimal([{
        "isbn": "9786070001001",
        "title": "Libro",
        "author": "Autora",
        "imageUrl": "image.png",
        "price": 100,
    }])

    assert b"<author>Autora</author>" in payload
    assert b"<price>" not in payload
