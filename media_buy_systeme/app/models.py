from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
from app.config import Config


def get_db():
    return psycopg2.connect(Config.DATABASE_URL)


class Campaign:
    @staticmethod
    def fetch_all(filters=None):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        where = []
        params = []
        if filters:
            if filters.get("launched") is not None:
                where.append("launched = %s")
                params.append(filters["launched"])
            if filters.get("status"):
                where.append("status = %s")
                params.append(filters["status"])
            if filters.get("countries"):
                where.append("countries = %s")
                params.append(filters["countries"])

        sql = "SELECT * FROM campaigns"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC"

        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def fetch_pending():
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM campaigns WHERE launched = FALSE ORDER BY id ASC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def fetch_one(campaign_id):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM campaigns WHERE id = %s", (campaign_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def create(data):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            INSERT INTO campaigns (name, objective, budget, budget_type, countries,
                                  age_min, age_max, creative_key, ad_title, ad_body, cta_link, status)
            VALUES (%(name)s, %(objective)s, %(budget)s, %(budget_type)s, %(countries)s,
                    %(age_min)s, %(age_max)s, %(creative_key)s, %(ad_title)s, %(ad_body)s, %(cta_link)s, %(status)s)
            RETURNING id
        """, data)
        new_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        return new_id

    @staticmethod
    def update(campaign_id, data):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE campaigns SET
                name = %(name)s, objective = %(objective)s, budget = %(budget)s,
                budget_type = %(budget_type)s, countries = %(countries)s,
                age_min = %(age_min)s, age_max = %(age_max)s,
                creative_key = %(creative_key)s, ad_title = %(ad_title)s,
                ad_body = %(ad_body)s, cta_link = %(cta_link)s, status = %(status)s
            WHERE id = %(id)s
        """, {**data, "id": campaign_id})
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def delete(campaign_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM campaigns WHERE id = %s", (campaign_id,))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def mark_launched(campaign_id, meta_campaign_id):
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE campaigns
            SET launched = TRUE, launched_at = %s, meta_campaign_id = %s
            WHERE id = %s
        """, (datetime.now(timezone.utc), meta_campaign_id, campaign_id))
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
                COUNT(*) FILTER (WHERE launched = TRUE) as launched,
                COUNT(*) FILTER (WHERE launched = FALSE) as pending,
                SUM(budget) FILTER (WHERE launched = TRUE) as total_budget_launched,
                MAX(launched_at) as last_launch
            FROM campaigns
        """)
        row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(row)