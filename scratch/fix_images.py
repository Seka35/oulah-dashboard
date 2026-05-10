
from db import get_connection
import json
from psycopg2.extras import DictCursor, Json

def fix_images():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    print("🛠️ Fixing Etsy images...")
    cursor.execute("SELECT id, raw_json FROM etsy_products WHERE image_url IS NULL OR image_url = ''")
    rows = cursor.fetchall()
    for r in rows:
        raw = r['raw_json']
        img = raw.get('imageUrl') or raw.get('image') or ''
        if img:
            cursor.execute("UPDATE etsy_products SET image_url = %s WHERE id = %s", (img, r['id']))
    
    print("🛠️ Fixing Amazon images...")
    cursor.execute("SELECT id, raw_json FROM amazon_products WHERE image_url IS NULL OR image_url = ''")
    rows = cursor.fetchall()
    for r in rows:
        raw = r['raw_json']
        img = raw.get('thumbnail') or raw.get('imageUrl') or raw.get('image') or ''
        if img:
            cursor.execute("UPDATE amazon_products SET image_url = %s WHERE id = %s", (img, r['id']))
            
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Images fixed!")

if __name__ == "__main__":
    fix_images()
