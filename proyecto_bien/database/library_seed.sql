BEGIN;

INSERT INTO library.formats (name, description) VALUES
    ('Impreso', 'Edición física'),
    ('Digital', 'Edición para lectura electrónica')
ON CONFLICT (name) DO NOTHING;

INSERT INTO library.authors (name) VALUES
    ('Lucía Herrera'),
    ('Mateo Salas'),
    ('Nora Campos')
ON CONFLICT (name) DO NOTHING;

INSERT INTO library.genres (name) VALUES
    ('Tecnología'),
    ('Arquitectura'),
    ('Educación')
ON CONFLICT (name) DO NOTHING;

INSERT INTO library.books (isbn, title, publisher, publication_year, price, stock, description, format_id, format_type)
SELECT '9786070001001', 'Sistemas distribuidos para equipos pequeños', 'Ediciones Norte', 2025, 385.00, 7,
       'Guía práctica para separar responsabilidades entre servicios.', f.format_id, f.name
  FROM library.formats AS f WHERE f.name = 'Impreso'
ON CONFLICT (isbn) DO NOTHING;

INSERT INTO library.books (isbn, title, publisher, publication_year, price, stock, description, format_id, format_type)
SELECT '9786070001002', 'Contratos XML e interoperabilidad', 'Taller Editorial', 2026, 299.50, 12,
       'Ejemplos de contratos XML, validación y manejo de errores.', f.format_id, f.name
  FROM library.formats AS f WHERE f.name = 'Digital'
ON CONFLICT (isbn) DO NOTHING;

INSERT INTO library.book_authors (isbn, author_id, author_order)
SELECT b.isbn, a.author_id, 1
  FROM library.books b CROSS JOIN library.authors a
 WHERE b.isbn = '9786070001001' AND a.name = 'Lucía Herrera'
ON CONFLICT DO NOTHING;

INSERT INTO library.book_authors (isbn, author_id, author_order)
SELECT b.isbn, a.author_id, 1
  FROM library.books b CROSS JOIN library.authors a
 WHERE b.isbn = '9786070001002' AND a.name = 'Mateo Salas'
ON CONFLICT DO NOTHING;

INSERT INTO library.book_genres (isbn, genre_id)
SELECT b.isbn, g.genre_id
  FROM library.books b CROSS JOIN library.genres g
 WHERE b.isbn = '9786070001001' AND g.name IN ('Tecnología', 'Arquitectura')
ON CONFLICT DO NOTHING;

INSERT INTO library.book_genres (isbn, genre_id)
SELECT b.isbn, g.genre_id
  FROM library.books b CROSS JOIN library.genres g
 WHERE b.isbn = '9786070001002' AND g.name IN ('Tecnología', 'Educación')
ON CONFLICT DO NOTHING;

INSERT INTO library.book_images (isbn, image_url, is_primary)
VALUES
    ('9786070001001', 'https://images.example.test/distribuidos.png', TRUE),
    ('9786070001002', 'https://images.example.test/xml.png', TRUE)
ON CONFLICT DO NOTHING;

INSERT INTO library.concepts (name) VALUES
    ('IaaS'), ('PaaS'), ('SaaS'), ('FaaS')
ON CONFLICT (name) DO NOTHING;

INSERT INTO library.book_concepts (concept_id, isbn, definition)
SELECT c.concept_id, b.isbn,
       CASE c.name
           WHEN 'IaaS' THEN 'Infraestructura disponible como servicio.'
           WHEN 'PaaS' THEN 'Plataforma administrada para ejecutar aplicaciones.'
           WHEN 'SaaS' THEN 'Software consumido como servicio.'
           WHEN 'FaaS' THEN 'Funciones ejecutadas bajo demanda.'
       END
  FROM library.concepts c
  CROSS JOIN library.books b
 WHERE b.isbn IN ('9786070001001', '9786070001002')
ON CONFLICT DO NOTHING;

COMMIT;
