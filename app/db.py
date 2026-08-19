from contextlib import contextmanager

import mysql.connector
from flask import current_app


@contextmanager
def get_conn(database: str | None = None):
    cfg = current_app.config
    conn = mysql.connector.connect(
        host=cfg["MYSQL_HOST"],
        port=cfg["MYSQL_PORT"],
        user=cfg["MYSQL_USER"],
        password=cfg["MYSQL_PASSWORD"],
        database=database,
        autocommit=False,
    )
    try:
        yield conn
    finally:
        conn.close()


def init_db(app):
    with app.app_context():
        cfg = app.config
        db_name = cfg["MYSQL_DATABASE"]

        with get_conn(database=None) as conn:
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            cursor.close()
            conn.commit()

        with get_conn(database=db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    email VARCHAR(255) UNIQUE,
                    phone VARCHAR(20) UNIQUE,
                    is_profile_complete TINYINT(1) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL
                ) ENGINE=InnoDB;
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    user_id BIGINT PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    address VARCHAR(255) NOT NULL,
                    city VARCHAR(80) NOT NULL,
                    state VARCHAR(80) NOT NULL,
                    pincode VARCHAR(10) NOT NULL,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB;
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS otp_codes (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    identifier VARCHAR(255) NOT NULL,
                    otp_hash VARCHAR(255) NOT NULL,
                    purpose ENUM('login','register') NOT NULL,
                    attempts INT NOT NULL DEFAULT 0,
                    expires_at DATETIME NOT NULL,
                    consumed_at DATETIME NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_identifier_purpose_created (identifier, purpose, created_at)
                ) ENGINE=InnoDB;
                """
            )
            cursor.close()
            conn.commit()
