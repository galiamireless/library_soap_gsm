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
                       email_verification_token, email_verification_expires_at)
                    VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP + INTERVAL '24 hours')
                    RETURNING user_id, first_name, last_name, maternal_last_name, email,
                              email_verified, created_at
                """, tuple(data[key] for key in (
                    "first_name", "last_name", "maternal_last_name", "email",
                    "password_hash", "verification_token",
                )))
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
                          email_verified, created_at
            """, (token,))
            row = cursor.fetchone()
            return self._user_row(row) if row else None

    def find_by_email(self, email: str) -> dict[str, Any] | None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"""
                SELECT user_id, first_name, last_name, maternal_last_name, email,
                       password_hash, email_verified, created_at
                  FROM {self.schema}.users WHERE email = %s
            """, (email,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(zip(("user_id", "first_name", "last_name", "maternal_last_name",
                             "email", "password_hash", "email_verified", "created_at"), row))

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
                       u.email, u.email_verified
                  FROM {self.schema}.auth_sessions s
                  JOIN {self.schema}.users u ON u.user_id = s.user_id
                 WHERE s.session_token = %s AND s.expires_at > CURRENT_TIMESTAMP
            """, (token,))
            row = cursor.fetchone()
            return dict(zip(("user_id", "first_name", "last_name", "maternal_last_name",
                             "email", "email_verified"), row)) if row else None

    def delete_session(self, token: str) -> None:
        with self.transaction() as (_, cursor):
            cursor.execute(f"DELETE FROM {self.schema}.auth_sessions WHERE session_token = %s", (token,))

    @staticmethod
    def _user_row(row):
        if not row:
            return None
        return dict(zip(("user_id", "first_name", "last_name", "maternal_last_name",
                         "email", "email_verified", "created_at"), row))
