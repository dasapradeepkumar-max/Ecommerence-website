import werkzeug.security
from pathlib import Path
from backend.models.database import Database
from config.settings import Settings

SCHEMA_FILE = Settings.BASE_DIR / "database" / "schema.sql"
SEED_FILE = Settings.BASE_DIR / "database" / "seed.sql"


def init_and_seed_db():
    """Ensure database schema is created and populated with seed data."""
    Database.test_connection()
    
    # Read and execute schema
    if SCHEMA_FILE.exists():
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        try:
            Database.execute_script(schema_sql)
            print("[Seed Service] Schema initialized successfully.")
        except Exception as e:
            print(f"[Seed Service] Schema initialization notice: {e}")

    # Column migrations for existing databases
    try:
        Database.execute("ALTER TABLE orders ADD COLUMN shipping_date VARCHAR(60) NULL")
    except Exception:
        pass
    try:
        Database.execute("ALTER TABLE orders ADD COLUMN delivery_date VARCHAR(60) NULL")
    except Exception:
        pass
    try:
        Database.execute("ALTER TABLE users ADD COLUMN user_code VARCHAR(20) NULL")
    except Exception:
        pass
    try:
        Database.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_user_code ON users (user_code)")
    except Exception:
        pass
    try:
        Database.execute("ALTER TABLE users ADD COLUMN login_count INT NOT NULL DEFAULT 0")
    except Exception:
        pass
    try:
        Database.execute("""
            CREATE TABLE IF NOT EXISTS user_login_logs (
                id BIGINT PRIMARY KEY AUTO_INCREMENT,
                user_id BIGINT NOT NULL,
                login_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45) NULL,
                user_agent VARCHAR(255) NULL,
                CONSTRAINT fk_user_login_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
    except Exception:
        pass

    # Backfill user_code & login_count for existing users
    try:
        users_without_code = Database.query_all("SELECT id, last_login, login_count FROM users WHERE user_code IS NULL OR user_code = ''")
        for u in users_without_code:
            ucode = f"USR-{int(u['id']):06d}"
            curr_count = u.get("login_count") or 0
            if curr_count == 0:
                curr_count = 1
                # Check if login log exists
                log_cnt = Database.query_one("SELECT COUNT(*) as cnt FROM user_login_logs WHERE user_id = %s", (u["id"],))
                if not log_cnt or log_cnt.get("cnt", 0) == 0:
                    Database.execute("INSERT INTO user_login_logs (user_id, login_at) VALUES (%s, COALESCE(%s, CURRENT_TIMESTAMP))", (u["id"], u.get("last_login")))
            Database.execute("UPDATE users SET user_code = %s, login_count = %s WHERE id = %s", (ucode, curr_count, u["id"]))
    except Exception as e:
        print(f"[Seed Service] User backfill notice: {e}")

    # Check if products already exist
    existing_products = Database.query_one("SELECT COUNT(*) as cnt FROM products")
    if not existing_products or existing_products.get("cnt", 0) == 0:
        if SEED_FILE.exists():
            with open(SEED_FILE, "r", encoding="utf-8") as f:
                seed_sql = f.read()
            try:
                Database.execute_script(seed_sql)
                print("[Seed Service] Seed data inserted successfully.")
            except Exception as e:
                print(f"[Seed Service] Seed insertion notice: {e}")

    # Ensure admin user has valid password hash for 'admin123'
    hashed_pw = werkzeug.security.generate_password_hash("admin123")
    admin = Database.query_one("SELECT id FROM admin WHERE email = %s", ("admin@techtrend.com",))
    if admin:
        Database.execute("UPDATE admin SET password_hash = %s WHERE id = %s", (hashed_pw, admin["id"]))
    else:
        Database.execute(
            "INSERT INTO admin (name, email, password_hash) VALUES (%s, %s, %s)",
            ("TechTrend Administrator", "admin@techtrend.com", hashed_pw)
        )
    print("[Seed Service] Default admin verified (admin@techtrend.com / admin123)")
