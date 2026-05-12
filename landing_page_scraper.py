"""
Landing Page Scraper
Downloads and stores landing pages from Facebook ads (link_url).
Inlines CSS, JS, and downloads images for offline viewing.
"""

import os
import re
import json
import zipfile
import base64
import sqlite3
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://anon-404@localhost/analyse_ad")
LANDING_PAGES_DIR = "static/landing_pages"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,de;q=0.8,fr;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
}


def get_db_connection():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def save_landing_page(ad_archive_id, source_url, html_content=None, metadata=None):
    """Save landing page record to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO landing_pages (ad_archive_id, source_url, domain, headline, price_amount, price_text, currency, checkout_type, status, scrape_error, scraped_at, local_html_path, local_assets_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ad_archive_id, source_url) DO UPDATE SET
                scraped_html = EXCLUDED.scraped_html,
                local_html_path = EXCLUDED.local_html_path,
                local_assets_path = EXCLUDED.local_assets_path,
                domain = EXCLUDED.domain,
                headline = EXCLUDED.headline,
                price_amount = EXCLUDED.price_amount,
                price_text = EXCLUDED.price_text,
                currency = EXCLUDED.currency,
                checkout_type = EXCLUDED.checkout_type,
                status = EXCLUDED.status,
                scrape_error = EXCLUDED.scrape_error,
                scraped_at = EXCLUDED.scraped_at
        """, (
            ad_archive_id, source_url,
            metadata.get('domain') if metadata else None,
            metadata.get('headline') if metadata else None,
            metadata.get('price_amount') if metadata else None,
            metadata.get('price_text') if metadata else None,
            metadata.get('currency', 'USD') if metadata else 'USD',
            metadata.get('checkout_type') if metadata else None,
            metadata.get('status', 'pending') if metadata else 'pending',
            metadata.get('scrape_error') if metadata else None,
            datetime.now() if metadata and metadata.get('status') == 'scraped' else None,
            metadata.get('local_html_path') if metadata else None,
            metadata.get('local_assets_path') if metadata else None
        ))
        conn.commit()
    except Exception as e:
        print(f"DB error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()


def download_file(url, timeout=10):
    """Download a file and return (content, mime_type)"""
    if not url or url.startswith('data:'):
        return None, None
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 200:
            content_type = resp.headers.get('content-type', '').split(';')[0]
            return resp.content, content_type
    except:
        pass
    return None, None


def scrape_landing_page(ad_archive_id, url, output_dir=None):
    """
    Scrape a landing page and save it locally.
    Returns metadata dict.
    """
    result = {
        'ad_archive_id': ad_archive_id,
        'source_url': url,
        'domain': None,
        'headline': None,
        'price_amount': None,
        'price_text': None,
        'currency': 'USD',
        'checkout_type': None,
        'status': 'pending',
        'scrape_error': None,
        'local_html_path': None,
        'local_assets_path': None,
        'scraped_html': None
    }

    if not url or url in ['N/A', '', 'null', 'undefined']:
        result['status'] = 'failed'
        result['scrape_error'] = 'No URL provided'
        return result

    # Default output dir
    if output_dir is None:
        output_dir = os.path.join(LANDING_PAGES_DIR, ad_archive_id)
    os.makedirs(output_dir, exist_ok=True)

    result['local_assets_path'] = output_dir

    try:
        # Fetch the page
        resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if resp.status_code != 200:
            result['status'] = 'failed'
            result['scrape_error'] = f'HTTP {resp.status_code}'
            return result

        html = resp.text
        parsed_url = urlparse(url)
        result['domain'] = parsed_url.netloc.replace('www.', '')

        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')

        # Extract metadata
        og_title = soup.find('meta', property='og:title')
        title_tag = soup.find('title')
        result['headline'] = og_title['content'].strip() if og_title and og_title.get('content') else (title_tag.get_text(strip=True)[:200] if title_tag else None)

        # Price extraction
        price_match = re.search(r'[\$€£¥]\s*[\d,]+(?:\.\d{2})?', html)
        if price_match:
            result['price_text'] = price_match.group(0)
            nums = re.findall(r'[\d,]+(?:\.\d+)?', price_match.group(0))
            if nums:
                result['price_amount'] = float(nums[0].replace(',', ''))
                if '€' in price_match.group(0):
                    result['currency'] = 'EUR'
                elif '£' in price_match.group(0):
                    result['currency'] = 'GBP'

        # Checkout detection
        html_lower = html.lower()
        checkouts = {
            'stripe': ['stripe', 'js.stripe.com', 'checkout.stripe.com'],
            'gumroad': ['gumroad', 'gum.co', 'gumroad.com/l/'],
            'paddle': ['paddle', 'paddle.com', 'cdn.paddle.com'],
            'shopify': ['shopify', 'cdn.shopify.com'],
            'woocommerce': ['woocommerce', 'wp-content/plugins/woocommerce'],
            'systeme': ['systeme.io', 'systeme.fr'],
            'kajabi': ['kajabi', 'cdn.kajabi.com'],
            'gumroad_embed': ['gumroad.com/embed'],
        }
        for platform, signatures in checkouts.items():
            if any(sig in html_lower for sig in signatures):
                result['checkout_type'] = platform
                break

        # Download and inline assets
        asset_count = 0

        # Images - inline small images as base64
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            img_url = urljoin(url, src)
            content, mime = download_file(img_url)
            if content and mime and len(content) < 500000:  # Max 500KB for inlining
                b64 = base64.b64encode(content).decode()
                img['src'] = f"data:{mime};base64,{b64}"
                asset_count += 1

        # CSS - inline external stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if not href:
                continue
            css_url = urljoin(url, href)
            content, _ = download_file(css_url)
            if content:
                style = soup.new_tag('style')
                style.string = content.decode('utf-8', errors='ignore')
                link.replace_with(style)
                asset_count += 1

        # JS - download external scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            js_url = urljoin(url, src)
            content, _ = download_file(js_url)
            if content:
                new_script = soup.new_tag('script')
                new_script.string = content.decode('utf-8', errors='ignore')
                script.replace_with(new_script)
                asset_count += 1

        # Save HTML
        html_path = os.path.join(output_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        result['local_html_path'] = html_path

        # Store first 50k of html for DB
        result['scraped_html'] = str(soup)[:50000]
        result['status'] = 'scraped'
        print(f"  ✓ Scraped {url} - {asset_count} assets inlined")

    except requests.Timeout:
        result['status'] = 'failed'
        result['scrape_error'] = 'Timeout'
    except requests.RequestException as e:
        result['status'] = 'failed'
        result['scrape_error'] = f'Request error: {str(e)[:50]}'
    except Exception as e:
        result['status'] = 'failed'
        result['scrape_error'] = f'Error: {str(e)[:50]}'

    return result


def scrape_batch(items, max_workers=3):
    """
    Scrape multiple landing pages.
    items = list of dicts with ad_archive_id and link_url
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(scrape_landing_page, item['ad_archive_id'], item['link_url']): item
            for item in items if item.get('link_url')
        }
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append(result)
                # Save to DB
                save_landing_page(item['ad_archive_id'], item['link_url'], metadata=result)
            except Exception as e:
                print(f"Batch error for {item.get('ad_archive_id')}: {e}")
                results.append({
                    'ad_archive_id': item.get('ad_archive_id'),
                    'source_url': item.get('link_url'),
                    'status': 'failed',
                    'scrape_error': str(e)[:50]
                })
    return results


def create_download_zip(ad_archive_id, output_dir=None):
    """
    Create a ZIP file of the scraped landing page.
    Returns the path to the ZIP file.
    """
    if output_dir is None:
        output_dir = os.path.join(LANDING_PAGES_DIR, ad_archive_id)

    zip_path = os.path.join(LANDING_PAGES_DIR, f"{ad_archive_id}.zip")

    if not os.path.exists(output_dir):
        return None

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, LANDING_PAGES_DIR)
                    zipf.write(file_path, arcname)
        return zip_path
    except Exception as e:
        print(f"ZIP error: {e}")
        return None


if __name__ == '__main__':
    # Test
    test_items = [
        {'ad_archive_id': 'test123', 'link_url': 'https://example.com'}
    ]
    for item in test_items:
        result = scrape_landing_page(item['ad_archive_id'], item['link_url'])
        print(f"Result: {result['status']} - {result.get('domain')} - {result.get('headline', '')[:50] if result.get('headline') else 'N/A'}")