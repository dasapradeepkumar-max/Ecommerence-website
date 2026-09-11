from backend.models.database import Database
from datetime import datetime


class User:

    @classmethod
    def get_by_id(cls, user_id: int):
        user = Database.query_one("SELECT * FROM users WHERE id = %s", (user_id,))
        if user and not user.get("user_code"):
            user["user_code"] = f"USR-{user['id']:06d}"
        return user

    @classmethod
    def get_by_identifier(cls, identifier: str):
        identifier = identifier.strip().lower()
        if "@" in identifier:
            user = Database.query_one("SELECT * FROM users WHERE email = %s", (identifier,))
        else:
            user = Database.query_one("SELECT * FROM users WHERE phone = %s", (identifier,))
        if user and not user.get("user_code"):
            user["user_code"] = f"USR-{user['id']:06d}"
        return user

    @classmethod
    def record_login(cls, user_id: int, ip_address: str = None, user_agent: str = None):
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = Database.query_one("SELECT * FROM users WHERE id = %s", (user_id,))
        if not user:
            return

        user_code = user.get("user_code") or f"USR-{user_id:06d}"
        new_count = (user.get("login_count") or 0) + 1

        Database.execute(
            "UPDATE users SET user_code = %s, login_count = %s, last_login = %s WHERE id = %s",
            (user_code, new_count, now_str, user_id)
        )
        Database.execute(
            "INSERT INTO user_login_logs (user_id, login_at, ip_address, user_agent) VALUES (%s, %s, %s, %s)",
            (user_id, now_str, ip_address, user_agent)
        )

    @classmethod
    def create_or_get(cls, identifier: str, ip_address: str = None, user_agent: str = None):
        identifier = identifier.strip().lower()
        user = cls.get_by_identifier(identifier)
        if user:
            cls.record_login(user["id"], ip_address=ip_address, user_agent=user_agent)
            return cls.get_by_id(user["id"]), False

        # Create new user
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "@" in identifier:
            user_id = Database.execute(
                "INSERT INTO users (email, is_profile_complete, login_count, last_login) VALUES (%s, 0, 1, %s)",
                (identifier, now_str)
            )
        else:
            user_id = Database.execute(
                "INSERT INTO users (phone, is_profile_complete, login_count, last_login) VALUES (%s, 0, 1, %s)",
                (identifier, now_str)
            )

        user_code = f"USR-{user_id:06d}"
        Database.execute("UPDATE users SET user_code = %s WHERE id = %s", (user_code, user_id))
        Database.execute(
            "INSERT INTO user_login_logs (user_id, login_at, ip_address, user_agent) VALUES (%s, %s, %s, %s)",
            (user_id, now_str, ip_address, user_agent)
        )

        # Create empty cart & wishlist for user
        Database.execute("INSERT INTO cart (user_id) VALUES (%s)", (user_id,))
        Database.execute("INSERT INTO wishlist (user_id) VALUES (%s)", (user_id,))

        user = cls.get_by_id(user_id)
        return user, True

    @classmethod
    def get_login_history(cls, user_id: int):
        return Database.query_all(
            """
            SELECT id, user_id, login_at, ip_address, user_agent
            FROM user_login_logs
            WHERE user_id = %s
            ORDER BY login_at DESC, id DESC
            """,
            (user_id,)
        )

    @classmethod
    def get_customer_detail(cls, user_id: int):
        user = cls.get_by_id(user_id)
        if not user:
            return None

        if not user.get("user_code"):
            user["user_code"] = f"USR-{user['id']:06d}"

        login_history = cls.get_login_history(user_id)
        addresses = cls.get_addresses(user_id)
        from backend.models.order import Order
        orders = Order.get_user_orders(user_id)

        total_spent = sum(float(o["total_amount"]) for o in orders if o.get("status") != "Cancelled")

        return {
            "user": user,
            "addresses": addresses,
            "login_count": user.get("login_count", len(login_history)),
            "login_history": login_history,
            "total_orders": len(orders),
            "total_spent": round(total_spent, 2),
            "orders": orders
        }

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
