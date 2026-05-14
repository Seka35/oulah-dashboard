from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
from app.config import Config
import json

def get_db():
    return psycopg2.connect(Config.DATABASE_URL)

class BaseORM:
    table_name = ""

    @classmethod
    def fetch_all(cls, filters=None, order_by="created_at DESC"):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        where = []
        params = []
        if filters:
            for key, val in filters.items():
                where.append(f"{key} = %s")
                params.append(val)
        
        sql = f"SELECT * FROM {cls.table_name}"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {order_by}"
        
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]

    @classmethod
    def fetch_one(cls, id_val, id_col="id"):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM {cls.table_name} WHERE {id_col} = %s", (id_val,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None

class Product(BaseORM):
    table_name = "products"

    @staticmethod
    def fetch_approved():
        return Product.fetch_all({"status": "approved"}, order_by="updated_at ASC")

    @staticmethod
    def update_status(product_id, status):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE products SET status = %s, updated_at = NOW() WHERE id = %s", (status, product_id))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def mark_testing(product_id, meta_data):
        """
        meta_data: {campaign_id, adset_id, ad_account_id, ad_account_name, daily_budget}
        """
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE products SET
                meta_campaign_id      = %s,
                meta_adset_id         = %s,
                meta_ad_account_id    = %s,
                meta_ad_account_name  = %s,
                meta_campaign_status  = 'active',
                testing_started_at    = NOW(),
                testing_daily_budget  = %s,
                status                = 'testing',
                updated_at            = NOW()
            WHERE id = %s
        """, (
            meta_data["campaign_id"],
            meta_data["adset_id"],
            meta_data["ad_account_id"],
            meta_data["ad_account_name"],
            meta_data["daily_budget"],
            product_id
        ))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def update_metrics(product_id, metrics):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE products SET
                meta_amount_spent     = %s,
                meta_purchases        = %s,
                meta_conversion_value = %s,
                meta_cpm              = %s,
                meta_ctr              = %s,
                meta_cpc              = %s,
                meta_atc              = %s,
                meta_ic               = %s,
                meta_roas             = %s,
                updated_at            = NOW()
            WHERE id = %s
        """, (
            metrics.get("spend", 0),
            metrics.get("purchases", 0),
            metrics.get("conversion_value", 0),
            metrics.get("cpm", 0),
            metrics.get("ctr", 0),
            metrics.get("cpc", 0),
            metrics.get("atc", 0),
            metrics.get("ic", 0),
            metrics.get("roas", 0),
            product_id
        ))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_stats():
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'testing') as testing,
                COUNT(*) FILTER (WHERE status = 'approved') as approved,
                COUNT(*) FILTER (WHERE status = 'draft') as draft,
                COALESCE(SUM(meta_amount_spent), 0) as total_spend,
                COALESCE(SUM(meta_purchases), 0) as total_purchases
            FROM products
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row)

class Creative(BaseORM):
    table_name = "creatives"

    @staticmethod
    def fetch_for_product(product_id, status="approved"):
        return Creative.fetch_all({"product_id": product_id, "status": status}, order_by="created_at ASC")

    @staticmethod
    def link_ad(creative_id, meta_ad_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE creatives SET meta_ad_id = %s, updated_at = NOW() WHERE id = %s", (meta_ad_id, creative_id))
        conn.commit()
        cur.close()
        conn.close()

class MetaAdset(BaseORM):
    table_name = "meta_adsets"

    @staticmethod
    def upsert(data):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO meta_adsets (
                product_id, campaign_id, adset_id, adset_name, status,
                daily_budget, amount_spent, purchases, conversion_value,
                cpm, ctr, cpc, atc, ic, roas, updated_at
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            ON CONFLICT (adset_id) DO UPDATE SET
                status            = EXCLUDED.status,
                daily_budget      = EXCLUDED.daily_budget,
                amount_spent      = EXCLUDED.amount_spent,
                purchases         = EXCLUDED.purchases,
                conversion_value  = EXCLUDED.conversion_value,
                cpm               = EXCLUDED.cpm,
                ctr               = EXCLUDED.ctr,
                cpc               = EXCLUDED.cpc,
                atc               = EXCLUDED.atc,
                ic                = EXCLUDED.ic,
                roas              = EXCLUDED.roas,
                updated_at        = NOW()
        """, (
            data["product_id"], data["campaign_id"], data["adset_id"], data["adset_name"], data["status"],
            data.get("daily_budget"), data.get("amount_spent", 0), data.get("purchases", 0), data.get("conversion_value", 0),
            data.get("cpm", 0), data.get("ctr", 0), data.get("cpc", 0), data.get("atc", 0), data.get("ic", 0), data.get("roas", 0)
        ))
        conn.commit()
        cur.close()
        conn.close()

class Event(BaseORM):
    table_name = "events"

    @staticmethod
    def log(product_id, event_type, payload):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO events (product_id, event_type, payload) VALUES (%s, %s, %s)", 
                   (product_id, event_type, json.dumps(payload)))
        conn.commit()
        cur.close()
        conn.close()

class Setting(BaseORM):
    table_name = "settings"

    @staticmethod
    def get(key, default=None):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = %s", (key,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else default

    @staticmethod
    def set(key, value):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO settings (key, value, updated_at) 
            VALUES (%s, %s, NOW()) 
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
        """, (key, value))
        conn.commit()
        cur.close()
        conn.close()