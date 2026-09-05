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
    def save_product(cls, category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, image_urls, product_id=None, is_active=1):
        is_active_val = 1 if is_active else 0
        if product_id:
            Database.execute(
                """
                UPDATE products 
                SET category_id = %s, name = %s, slug = %s, short_description = %s, description = %s, 
                    specifications = %s, price = %s, discount_percent = %s, stock = %s, 
                    is_featured = %s, is_trending = %s, is_active = %s
                WHERE id = %s
                """,
                (category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, is_active_val, product_id)
            )
            # Replace images if new ones provided
            if image_urls and len(image_urls) > 0:
                Database.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))
                for i, img_url in enumerate(image_urls):
                    if img_url and str(img_url).strip():
                        is_p = 1 if i == 0 else 0
                        Database.execute("INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)", (product_id, str(img_url).strip(), is_p))
            return product_id
        else:
            pid = Database.execute(
                """
                INSERT INTO products (category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (category_id, name, slug, short_description, description, specifications, price, discount_percent, stock, is_featured, is_trending, is_active_val)
            )
            if image_urls and len(image_urls) > 0:
                for i, img_url in enumerate(image_urls):
                    if img_url and str(img_url).strip():
                        is_p = 1 if i == 0 else 0
                        Database.execute("INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)", (pid, str(img_url).strip(), is_p))
            return pid

    @classmethod
    def get_admin_products(cls, category_id=None, status="all", stock_status="all", search=None, sort_by="newest", page=1, limit=10):
        where_clauses = ["1=1"]
        params = []

        if category_id and str(category_id).isdigit():
            where_clauses.append("p.category_id = %s")
            params.append(int(category_id))

        if status == "active":
            where_clauses.append("p.is_active = 1")
        elif status == "inactive":
            where_clauses.append("p.is_active = 0")

        if stock_status == "in_stock":
            where_clauses.append("p.stock > 0")
        elif stock_status == "low_stock":
            where_clauses.append("p.stock > 0 AND p.stock <= 10")
        elif stock_status == "out_of_stock":
            where_clauses.append("p.stock <= 0")

        if search and str(search).strip():
            pattern = f"%{str(search).strip()}%"
            where_clauses.append("(p.name LIKE %s OR p.short_description LIKE %s OR p.description LIKE %s OR c.name LIKE %s)")
            params.extend([pattern, pattern, pattern, pattern])

        where_sql = " AND ".join(where_clauses)

        # Count total records
        count_sql = f"SELECT COUNT(*) as total FROM products p JOIN categories c ON p.category_id = c.id WHERE {where_sql}"
        count_res = Database.query_one(count_sql, params)
        total_count = count_res.get("total", 0) if count_res else 0

        # Sorting mapping
        sort_map = {
            "newest": "p.id DESC",
            "oldest": "p.id ASC",
            "name_asc": "p.name ASC",
            "name_desc": "p.name DESC",
            "price_asc": "p.price ASC",
            "price_desc": "p.price DESC",
            "final_price_asc": "(p.price * (1 - p.discount_percent/100)) ASC",
            "final_price_desc": "(p.price * (1 - p.discount_percent/100)) DESC",
            "stock_asc": "p.stock ASC",
            "stock_desc": "p.stock DESC",
        }
        order_clause = sort_map.get(sort_by, "p.id DESC")

        # Pagination calculation
        page = max(1, int(page))
        limit = max(1, int(limit))
        offset = (page - 1) * limit
        total_pages = max(1, (total_count + limit - 1) // limit)

        sql = f"""
            SELECT p.*, c.name as category_name, c.slug as category_slug,
                   (SELECT image_url FROM product_images WHERE product_id = p.id AND is_primary = 1 LIMIT 1) as primary_image
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE {where_sql}
            ORDER BY {order_clause}
            LIMIT {limit} OFFSET {offset}
        """

        products = Database.query_all(sql, params)
        for prod in products:
            if not prod.get("primary_image"):
                prod["primary_image"] = "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=800&q=80"
            price = float(prod.get("price", 0))
            disc = float(prod.get("discount_percent", 0))
            prod["discounted_price"] = round(price * (1 - disc / 100.0), 2)
            # Format created date string safely
            created_at = prod.get("created_at")
            if created_at:
                prod["created_date"] = str(created_at).split(" ")[0]
            else:
                prod["created_date"] = "-"

        return {
            "products": products,
            "total": total_count,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }

    @classmethod
    def toggle_status(cls, product_id: int, is_active: bool):
        Database.execute("UPDATE products SET is_active = %s WHERE id = %s", (1 if is_active else 0, product_id))
        return True

    @classmethod
    def delete_product(cls, product_id: int, permanent: bool = False):
        if permanent:
            Database.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))
            Database.execute("DELETE FROM cart_items WHERE product_id = %s", (product_id,))
            Database.execute("DELETE FROM wishlist_items WHERE product_id = %s", (product_id,))
            Database.execute("DELETE FROM reviews WHERE product_id = %s", (product_id,))
            Database.execute("DELETE FROM products WHERE id = %s", (product_id,))
        else:
            Database.execute("UPDATE products SET is_active = 0 WHERE id = %s", (product_id,))
        return True

