import logging
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.errors import UniqueViolation

LOGGER = logging.getLogger(__name__)


class DuplicateClassificationError(Exception):
    pass


class ConceptNotFoundError(Exception):
    pass


class DatabaseRepository:
    def __init__(self, config: dict, connection_factory=None):
        self.config = config
        self.connection_factory = connection_factory or psycopg.connect

    @contextmanager
    def transaction(self):
        with self.connection_factory(**self.config) as connection:
            with connection.cursor() as cursor:
                yield connection, cursor

    def list_pending_concepts(self, client_type: str, client_id: str) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute(
                """
                SELECT bc.concept_id, bc.isbn, c.name, bc.definition, b.title,
                       COALESCE(string_agg(DISTINCT g.name, ', ' ORDER BY g.name), '') AS categories
                FROM book_concepts bc
                JOIN concepts c ON c.concept_id = bc.concept_id
                JOIN books b ON b.isbn = bc.isbn
                LEFT JOIN book_genres bg ON bg.isbn = b.isbn
                LEFT JOIN genres g ON g.genre_id = bg.genre_id
                LEFT JOIN clasificaciones_cloud cc
                  ON cc.concept_id = bc.concept_id
                 AND cc.isbn = bc.isbn
                WHERE cc.classification_id IS NULL
                GROUP BY bc.concept_id, bc.isbn, c.name, bc.definition, b.title
                ORDER BY b.title, c.name
                """
            )
            rows = cursor.fetchall()
            self._record_client(cursor, client_type, client_id)
            return [
                {"conceptId": row[0], "isbn": row[1], "concept": row[2],
                 "definition": row[3], "title": row[4], "category": row[5]}
                for row in rows
            ]

    def register_classification(self, data: dict[str, Any]) -> dict[str, Any]:
        with self.transaction() as (connection, cursor):
            cursor.execute(
                "SELECT 1 FROM book_concepts WHERE concept_id = %s AND isbn = %s",
                (data["concept_id"], data["isbn"]),
            )
            if cursor.fetchone() is None:
                raise ConceptNotFoundError()

            cursor.execute(
                """
                INSERT INTO clasificadores (nombre, apellidos, correo)
                VALUES (%s, %s, %s)
                ON CONFLICT (correo) DO UPDATE SET
                  nombre = EXCLUDED.nombre, apellidos = EXCLUDED.apellidos
                RETURNING clasificador_id
                """,
                (data["first_name"], data["last_name"], data["email"]),
            )
            classifier_id = cursor.fetchone()[0]
            try:
                cursor.execute(
                    """
                    INSERT INTO clasificaciones_cloud
                      (concept_id, isbn, clasificador_id, modelo_cloud)
                    VALUES (%s, %s, %s, %s)
                    RETURNING classification_id, classified_at
                    """,
                    (data["concept_id"], data["isbn"], classifier_id, data["model"]),
                )
                result = cursor.fetchone()
            except UniqueViolation as error:
                connection.rollback()
                raise DuplicateClassificationError() from error

            self._record_client(cursor, data["client_type"], data["client_id"])
            return {"classificationId": result[0], "classifiedAt": result[1].isoformat()}

    def get_user_progress(self, email: str, client_type: str, client_id: str) -> dict[str, int | str]:
        with self.transaction() as (_, cursor):
            cursor.execute(
                """
                SELECT COUNT(*) FILTER (WHERE cc.classification_id IS NOT NULL),
                       COUNT(*) FILTER (WHERE cc.classification_id IS NULL)
                FROM book_concepts bc
                LEFT JOIN clasificadores cl ON cl.correo = %s
                LEFT JOIN clasificaciones_cloud cc
                  ON cc.concept_id = bc.concept_id AND cc.isbn = bc.isbn
                 AND cc.clasificador_id = cl.clasificador_id
                """,
                (email,),
            )
            classified, pending = cursor.fetchone()
            self._record_client(cursor, client_type, client_id)
            return {"email": email, "classified": classified, "pending": pending}

    def get_statistics(self, client_type: str, client_id: str) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute(
                """
                SELECT modelo_cloud, COUNT(*)
                FROM clasificaciones_cloud
                GROUP BY modelo_cloud
                ORDER BY modelo_cloud
                """
            )
            result = [{"model": row[0], "count": row[1]} for row in cursor.fetchall()]
            self._record_client(cursor, client_type, client_id)
            return result

    def list_books(self, isbn: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT b.isbn, b.title,
                   COALESCE(string_agg(DISTINCT a.name, ', ' ORDER BY a.name), '') AS author,
                   b.publisher, b.publication_year, b.price, b.stock, b.description,
                   COALESCE(f.name, b.format_type) AS format,
                   COALESCE(string_agg(DISTINCT bi.image_url, ', ' ORDER BY bi.image_url), '') AS image_url
            FROM books b
            LEFT JOIN book_authors ba ON ba.isbn = b.isbn
            LEFT JOIN authors a ON a.author_id = ba.author_id
            LEFT JOIN formats f ON f.format_id = b.format_id
            LEFT JOIN book_images bi ON bi.isbn = b.isbn
        """
        parameters = ()
        if isbn:
            query += " WHERE b.isbn = %s"
            parameters = (isbn,)
        query += " GROUP BY b.isbn, b.title, b.publisher, b.publication_year, b.price, b.stock, b.description, f.name, b.format_type ORDER BY b.title"
        with self.transaction() as (_, cursor):
            cursor.execute(query, parameters)
            columns = ("isbn", "title", "author", "publisher", "publicationYear", "price",
                       "stock", "description", "format", "imageUrl")
            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def list_cloud_concepts(self) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute(
                """
                SELECT c.concept_id, c.name, bc.definition, b.isbn, b.title,
                       COALESCE(string_agg(DISTINCT g.name, ', ' ORDER BY g.name), '') AS categories
                FROM concepts c
                JOIN book_concepts bc ON bc.concept_id = c.concept_id
                JOIN books b ON b.isbn = bc.isbn
                LEFT JOIN book_genres bg ON bg.isbn = b.isbn
                LEFT JOIN genres g ON g.genre_id = bg.genre_id
                GROUP BY c.concept_id, c.name, bc.definition, b.isbn, b.title
                ORDER BY c.name, b.title
                """
            )
            return [
                {"conceptId": row[0], "concept": row[1], "definition": row[2],
                 "isbn": row[3], "title": row[4], "categories": row[5]}
                for row in cursor.fetchall()
            ]

    def check_health(self) -> bool:
        with self.transaction() as (_, cursor):
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)

    @staticmethod
    def _record_client(cursor, client_type: str, client_id: str) -> None:
        cursor.execute(
            """
            INSERT INTO clientes_servidos (tipo_cliente, identificador, peticiones_atendidas)
            VALUES (%s, %s, 1)
            ON CONFLICT (tipo_cliente, identificador) DO UPDATE
              SET peticiones_atendidas = clientes_servidos.peticiones_atendidas + 1,
                  ultima_peticion = CURRENT_TIMESTAMP
            """,
            (client_type, client_id),
        )
