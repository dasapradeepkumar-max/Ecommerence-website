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
