from backend.models.database import Database
from datetime import datetime


class User:

    @classmethod
    def get_by_id(cls, user_id: int):
        return Database.query_one("SELECT * FROM users WHERE id = %s", (user_id,))

    @classmethod
    def get_by_identifier(cls, identifier: str):
        identifier = identifier.strip().lower()
        if "@" in identifier:
            return Database.query_one("SELECT * FROM users WHERE email = %s", (identifier,))
        else:
            return Database.query_one("SELECT * FROM users WHERE phone = %s", (identifier,))

    @classmethod
    def create_or_get(cls, identifier: str):
        identifier = identifier.strip().lower()
        user = cls.get_by_identifier(identifier)
        if user:
            # Update last login
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            Database.execute("UPDATE users SET last_login = %s WHERE id = %s", (now_str, user["id"]))
            return user, False

        # Create new user
        if "@" in identifier:
            user_id = Database.execute(
                "INSERT INTO users (email, is_profile_complete, last_login) VALUES (%s, 0, CURRENT_TIMESTAMP)",
                (identifier,)
            )
        else:
            user_id = Database.execute(
                "INSERT INTO users (phone, is_profile_complete, last_login) VALUES (%s, 0, CURRENT_TIMESTAMP)",
                (identifier,)
            )

        # Create empty cart & wishlist for user
        Database.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
        Database.execute("INSERT INTO wishlist (user_id) VALUES (%s)", (user_id,))

        user = cls.get_by_id(user_id)
        return user, True

    @classmethod
    def update_profile(cls, user_id: int, full_name: str, phone: str = None, email: str = None, address: str = None, city: str = None, state: str = None, pincode: str = None):
        user = cls.get_by_id(user_id)
        if not user:
            return False

        # Update user profile details
        Database.execute(
            """
            UPDATE users 
            SET full_name = %s, 
                phone = COALESCE(%s, phone), 
                email = COALESCE(%s, email), 
                is_profile_complete = 1 
            WHERE id = %s
            """,
            (full_name, phone, email, user_id)
        )

        # Add or update default address if provided
        if address and city and state and pincode:
            cls.save_address(
                user_id=user_id,
                full_name=full_name,
                phone=phone or user.get("phone") or "N/A",
                address_line=address,
                city=city,
                state=state,
                pincode=pincode,
                is_default=1
            )

        return True

    @classmethod
    def save_address(cls, user_id: int, full_name: str, phone: str, address_line: str, city: str, state: str, pincode: str, is_default: int = 1):
        if is_default:
            Database.execute("UPDATE addresses SET is_default = 0 WHERE user_id = %s", (user_id,))

        # Check existing default address
        existing = Database.query_one("SELECT id FROM addresses WHERE user_id = %s AND is_default = 1", (user_id,))
        if existing:
            Database.execute(
                """
                UPDATE addresses 
                SET full_name = %s, phone = %s, address_line = %s, city = %s, state = %s, pincode = %s 
                WHERE id = %s
                """,
                (full_name, phone, address_line, city, state, pincode, existing["id"])
            )
            return existing["id"]
        else:
            return Database.execute(
                """
                INSERT INTO addresses (user_id, full_name, phone, address_line, city, state, pincode, is_default)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, full_name, phone, address_line, city, state, pincode, is_default)
            )

    @classmethod
    def get_addresses(cls, user_id: int):
        return Database.query_all("SELECT * FROM addresses WHERE user_id = %s ORDER BY is_default DESC, id DESC", (user_id,))
