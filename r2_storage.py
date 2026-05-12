"""
R2 Storage Integration - Cloudflare R2
Upload des créatives scrapées selon la convention:
  scrape/meta/<ad_archive_id>/creative-<n>.<ext>
  scrape/tiktok/<ad_id>/creative-<n>.<ext>
"""

import os
import boto3
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv()

# Configuration R2
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_BUCKET = os.getenv("R2_BUCKET", "launch-engine-creatives")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "").rstrip("/")

# Initialiser le client S3 (boto3)
_s3_client = None

def get_s3_client():
    """Get or create S3 client for R2"""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4'),
            region_name='auto',
        )
    return _s3_client

def upload_creative(local_path, key, content_type="application/octet-stream"):
    """
    Upload un fichier vers R2 et retourne l'URL publique.

    Args:
        local_path: Chemin local du fichier à uploader
        key: Clé R2 (ex: scrape/meta/123456789/creative-1.mp4)
        content_type: MIME type du fichier

    Returns:
        URL publique du fichier sur R2, ou None si échec
    """
    if not os.path.exists(local_path):
        print(f"[R2] File not found: {local_path}")
        return None

    try:
        s3 = get_s3_client()
        s3.upload_file(
            Filename=local_path,
            Bucket=R2_BUCKET,
            Key=key,
            ExtraArgs={
                'ContentType': content_type,
                'CacheControl': 'public, max-age=31536000',
                'ACL': 'public-read',  # Explicit public access for R2
            },
        )
        public_url = f"{R2_PUBLIC_URL}/{key}"
        print(f"[R2] Uploaded: {key}")
        return public_url
    except Exception as e:
        print(f"[R2] Upload error: {e}")
        return None

def upload_bytes(file_bytes, key, content_type="application/octet-stream"):
    """
    Upload des bytes vers R2.

    Args:
        file_bytes: Contenu du fichier en bytes
        key: Clé R2
        content_type: MIME type

    Returns:
        URL publique ou None si échec
    """
    try:
        s3 = get_s3_client()
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            CacheControl='public, max-age=31536000',
        )
        public_url = f"{R2_PUBLIC_URL}/{key}"
        print(f"[R2] Uploaded (bytes): {key}")
        return public_url
    except Exception as e:
        print(f"[R2] Upload error (bytes): {e}")
        return None

def delete_creative(key):
    """Supprime un fichier de R2"""
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=R2_BUCKET, Key=key)
        print(f"[R2] Deleted: {key}")
        return True
    except Exception as e:
        print(f"[R2] Delete error: {e}")
        return False

def get_public_url(key):
    """Retourne l'URL publique d'un fichier R2"""
    return f"{R2_PUBLIC_URL}/{key}"

def test_connection():
    """Test la connexion à R2 avec un petit fichier"""
    try:
        s3 = get_s3_client()
        s3.upload_file(
            Filename='/tmp/test.txt',
            Bucket=R2_BUCKET,
            Key='test/connection_test.txt',
        )
        url = f"{R2_PUBLIC_URL}/test/connection_test.txt"
        print(f"[R2] ✅ Connection OK: {url}")
        return True
    except Exception as e:
        print(f"[R2] ❌ Connection failed: {e}")
        return False

# ============ Helpers pour chemin R2 ============

def get_creative_key(platform, ad_id, creative_num, extension):
    """
    Génère la clé R2 selon la convention de nommage.

    Args:
        platform: 'meta' (Facebook), 'tiktok', 'google', 'etsy'
        ad_id: ID de l'annonce
        creative_num: Numéro de la créative (1, 2, ...)
        extension: Extension du fichier ('mp4', 'jpg', 'png')

    Returns:
        Clé R2 (ex: scrape/meta/123456789/creative-1.mp4)
    """
    return f"scrape/{platform}/{ad_id}/creative-{creative_num}.{extension}"

def guess_content_type(filename):
    """Devine le MIME type depuis l'extension du fichier"""
    ext = filename.lower().split('.')[-1]
    mime_types = {
        'mp4': 'video/mp4',
        'webm': 'video/webm',
        'mov': 'video/quicktime',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
    }
    return mime_types.get(ext, 'application/octet-stream')


# ============ Landing Pages ============

def get_landing_page_key(ad_archive_id, filename="index.html"):
    """Génère la clé R2 pour une landing page"""
    return f"scrape/landing_pages/{ad_archive_id}/{filename}"


def upload_landing_page(local_html_path, ad_archive_id):
    """
    Upload tous les fichiers d'une landing page vers R2.
    Retourne l'URL publique de la page HTML principale.
    """
    if not os.path.exists(local_html_path):
        print(f"[R2] Landing page file not found: {local_html_path}")
        return None

    try:
        s3 = get_s3_client()
        html_dir = os.path.dirname(local_html_path)
        html_filename = os.path.basename(local_html_path)

        # Upload le fichier HTML principal
        html_key = get_landing_page_key(ad_archive_id, html_filename)
        s3.upload_file(
            Filename=local_html_path,
            Bucket=R2_BUCKET,
            Key=html_key,
            ExtraArgs={
                'ContentType': 'text/html; charset=utf-8',
                'CacheControl': 'public, max-age=86400',
                'ACL': 'public-read',
            },
        )
        main_url = f"{R2_PUBLIC_URL}/{html_key}"
        print(f"[R2] Landing page uploaded: {html_key}")

        # Upload les autres fichiers dans le dossier (css, js, etc.)
        if os.path.isdir(html_dir):
            for root, dirs, files in os.walk(html_dir):
                for file in files:
                    if file == html_filename:
                        continue  # déjà uploadé
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, html_dir)
                    key = get_landing_page_key(ad_archive_id, f"assets/{rel_path}")

                    ext = file.lower().split('.')[-1]
                    content_type = guess_content_type(file)
                    if ext == 'js':
                        content_type = 'application/javascript'
                    elif ext == 'css':
                        content_type = 'text/css'

                    s3.upload_file(
                        Filename=file_path,
                        Bucket=R2_BUCKET,
                        Key=key,
                        ExtraArgs={
                            'ContentType': content_type,
                            'CacheControl': 'public, max-age=31536000',
                            'ACL': 'public-read',
                        },
                    )

        return main_url

    except Exception as e:
        print(f"[R2] Landing page upload error: {e}")
        return None