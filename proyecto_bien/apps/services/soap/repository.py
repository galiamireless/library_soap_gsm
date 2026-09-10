"""PostgreSQL access for the independent library schema."""

from __future__ import annotations

import logging
import threading
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.errors import UniqueViolation


LOGGER = logging.getLogger(__name__)


class DuplicateClassificationError(Exception):
    """The same classifier cannot classify the same book concept twice."""


class ConceptNotFoundError(Exception):
    """The requested concept/book relation does not exist."""


class LibraryRepository:
    def __init__(self, db_config: dict[str, Any], pool=None, pool_settings: dict[str, Any] | None = None):
        self.db_config = dict(db_config)
        self.pool = pool or self._create_pool(pool_settings)
        self._pool_opened = False
        self._pool_lock = threading.Lock()

    @staticmethod
    def _create_pool(pool_settings):
        if pool_settings is None:
            return None
        from psycopg_pool import ConnectionPool

        options = dict(pool_settings)
        db_config = options.pop("db_config", {})
        return ConnectionPool(
            conninfo="",
            kwargs=db_config,
            min_size=options["min_size"],
            max_size=options["max_size"],
            timeout=options["timeout"],
            open=False,
        )

    @contextmanager
    def transaction(self):
        if self.pool is not None:
            with self._pool_lock:
                if not self._pool_opened:
                    self.pool.open(wait=False)
                    self._pool_opened = True
            with self.pool.connection() as connection:
                with connection.cursor() as cursor:
                    yield connection, cursor
            return

        with psycopg.connect(**self.db_config) as connection:
            with connection.cursor() as cursor:
                yield connection, cursor

    def close(self) -> None:
        with self._pool_lock:
            if self.pool is not None and self._pool_opened:
                self.pool.close()
                self._pool_opened = False

    def check_health(self) -> bool:
        with self.transaction() as (_, cursor):
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)

    def list_books(self, isbn: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT b.isbn, b.title,
                   COALESCE(string_agg(DISTINCT a.name, ', ' ORDER BY a.name), '') AS author,
                   b.publication_year, b.publisher, b.price, b.stock, b.description,
                   COALESCE(f.name, b.format_type) AS format,
                   COALESCE(string_agg(DISTINCT bi.image_url, ', ' ORDER BY bi.image_url), '') AS image_url
              FROM library.books AS b
              LEFT JOIN library.book_authors AS ba ON ba.isbn = b.isbn
              LEFT JOIN library.authors AS a ON a.author_id = ba.author_id
              LEFT JOIN library.formats AS f ON f.format_id = b.format_id
              LEFT JOIN library.book_images AS bi ON bi.isbn = b.isbn
        """
        params: tuple[Any, ...] = ()
        if isbn:
            query += " WHERE b.isbn = %s"
            params = (isbn,)
        query += """
            GROUP BY b.isbn, b.title, b.publication_year, b.publisher, b.price,
                     b.stock, b.description, f.name, b.format_type
            ORDER BY b.title
        """
        with self.transaction() as (_, cursor):
            cursor.execute(query, params)
            columns = (
                "isbn", "title", "author", "publicationYear", "publisher", "price",
                "stock", "description", "format", "imageUrl",
            )
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def list_minimal_books(self) -> list[dict[str, Any]]:
        return self.list_books()

    def list_cloud_concepts(self) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute("""
                SELECT c.concept_id, c.name, bc.definition, b.isbn, b.title,
                       COALESCE(string_agg(DISTINCT g.name, ', ' ORDER BY g.name), '') AS categories
                  FROM library.concepts AS c
                  JOIN library.book_concepts AS bc ON bc.concept_id = c.concept_id
                  JOIN library.books AS b ON b.isbn = bc.isbn
                  LEFT JOIN library.book_genres AS bg ON bg.isbn = b.isbn
                  LEFT JOIN library.genres AS g ON g.genre_id = bg.genre_id
                 GROUP BY c.concept_id, c.name, bc.definition, b.isbn, b.title
                 ORDER BY c.name, b.title
            """)
            return [
                {
                    "conceptId": row[0], "concept": row[1], "definition": row[2],
                    "isbn": row[3], "title": row[4], "categories": row[5],
                }
                for row in cursor.fetchall()
            ]

    def list_pending_concepts(self, client_type: str, client_id: str) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute("""
                SELECT bc.concept_id, bc.isbn, c.name, bc.definition, b.title,
                       COALESCE(string_agg(DISTINCT g.name, ', ' ORDER BY g.name), '') AS categories
                  FROM library.book_concepts AS bc
                  JOIN library.concepts AS c ON c.concept_id = bc.concept_id
                  JOIN library.books AS b ON b.isbn = bc.isbn
                  LEFT JOIN library.book_genres AS bg ON bg.isbn = b.isbn
                  LEFT JOIN library.genres AS g ON g.genre_id = bg.genre_id
                  LEFT JOIN library.clasificaciones_cloud AS cc
                    ON cc.concept_id = bc.concept_id AND cc.isbn = bc.isbn
                 WHERE cc.classification_id IS NULL
                 GROUP BY bc.concept_id, bc.isbn, c.name, bc.definition, b.title
                 ORDER BY b.title, c.name
            """)
            rows = cursor.fetchall()
            self._record_client(cursor, client_type, client_id)
            return [
                {
                    "conceptId": row[0], "isbn": row[1], "concept": row[2],
                    "definition": row[3], "title": row[4], "category": row[5],
                }
                for row in rows
            ]

    def register_classification(self, data: dict[str, Any]) -> dict[str, Any]:
        with self.transaction() as (connection, cursor):
            cursor.execute(
                "SELECT 1 FROM library.book_concepts WHERE concept_id = %s AND isbn = %s",
                (data["concept_id"], data["isbn"]),
            )
            if cursor.fetchone() is None:
                raise ConceptNotFoundError()

            cursor.execute("""
                INSERT INTO library.clasificadores (nombre, apellidos, correo)
                VALUES (%s, %s, %s)
                ON CONFLICT (correo) DO UPDATE SET
                  nombre = EXCLUDED.nombre, apellidos = EXCLUDED.apellidos,
                  updated_at = CURRENT_TIMESTAMP
                RETURNING clasificador_id
            """, (data["first_name"], data["last_name"], data["email"]))
            classifier_id = cursor.fetchone()[0]
            try:
                cursor.execute("""
                    INSERT INTO library.clasificaciones_cloud
                      (concept_id, isbn, clasificador_id, modelo_cloud)
                    VALUES (%s, %s, %s, %s)
                    RETURNING classification_id, classified_at
                """, (data["concept_id"], data["isbn"], classifier_id, data["model"]))
                result = cursor.fetchone()
            except UniqueViolation as error:
                connection.rollback()
                raise DuplicateClassificationError() from error

            self._record_client(cursor, data["client_type"], data["client_id"])
            return {"classificationId": result[0], "classifiedAt": result[1].isoformat()}

    def get_user_progress(self, email: str, client_type: str, client_id: str) -> dict[str, Any]:
        with self.transaction() as (_, cursor):
            cursor.execute("""
                SELECT COUNT(*) FILTER (WHERE cc.classification_id IS NOT NULL),
                       COUNT(*) FILTER (WHERE cc.classification_id IS NULL)
                  FROM library.book_concepts AS bc
                  LEFT JOIN library.clasificadores AS cl ON cl.correo = %s
                  LEFT JOIN library.clasificaciones_cloud AS cc
                    ON cc.concept_id = bc.concept_id AND cc.isbn = bc.isbn
                   AND cc.clasificador_id = cl.clasificador_id
            """, (email,))
            classified, pending = cursor.fetchone()
            self._record_client(cursor, client_type, client_id)
            return {"email": email, "classified": classified, "pending": pending}

    def get_statistics(self, client_type: str, client_id: str) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute("""
                SELECT modelo_cloud, COUNT(*)
                  FROM library.clasificaciones_cloud
                 GROUP BY modelo_cloud ORDER BY modelo_cloud
            """)
            result = [{"model": row[0], "count": row[1]} for row in cursor.fetchall()]
            self._record_client(cursor, client_type, client_id)
            return result

    @staticmethod
    def _record_client(cursor, client_type: str, client_id: str) -> None:
        cursor.execute("""
            INSERT INTO library.clientes_servidos (tipo_cliente, identificador, peticiones_atendidas)
            VALUES (%s, %s, 1)
            ON CONFLICT (tipo_cliente, identificador) DO UPDATE SET
              peticiones_atendidas = library.clientes_servidos.peticiones_atendidas + 1,
              ultima_peticion = CURRENT_TIMESTAMP
        """, (client_type, client_id))
