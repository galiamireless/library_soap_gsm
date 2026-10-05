from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psycopg
from psycopg import errors


class UserAlreadyExistsError(Exception):
    pass


class LoginRepository:
    def __init__(self, db_config: dict[str, Any], schema: str = "library"):
        self.db_config = dict(db_config)
        self.schema = schema

    @contextmanager
    def transaction(self):
        with psycopg.connect(**self.db_config) as connection:
            with connection.cursor() as cursor:
                yield connection, cursor

    def check_health(self) -> bool:
        with self.transaction() as (_, cursor):
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)

    def create_user(self, data: dict[str, Any]) -> dict[str, Any]:
        try:
            with self.transaction() as (_, cursor):
                cursor.execute(f"""
                    INSERT INTO {self.schema}.users
                      (first_name, last_name, maternal_last_name, email, password_hash,
                       role_id, email_verification_token, email_verification_expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '24 hours')
                    RETURNING user_id, first_name, last_name, maternal_last_name, email,
                              email_verified, role_id, created_at
                """, (
                    data["first_name"], data["last_name"], data["maternal_last_name"],
                    data["email"], data["password_hash"], int(data.get("role_id", 3)),
                    data["verification_token"],
                ))
                return self._user_row(cursor.fetchone())
        except errors.UniqueViolation as error:
            raise UserAlreadyExistsError() from error

    def verify_email(self, token: str) -> dict[str, Any] | None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                UPDATE {self.schema}.users
                   SET email_verified = TRUE, email_verification_token = NULL,
                       email_verification_expires_at = NULL, updated_at = CURRENT_TIMESTAMP
                 WHERE email_verification_token = %s
                   AND email_verification_expires_at > CURRENT_TIMESTAMP
                RETURNING user_id, first_name, last_name, maternal_last_name, email,
                          email_verified, role_id, created_at
            """, (token,))
            row = cursor.fetchone()
            return self._user_row(row) if row else None

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                  SELECT user_id, first_name, last_name, maternal_last_name, email,
                      password_hash, email_verified, role_id, created_at
                  FROM {self.schema}.users WHERE email = %s
            """, (email,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(zip(("user_id", "first_name", "last_name", "maternal_last_name",
                             "email", "password_hash", "email_verified", "role_id", "created_at"), row))

    def list_users(self) -> list[dict[str, Any]]:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                SELECT user_id, first_name, last_name, maternal_last_name, email,
                       email_verified, role_id, created_at
                  FROM {self.schema}.users ORDER BY user_id
            """)
            return [self._user_row(row) for row in cursor.fetchall()]

    def get_user(self, user_id: int) -> dict[str, Any] | None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                SELECT user_id, first_name, last_name, maternal_last_name, email,
                       email_verified, role_id, created_at
                  FROM {self.schema}.users WHERE user_id = %s
            """, (user_id,))
            return self._user_row(cursor.fetchone())

    def update_user(self, user_id: int, data: dict[str, Any]) -> dict[str, Any] | None:
        fields = {
            "first_name": "first_name", "last_name": "last_name",
            "maternal_last_name": "maternal_last_name", "email": "email",
            "role_id": "role_id", "email_verified": "email_verified",
            "password_hash": "password_hash",
        }
        assignments = [f"{column} = %s" for key, column in fields.items() if key in data]
        values = [data[key] for key in fields if key in data]
        if not assignments:
            return self.get_user(user_id)
        assignments.append("updated_at = CURRENT_TIMESTAMP")
        try:
            with self.transaction() as (_, cursor):
                cursor.execute(f"""
                    UPDATE {self.schema}.users SET {', '.join(assignments)}
                     WHERE user_id = %s
                    RETURNING user_id, first_name, last_name, maternal_last_name, email,
                              email_verified, role_id, created_at
                """, (*values, user_id))
                return self._user_row(cursor.fetchone())
        except errors.UniqueViolation as error:
            raise UserAlreadyExistsError() from error

    def delete_user(self, user_id: int) -> bool:
        with self.transaction() as (_, cursor):
            cursor.execute(f"DELETE FROM {self.schema}.users WHERE user_id = %s", (user_id,))
            return cursor.rowcount > 0

    def create_session(self, user_id: int, token: str, expires_at: datetime) -> None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                INSERT INTO {self.schema}.auth_sessions (session_token, user_id, expires_at)
                VALUES (%s, %s, %s)
            """, (token, user_id, expires_at))

    def get_session_user(self, token: str) -> dict[str, Any] | None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                  SELECT u.user_id, u.first_name, u.last_name, u.maternal_last_name,
                      u.email, u.email_verified, u.role_id
                  FROM {self.schema}.auth_sessions s
                  JOIN {self.schema}.users u ON u.user_id = s.user_id
                 WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP
            """, (token,))
            row = cursor.fetchone()
            return dict(zip(("user_id", "first_name", "last_name", "maternal_last_name",
                             "email", "email_verified", "role_id"), row)) if row else None

    def delete_session(self, token: str) -> None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"DELETE FROM {self.schema}.auth_sessions WHERE session_token = %s", (token,))

    @staticmethod
    def _user_row(row):
        if not row:
            return None
        return dict(zip(("user_id", "first_name", "last_name", "maternal_last_name",
                 "email", "email_verified", "role_id", "created_at"), row))
