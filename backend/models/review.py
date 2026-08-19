from backend.models.database import Database


class Review:

    @classmethod
    def get_by_product(cls, product_id: int):
        return Database.query_all(
            """
            SELECT r.*, u.full_name, u.email
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = %s
            ORDER BY r.id DESC
            """,
            (product_id,)
        )

    @classmethod
    def save_review(cls, user_id: int, product_id: int, rating: int, review_text: str):
        existing = Database.query_one(
            "SELECT id FROM reviews WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        if existing:
            Database.execute(
                "UPDATE reviews SET rating = %s, review_text = %s WHERE id = %s",
                (rating, review_text, existing["id"])
            )
        else:
            Database.execute(
                "INSERT INTO reviews (user_id, product_id, rating, review_text) VALUES (%s, %s, %s, %s)",
                (user_id, product_id, rating, review_text)
            )

        # Recalculate average rating & review count for product
        stats = Database.query_one(
            "SELECT AVG(rating) as avg_r, COUNT(*) as cnt FROM reviews WHERE product_id = %s",
            (product_id,)
        )
        avg_r = round(float(stats["avg_r"]), 2) if stats and stats.get("avg_r") else rating
        cnt = int(stats["cnt"]) if stats and stats.get("cnt") else 1

        Database.execute(
            "UPDATE products SET avg_rating = %s, review_count = %s WHERE id = %s",
            (avg_r, cnt, product_id)
        )
        return True

    @classmethod
    def delete_review(cls, review_id: int, user_id: int = None):
        sql = "DELETE FROM reviews WHERE id = %s"
        params = [review_id]
        if user_id:
            sql += " AND user_id = %s"
            params.append(user_id)

        Database.execute(sql, params)
        return True
