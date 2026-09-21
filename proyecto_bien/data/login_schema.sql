BEGIN;

CREATE SCHEMA IF NOT EXISTS library;

CREATE TABLE IF NOT EXISTS library.users (
    user_id BIGSERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    maternal_last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token VARCHAR(128) UNIQUE,
    email_verification_expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS library.auth_sessions (
    session_id BIGSERIAL PRIMARY KEY,
    session_token VARCHAR(128) NOT NULL UNIQUE,
    user_id BIGINT NOT NULL REFERENCES library.users(user_id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_users_email ON library.users (lower(email));
CREATE INDEX IF NOT EXISTS ix_auth_sessions_expiry ON library.auth_sessions (expires_at);

COMMIT;

-- El servicio necesita estos permisos además de los definidos para el catálogo:
-- GRANT USAGE ON SCHEMA library TO library_classifier_user;
-- GRANT SELECT, INSERT, UPDATE ON library.users, library.auth_sessions TO library_classifier_user;
-- GRANT USAGE, SELECT ON SEQUENCE library.users_user_id_seq, library.auth_sessions_session_id_seq TO library_classifier_user;
