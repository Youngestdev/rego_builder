import psycopg2 as pg
from psycopg2.errors import (
    DuplicateSchema,
    DuplicateTable,
    DuplicateObject,
    UniqueViolation,
    InvalidTableDefinition,
)
import sqlparse
import os, sys
from pathlib import Path
from app.config.config import settings


ROOT_DIR = Path(__file__).parent.parent.parent
file_path = os.path.join(ROOT_DIR, "sql", "create_tables.sql")
f = os.path.join(ROOT_DIR, "sql", "test.sql")


class Database:
    def __init__(self):
        self.table_exists = 0
        self.conn = self.connect()
        self.create_tables()

    def connect(self):
        """
        Connect to database and return connection
        """

        try:
            conn = pg.connect(
                host=settings.HOST,
                port=settings.PORT,
                database=settings.DATABASE,
                user=settings.DB_USER,
                password=settings.PASSWORD,
            )
            conn.autocommit = True

            return conn
        except pg.OperationalError as e:
            sys.exit(1)

    def create_tables(self):
        """
        Create tables in database
        """
        # TODO: Handle error if table already exists

        with self.conn.cursor() as cursor:
            with open(file_path, "r", encoding="utf-8") as file:
                sql = sqlparse.split(sqlparse.format(file.read(), strip_comments=True))

            for statement in sql:
                try:
                    cursor.execute(statement)
                except (
                    DuplicateSchema,
                    DuplicateTable,
                    DuplicateObject,
                    UniqueViolation,
                    InvalidTableDefinition,
                ) as e:
                    continue

    def get_data(self, sql: str):
        cur = self.conn.cursor()
        cur.execute(sql)
        return cur.fetchall()