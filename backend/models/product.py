from backend.models.database import Database


class Product:

    @classmethod
    def get_categories(cls):
        return Database.query_all("SELECT * FROM categories ORDER BY name ASC")

    @classmethod
    def get_category_by_slug(cls, slug: str):
        return Database.query_one("SELECT * FROM categories WHERE slug = %s", (slug,))

    @classmethod
    def get_all(cls, category_id=None, search=None, min_price=None, max_price=None, min_rating=None, sort_by="popular", limit=100):
        sql = """
            SELECT p.*, c.name as category_name, c.slug as category_slug,
                   (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = 1 LIMIT 1) as primary_image
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1
        """
        params = []

        if category_id:
            sql += " AND p.category_id = %s"
            params.append(category_id)

        if search:
            sql += " AND (p.name LIKE %s OR p.short_description LIKE %s OR p.description LIKE %s)"
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])

        if min_price is not None and str(min_price).strip() != "":
            sql += " AND p.price >= %s"
            params.append(float(min_price))

        if max_price is not None and str(max_price).strip() != "":
            sql += " AND p.price <= %s"
            params.append(float(max_price))

        if min_rating is not None and str(min_rating).strip() != "":
            sql += " AND p.avg_rating >= %s"
            params.append(float(min_rating))

        # Sorting
        if sort_by == "price_low":
            sql += " ORDER BY (p.price * (1 - p.discount_percent/100)) ASC"
        elif sort_by == "price_high":
            sql += " ORDER BY (p.price * (1 - p.discount_percent/100)) DESC"
        elif sort_by == "rating":
            sql += " ORDER BY p.avg_rating DESC"
        elif sort_by == "newest":
            sql += " ORDER BY p.id DESC"
        else:
            sql += " ORDER BY p.is_featured DESC, p.review_count DESC, p.id DESC"

        if limit:
            sql += f" LIMIT {int(limit)}"

        products = Database.query_all(sql, params)
        for prod in products:
            if not prod.get("primary_image"):
                prod["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"
            prod["discounted_price"] = round(float(prod["price"]) * (1 - float(prod["discount_percent"]) / 100.0), 2)
        return products

    @classmethod
    def get_by_id(cls, product_id: int):
        sql = """
            SELECT p.*, c.name as category_name, c.slug as category_slug
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        """
        prod = Database.query_one(sql, (product_id,))
        if not prod:
            return None

        # Fetch images
        images = Database.query_all(
            "SELECT * FROM product_images WHERE product_id = %s ORDER BY is_primary DESC, id ASC",
            (product_id,)
        )
        if not images:
            images = [{"image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80", "is_primary": 1}]

        prod["images"] = images
        prod["primary_image"] = images[0]["image_url"]
        prod["discounted_price"] = round(float(prod["price"]) * (1 - float(prod["discount_percent"]) / 100.0), 2)
        return prod

    @classmethod
    def get_by_slug(cls, slug: str):
        prod = Database.query_one("SELECT id FROM products WHERE slug = %s", (slug,))
        if prod:
            return cls.get_by_id(prod["id"])
        return None

    @classmethod
    def get_featured(cls, limit=6):
        return cls.get_all(sort_by="popular", limit=limit)

    @classmethod
    def get_trending(cls, limit=6):
        sql = """
            SELECT p.*, c.name as category_name,
                   (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = 1 LIMIT 1) as primary_image
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 AND p.is_trending = 1
            ORDER BY p.id DESC LIMIT %s
        """
        products = Database.query_all(sql, (limit,))
        for prod in products:
            if not prod.get("primary_image"):
                prod["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"
            prod["discounted_price"] = round(float(prod["price"]) * (1 - float(prod["discount_percent"]) / 100.0), 2)
        return products

    @classmethod
    def save_product(cls, category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, image_urls, product_id=None):
        if product_id:
            Database.execute(
                """
                UPDATE products 
                SET category_id = %s, name = %s, slug = %s, short_description = %s, description = %s, 
                    specifications = %s, price = %s, discount_percent = %s, stock = %s, 
                    is_featured = %s, is_trending = %s
                WHERE id = %s
                """,
                (category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, product_id)
            )
            # Replace images if new ones provided
            if image_urls:
                Database.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))
                for i, img_url in enumerate(image_urls):
                    is_p = 1 if i == 0 else 0
                    Database.execute("INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)", (product_id, img_url, is_p))
            return product_id
        else:
            pid = Database.execute(
                """
                INSERT INTO products (category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                """,
                (category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending)
            )
            if image_urls:
                for i, img_url in enumerate(image_urls):
                    is_p = 1 if i == 0 else 0
                    Database.execute("INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)", (pid, img_url, is_p))
            return pid

    @classmethod
    def delete_product(cls, product_id: int):
        Database.execute("UPDATE products SET is_active = 0 WHERE id = %s", (product_id,))
        return True
