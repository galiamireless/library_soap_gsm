BEGIN;

CREATE SCHEMA IF NOT EXISTS library;

CREATE TABLE IF NOT EXISTS library.formats (
    format_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS library.authors (
    author_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(180) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS library.genres (
    genre_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS library.books (
    isbn VARCHAR(20) PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    publisher VARCHAR(180),
    publication_year INTEGER CHECK (publication_year BETWEEN 1450 AND 9999),
    price NUMERIC(12, 2) CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    description TEXT,
    format_id BIGINT REFERENCES library.formats(format_id),
    format_type VARCHAR(80),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS library.book_authors (
    isbn VARCHAR(20) NOT NULL REFERENCES library.books(isbn) ON DELETE CASCADE,
    author_id BIGINT NOT NULL REFERENCES library.authors(author_id),
    author_order INTEGER NOT NULL DEFAULT 1 CHECK (author_order > 0),
    PRIMARY KEY (isbn, author_id)
);

CREATE TABLE IF NOT EXISTS library.book_genres (
    isbn VARCHAR(20) NOT NULL REFERENCES library.books(isbn) ON DELETE CASCADE,
    genre_id BIGINT NOT NULL REFERENCES library.genres(genre_id),
    PRIMARY KEY (isbn, genre_id)
);

CREATE TABLE IF NOT EXISTS library.book_images (
    image_id BIGSERIAL PRIMARY KEY,
    isbn VARCHAR(20) NOT NULL REFERENCES library.books(isbn) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (isbn, image_url)
);

CREATE TABLE IF NOT EXISTS library.concepts (
    concept_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS library.book_concepts (
    concept_id BIGINT NOT NULL REFERENCES library.concepts(concept_id) ON DELETE CASCADE,
    isbn VARCHAR(20) NOT NULL REFERENCES library.books(isbn) ON DELETE CASCADE,
    definition TEXT,
    PRIMARY KEY (concept_id, isbn)
);

CREATE TABLE IF NOT EXISTS library.clasificadores (
    clasificador_id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    correo VARCHAR(254) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS library.clasificaciones_cloud (
    classification_id BIGSERIAL PRIMARY KEY,
    concept_id BIGINT NOT NULL,
    isbn VARCHAR(20) NOT NULL,
    clasificador_id BIGINT NOT NULL REFERENCES library.clasificadores(clasificador_id),
    modelo_cloud VARCHAR(4) NOT NULL CHECK (modelo_cloud IN ('IaaS', 'PaaS', 'SaaS', 'FaaS')),
    classified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id, isbn) REFERENCES library.book_concepts(concept_id, isbn),
    UNIQUE (clasificador_id, concept_id, isbn)
);

CREATE TABLE IF NOT EXISTS library.clientes_servidos (
    cliente_servido_id BIGSERIAL PRIMARY KEY,
    tipo_cliente VARCHAR(40) NOT NULL,
    identificador VARCHAR(150) NOT NULL,
    peticiones_atendidas INTEGER NOT NULL DEFAULT 1 CHECK (peticiones_atendidas > 0),
    primera_peticion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultima_peticion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tipo_cliente, identificador)
);

CREATE INDEX IF NOT EXISTS ix_books_title ON library.books (lower(title));
CREATE INDEX IF NOT EXISTS ix_book_authors_author ON library.book_authors (author_id);
CREATE INDEX IF NOT EXISTS ix_book_genres_genre ON library.book_genres (genre_id);
CREATE INDEX IF NOT EXISTS ix_book_concepts_book ON library.book_concepts (isbn);
CREATE INDEX IF NOT EXISTS ix_classifications_classifier ON library.clasificaciones_cloud (clasificador_id);
CREATE INDEX IF NOT EXISTS ix_classifications_model ON library.clasificaciones_cloud (modelo_cloud);

COMMIT;

-- En producción, conceder solo los permisos del esquema library al usuario del servicio:
-- GRANT USAGE ON SCHEMA library TO library_classifier_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA library TO library_classifier_user;
-- GRANT INSERT, UPDATE ON library.clasificadores, library.clasificaciones_cloud, library.clientes_servidos TO library_classifier_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA library TO library_classifier_user;
