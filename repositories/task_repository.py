import os
import psycopg
from psycopg.rows import dict_row


class TaskRepository:

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")

    def get_all(self):
        with psycopg.connect(
            self.database_url,
            row_factory=dict_row
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM tasks ORDER BY id"
                )
                return cursor.fetchall()

    def get_by_id(self, task_id):
        with psycopg.connect(
            self.database_url,
            row_factory=dict_row
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM tasks WHERE id = %s",
                    (task_id,)
                )
                return cursor.fetchone()

    def create(self, title):
        with psycopg.connect(
            self.database_url,
            row_factory=dict_row
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO tasks (title, done)
                    VALUES (%s, %s)
                    RETURNING *
                    """,
                    (title, False)
                )
                return cursor.fetchone()

    def update(self, task_id, title, done):
        with psycopg.connect(
            self.database_url,
            row_factory=dict_row
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE tasks
                    SET title = %s, done = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (title, done, task_id)
                )
                return cursor.fetchone()

    def delete(self, task_id):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM tasks WHERE id = %s",
                    (task_id,)
                )

                return cursor.rowcount > 0