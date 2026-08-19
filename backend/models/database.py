import os
import sqlite3
import re
from pathlib import Path
from contextlib import contextmanager
import mysql.connector
from config.settings import Settings

DB_FILE = Settings.BASE_DIR / "ecommerce.db"


class Database:
    """Unified Database connection manager supporting MySQL with automatic SQLite fallback."""
    
    _use_sqlite = False

    @classmethod
    def test_connection(cls):
        """Test MySQL connection; fallback to SQLite if connection fails."""
        try:
            conn = mysql.connector.connect(
                host=Settings.MYSQL_HOST,
                port=Settings.MYSQL_PORT,
                user=Settings.MYSQL_USER,
                password=Settings.MYSQL_PASSWORD,
                connection_timeout=3
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Settings.MYSQL_DATABASE}")
            cursor.close()
            conn.close()
            cls._use_sqlite = False
            print("[Database] Successfully connected to MySQL database.")
            return "mysql"
        except Exception as e:
            cls._use_sqlite = True
            print(f"[Database] MySQL connection unavailable ({e}). Operating in SQLite Mode: {DB_FILE}")
            return "sqlite"

    @classmethod
    @contextmanager
    def get_connection(cls):
        if not cls._use_sqlite:
            try:
                conn = mysql.connector.connect(
                    host=Settings.MYSQL_HOST,
                    port=Settings.MYSQL_PORT,
                    user=Settings.MYSQL_USER,
                    password=Settings.MYSQL_PASSWORD,
                    database=Settings.MYSQL_DATABASE,
                    autocommit=False
                )
                try:
                    yield conn
                finally:
                    conn.close()
                return
            except Exception as e:
                print(f"[Database] MySQL error ({e}), switching to SQLite mode.")
                cls._use_sqlite = True

        # SQLite Mode
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def convert_query(cls, sql, params=()):
        """Format parameters for SQLite (%s to ?) or MySQL."""
        if cls._use_sqlite:
            sql = sql.replace("%s", "?")
            sql = sql.replace("BIGINT PRIMARY KEY AUTO_INCREMENT", "INTEGER PRIMARY KEY AUTOINCREMENT")
            sql = sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
            sql = sql.replace("ENGINE=InnoDB", "")
            sql = sql.replace("DEFAULT CHARSET=utf8mb4", "")
            sql = re.sub(r'TINYINT\(\d+\)', 'INTEGER', sql, flags=re.IGNORECASE)
            sql = re.sub(r'ENUM\([^)]+\)', 'TEXT', sql, flags=re.IGNORECASE)
        return sql, params

    @classmethod
    def query_all(cls, sql, params=()):
        sql, params = cls.convert_query(sql, params)
        with cls.get_connection() as conn:
            if cls._use_sqlite:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(sql, params)
                result = cursor.fetchall()
                cursor.close()
                return result

    @classmethod
    def query_one(cls, sql, params=()):
        sql, params = cls.convert_query(sql, params)
        with cls.get_connection() as conn:
            if cls._use_sqlite:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(sql, params)
                result = cursor.fetchone()
                cursor.close()
                return result

    @classmethod
    def execute(cls, sql, params=()):
        sql, params = cls.convert_query(sql, params)
        with cls.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            last_id = cursor.lastrowid
            conn.commit()
            if not cls._use_sqlite:
                cursor.close()
            return last_id

    @classmethod
    def execute_script(cls, sql_script):
        with cls.get_connection() as conn:
            if cls._use_sqlite:
                s = sql_script
                s = s.replace("BIGINT PRIMARY KEY AUTO_INCREMENT", "INTEGER PRIMARY KEY AUTOINCREMENT")
                s = s.replace("AUTO_INCREMENT", "AUTOINCREMENT")
                s = s.replace("ENGINE=InnoDB", "")
                s = s.replace("DEFAULT CHARSET=utf8mb4", "")
                s = re.sub(r'TINYINT\(\d+\)', 'INTEGER', s, flags=re.IGNORECASE)
                s = re.sub(r'ENUM\([^)]+\)', 'TEXT', s, flags=re.IGNORECASE)
                
                # Split statements by semicolon and execute non-empty statements
                statements = s.split(';')
                cursor = conn.cursor()
                for stmt in statements:
                    stmt = stmt.strip()
                    if stmt:
                        try:
                            cursor.execute(stmt)
                        except Exception as ex:
                            # Ignore INDEX or CONSTRAINT warnings if table doesn't support
                            pass
                conn.commit()
            else:
                cursor = conn.cursor()
                for statement in sql_script.split(';'):
                    stmt = statement.strip()
                    if stmt:
                        cursor.execute(stmt)
                conn.commit()
                cursor.close()
