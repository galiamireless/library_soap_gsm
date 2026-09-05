BEGIN;

CREATE TABLE IF NOT EXISTS clasificadores (
    clasificador_id BIGSERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    apellidos VARCHAR(150) NOT NULL,
    correo VARCHAR(254) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clasificaciones_cloud (
    classification_id BIGSERIAL PRIMARY KEY,
    concept_id INTEGER NOT NULL REFERENCES concepts(concept_id),
    isbn VARCHAR(20) NOT NULL REFERENCES books(isbn),
    clasificador_id BIGINT NOT NULL REFERENCES clasificadores(clasificador_id),
    modelo_cloud VARCHAR(4) NOT NULL CHECK (modelo_cloud IN ('IaaS', 'PaaS', 'SaaS', 'FaaS')),
    classified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (clasificador_id, concept_id),
    UNIQUE (clasificador_id, concept_id, isbn)
);

CREATE TABLE IF NOT EXISTS clientes_servidos (
    cliente_servido_id BIGSERIAL PRIMARY KEY,
    tipo_cliente VARCHAR(40) NOT NULL,
    identificador VARCHAR(150) NOT NULL,
    peticiones_atendidas INTEGER NOT NULL DEFAULT 1 CHECK (peticiones_atendidas > 0),
    primera_peticion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ultima_peticion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tipo_cliente, identificador)
);

CREATE INDEX IF NOT EXISTS idx_clasificaciones_concepto ON clasificaciones_cloud (concept_id, isbn);
CREATE INDEX IF NOT EXISTS idx_clasificaciones_modelo ON clasificaciones_cloud (modelo_cloud);
CREATE INDEX IF NOT EXISTS idx_clientes_tipo ON clientes_servidos (tipo_cliente);

COMMENT ON TABLE clasificadores IS 'Identidades propias del cliente SOAP; no reutiliza users del monolito.';
COMMENT ON TABLE clasificaciones_cloud IS 'Clasificaciones agregadas por el módulo SOAP.';
COMMENT ON TABLE clientes_servidos IS 'Contador de peticiones por aplicación cliente.';

COMMIT;

-- Ejecutar como administrador una vez y usar solo este rol en la aplicación:
-- CREATE ROLE library_soap_user LOGIN PASSWORD 'configure-outside-source-control';
-- GRANT CONNECT ON DATABASE gsm_library_db TO library_soap_user;
-- GRANT USAGE ON SCHEMA public TO library_soap_user;
-- GRANT SELECT ON books, concepts, genres, book_genres, book_concepts TO library_soap_user;
-- GRANT SELECT, INSERT, UPDATE ON clasificadores, clasificaciones_cloud, clientes_servidos TO library_soap_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO library_soap_user;
