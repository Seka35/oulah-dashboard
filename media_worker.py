import os
import time
import requests
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
import tempfile

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://anon-404@localhost/analyse_ad")
MAX_RETRIES = 3
MAX_THREADS = 10  # Parallel downloads

# R2 Storage
from r2_storage import upload_creative, get_creative_key, guess_content_type

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

HEADERS_FB = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.facebook.com/",
    "Accept": "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "video",
    "Sec-Fetch-Mode": "no-cors",
    "Sec-Fetch-Site": "cross-site",
}

HEADERS_TIKTOK = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.tiktok.com/",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}

def is_valid_url(url):
    """Skip obviously broken/truncated URLs"""
    if not url or not isinstance(url, str):
        return False
    if url.strip().endswith('...'):
        return False
    if len(url) < 20:
        return False
    if not url.startswith('http'):
        return False
    return True

def download_file(url, local_path, headers=None):
    if not is_valid_url(url):
        return None, None
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    try:
        response = requests.get(url, stream=True, timeout=60, headers=headers or {}, allow_redirects=True)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        size = os.path.getsize(local_path)
        if size < 512:
            os.remove(local_path)
            return None, None
        mime = response.headers.get('content-type', '')
        return size, mime
    except Exception as e:
        if os.path.exists(local_path):
            os.remove(local_path)
        return None, None

def process_single_fb(c):
    """Download FB creative, upload to R2, store R2 URL in DB"""
    if not is_valid_url(c['original_url']):
        return

    ext = 'mp4' if 'video' in c['type'] else 'jpg'
    ad_id = c['ad_archive_id']

    # Use temp file for download
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        local_path = tmp.name

    try:
        for attempt in range(MAX_RETRIES):
            size, mime = download_file(c['original_url'], local_path, headers=HEADERS_FB)
            if size:
                # Generate R2 key and upload
                creative_num = c.get('card_id') or c['id']
                r2_key = get_creative_key('meta', ad_id, creative_num, ext)
                content_type = guess_content_type(ext)

                r2_url = upload_creative(local_path, r2_key, content_type)
                if r2_url:
                    with psycopg2.connect(DATABASE_URL) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE ad_creatives
                                SET local_path = %s, downloaded_at = NOW(), file_size_bytes = %s, mime_type = %s
                                WHERE id = %s
                            """, (r2_url, size, mime, c['id']))
                    print(f"[R2] FB creative {c['id']} -> {r2_url}")
                    return
            time.sleep(1)

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE ad_creatives SET download_failed = TRUE WHERE id = %s", (c['id'],))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

def process_single_tiktok(m):
    """Download TikTok media, upload to R2, store R2 URL in DB"""
    if not is_valid_url(m['original_url']):
        return

    ext = 'mp4' if m['media_type'] == 'video' else 'jpg'
    ad_id = m['ad_id']

    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        local_path = tmp.name

    try:
        for attempt in range(MAX_RETRIES):
            size, mime = download_file(m['original_url'], local_path, headers=HEADERS_TIKTOK)
            if size:
                creative_num = m.get('media_index') or m['id']
                r2_key = get_creative_key('tiktok', ad_id, creative_num, ext)
                content_type = guess_content_type(ext)

                r2_url = upload_creative(local_path, r2_key, content_type)
                if r2_url:
                    with psycopg2.connect(DATABASE_URL) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("""
                                UPDATE tiktok_ad_media
                                SET local_path = %s, downloaded_at = NOW(), file_size_bytes = %s, mime_type = %s
                                WHERE id = %s
                            """, (r2_url, size, mime, m['id']))
                    print(f"[R2] TikTok media {m['id']} -> {r2_url}")
                    return
            time.sleep(1)

        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE tiktok_ad_media SET download_failed = TRUE WHERE id = %s", (m['id'],))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

def process_fb_creatives():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT id, ad_archive_id, type, original_url
            FROM ad_creatives
            WHERE downloaded_at IS NULL AND download_failed = FALSE AND original_url IS NOT NULL
            LIMIT 50
        """)
        creatives = cursor.fetchall()
        if not creatives: return
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            executor.map(process_single_fb, creatives)
    finally:
        cursor.close()
        conn.close()

def process_tiktok_media():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT id, ad_id, media_index, media_type, original_url
            FROM tiktok_ad_media
            WHERE downloaded_at IS NULL AND download_failed = FALSE AND original_url IS NOT NULL
            LIMIT 50
        """)
        media = cursor.fetchall()
        if not media: return
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            executor.map(process_single_tiktok, media)
    finally:
        cursor.close()
        conn.close()

def main():
    print("Starting Media Downloader Worker (R2 upload mode)...")
    while True:
        try:
            process_fb_creatives()
            process_tiktok_media()
        except Exception as e:
            print(f"Worker iteration error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()