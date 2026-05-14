"""
Landing Page Scraper
Downloads and stores landing pages from Facebook ads (link_url).
Inlines CSS, JS, and downloads images for offline viewing.
Uses Playwright for JavaScript-rendered pages (SPAs like Zalando).
"""

import os
import re
import json
import zipfile
import base64
import hashlib
import sqlite3
from urllib.parse import urljoin, urlparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import requests
import subprocess
import shutil
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://anon-404@localhost/analyse_ad")
LANDING_PAGES_DIR = "static/landing_pages"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}

PROXY_URL = os.getenv("SCRAPER_PROXY_URL")
PROXY_AUTH = os.getenv("SCRAPER_PROXY_AUTH")
PROXY_TYPE = os.getenv("SCRAPER_PROXY_TYPE", "http")

def get_proxies():
    if PROXY_URL and PROXY_AUTH:
        # Use socks5h for remote DNS and better compatibility
        prefix = "socks5h" if PROXY_TYPE.lower() == "socks5" else "http"
        proxy_full = f"{prefix}://{PROXY_AUTH}@{PROXY_URL}"
        return {
            'http': proxy_full,
            'https': proxy_full
        }
    return None


def get_db_connection():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def save_landing_page(ad_archive_id, source_url, html_content=None, metadata=None):
    """Save landing page record to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO landing_pages (ad_archive_id, source_url, domain, headline, price_amount, price_text, currency, checkout_type, status, scrape_error, scraped_at, local_html_path, local_assets_path, r2_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                scraped_at = EXCLUDED.scraped_at,
                r2_url = EXCLUDED.r2_url
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
            metadata.get('local_assets_path') if metadata else None,
            metadata.get('r2_url') if metadata else None
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
        proxies = get_proxies()
        resp = requests.get(url, headers=HEADERS, timeout=timeout, proxies=proxies)
        if resp.status_code == 200:
            content_type = resp.headers.get('content-type', '').split(';')[0]
            return resp.content, content_type
    except:
        pass
    return None, None


def scrape_with_playwright(url, output_dir, timeout=90):
    """
    Scrape a page using Playwright (headless Chrome) with STEALTH enhancements.
    """
    try:
        from playwright.sync_api import sync_playwright
        import random
        import time

        print(f"  🌐 [Playwright] Starting browser for {url}...")
    except ImportError:
        print("  ❌ [Playwright] Library not found. Install with 'pip install playwright'")
        return None
    except Exception as e:
        print(f"  ❌ [Playwright] Setup error: {e}")
        return None
    metadata = {
        'headline': None,
        'price_text': None,
        'price_amount': None,
        'currency': 'USD',
        'checkout_type': None
    }
    
    try:
        with sync_playwright() as p:
            print(f"  🌐 [Playwright] Launching Firefox...")
            browser = p.firefox.launch(headless=True)
            
            # Proxy config for Playwright
            proxy_config = None
            if PROXY_URL and PROXY_AUTH:
                # Playwright supports socks5h:// for remote DNS resolution
                ptype = "socks5h" if PROXY_TYPE.lower() == "socks5" else PROXY_TYPE
                server_url = f"{ptype}://{PROXY_URL}"
                proxy_config = {
                    "server": server_url,
                    "username": PROXY_AUTH.split(':')[0],
                    "password": PROXY_AUTH.split(':')[1]
                }

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
                viewport={'width': 1920, 'height': 1080},
                proxy=proxy_config,
                extra_http_headers=HEADERS
            )

            # Manual Stealth: Delete navigator.webdriver
            context.add_init_script("delete Object.getPrototypeOf(navigator).webdriver")

            page = context.new_page()
            page.set_default_timeout(timeout * 1000)

            try:
                # Random delay before navigation
                time.sleep(random.uniform(1.0, 3.0))
                
                # Wait and scroll to trigger lazy loading
                print(f"  🖱️ [Playwright] Scrolling and waiting for {url}...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                page.wait_for_timeout(3000)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(5000) # Increased wait for videos/assets

                html_content = page.content()
                metadata['headline'] = page.title()

                # Extract price
                try:
                    price_elem = page.locator('[class*="price"], [class*="Price"], [data-testid*="price"], .sale-price, .original-price').first
                    if price_elem.count() > 0:
                        price_text = price_elem.inner_text()
                        if price_text:
                            metadata['price_text'] = price_text.strip()
                            nums = re.findall(r'[\d,]+(?:\.\d+)?', price_text)
                            if nums:
                                try:
                                    metadata['price_amount'] = float(nums[0].replace(',', ''))
                                except ValueError:
                                    pass
                except:
                    pass

                # Checkouts
                html_lower = html_content.lower()
                checkouts = {
                    'stripe': ['stripe', 'js.stripe.com', 'checkout.stripe.com'],
                    'gumroad': ['gumroad', 'gum.co', 'gumroad.com/l/'],
                    'paddle': ['paddle', 'paddle.com', 'cdn.paddle.com'],
                    'shopify': ['shopify', 'cdn.shopify.com'],
                    'woocommerce': ['woocommerce', 'wp-content/plugins/woocommerce'],
                    'systeme': ['systeme.io', 'systeme.fr'],
                    'kajabi': ['kajabi', 'cdn.kajabi.com'],
                }
                for platform, signatures in checkouts.items():
                    if any(sig in html_lower for sig in signatures):
                        metadata['checkout_type'] = platform
                        break

            except Exception as e:
                browser.close()
                return None, f"Playwright error: {str(e)[:50]}"

            browser.close()

        return html_content, metadata

    except ImportError:
        return None, "Playwright not installed. Run: pip install playwright && playwright install chromium"
    except Exception as e:
        return None, f"Playwright fatal error: {str(e)[:50]}"


def scrape_with_wget(url, output_dir, timeout=120):
    """
    Scrape a page using wget --page-requisites --convert-links --adjust-extension.
    Returns (html_content, metadata)
    """
    print(f"  📥 [Wget] Scraping {url} to {output_dir}...")
    
    # Ensure output_dir exists and is clean for wget
    if os.path.exists(output_dir):
        # We might want to keep it if we are resume, but usually clean is better
        pass
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Command suggested by user: 
        # wget --page-requisites --convert-links --adjust-extension -P ./page2 https://www.landing.page
        # We add --no-host-directories and -nH to keep it flat in output_dir
        cmd = [
            "wget",
            "--page-requisites",
            "--convert-links",
            "--adjust-extension",
            "-e", "robots=off",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "--no-check-certificate",
            "--no-directories",
            "--no-host-directories",
            "-nH",
            "--span-hosts", # Download assets from other domains (CDNs)
            "--timeout", str(timeout),
            "--tries", "2",
            "-P", output_dir,
            url
        ]
        
        # Add User-Agent to wget
        cmd.extend(["--user-agent", HEADERS['User-Agent']])

        # Run wget
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 10)
        
        if result.returncode != 0:
            print(f"  ⚠️ [Wget] Warning/Error (code {result.returncode}): {result.stderr[:200]}")
            # Wget often returns non-zero for minor resource errors, we continue if index.html exists

        # Find the main HTML file and rename it to index.html if necessary
        index_path = os.path.join(output_dir, "index.html")
        if not os.path.exists(index_path):
            html_files = [f for f in os.listdir(output_dir) if f.endswith(".html")]
            if html_files:
                original_index = os.path.join(output_dir, html_files[0])
                os.rename(original_index, index_path)
                print(f"  📝 [Wget] Renamed {html_files[0]} to index.html")
            else:
                return None, "Wget failed: no HTML file found"

        with open(index_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        metadata = {
            'headline': None,
            'price_text': None,
            'price_amount': None,
            'currency': 'USD',
            'checkout_type': None,
            'method': 'wget',
            'local_index': index_path
        }
        
        # Basic metadata extraction from HTML
        soup = BeautifulSoup(html_content, 'lxml')
        title_tag = soup.find('title')
        if title_tag:
            metadata['headline'] = title_tag.get_text().strip()

        return html_content, metadata

    except subprocess.TimeoutExpired:
        return None, "Wget timeout"
    except Exception as e:
        return None, f"Wget error: {str(e)}"


def scrape_with_apify(url, timeout=60):
    """
    Fallback to Apify Web Scraper for extremely difficult sites (Akamai/Cloudflare).
    Uses residential proxies and stealth.
    """
    try:
        from scrapers import start_apify_actor, APIFY_KEY
        if not APIFY_KEY:
            return None, "APIFY_KEY not set"

        print(f"  ☁️ Falling back to Apify for {url}...")
        
        # Using a specialized stealth scraper if possible, or standard web scraper
        actor_id = "apify~web-scraper"
        input_data = {
            "runMode": "PRODUCTION",
            "startUrls": [{"url": url}],
            "pageFunction": "async function pageFunction(context) { return { html: await context.page.content(), title: await context.page.title() }; }",
            "proxyConfiguration": {"useApifyProxy": True, "apifyProxyGroups": ["RESIDENTIAL"]},
            "useStealth": True,
            "maxPagesPerCrawl": 1,
            "browserPoolOptions": {"useFingerprints": True}
        }
        
        result = start_apify_actor(actor_id, input_data)
        if "error" in result:
            return None, result["error"]
        
        items = result.get("ads", []) # start_apify_actor returns data in "ads" key
        if items and len(items) > 0:
            item = items[0]
            html_content = item.get("html")
            metadata = {
                'headline': item.get("title"),
                'price_text': None,
                'price_amount': None,
                'currency': 'USD',
                'checkout_type': None,
            }
            return html_content, metadata
            
        return None, "No data returned from Apify"
    except Exception as e:
        return None, f"Apify fallback error: {str(e)[:50]}"


def scrape_landing_page(ad_archive_id, url, output_dir=None):
    """
    Scrape a landing page and save it locally.
    Uses Playwright for SPA pages, falls back to requests for simple pages.
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

    print(f"🚀 [Scrape] Starting scrape for {ad_archive_id} URL: {url}")
    if not url or url in ['N/A', '', 'null', 'undefined']:
        print(f"  ❌ [Scrape] Invalid URL: {url}")
        result['status'] = 'failed'
        result['scrape_error'] = 'No URL provided'
        return result

    # Default output dir
    if output_dir is None:
        output_dir = os.path.join(LANDING_PAGES_DIR, ad_archive_id)
    os.makedirs(output_dir, exist_ok=True)

    result['local_assets_path'] = output_dir
    parsed_url = urlparse(url)
    result['domain'] = parsed_url.netloc.replace('www.', '')

    # Check if we should use Wget (New preferred method)
    use_wget = os.getenv("USE_WGET_SCRAPER", "true").lower() == "true"
    
    html_content = None
    pw_metadata = {}

    try:
        if use_wget:
            html_content, wget_metadata = scrape_with_wget(url, output_dir)
            if html_content:
                result['scraped_html'] = html_content
                result['headline'] = wget_metadata.get('headline')
                result['local_html_path'] = wget_metadata.get('local_index')
                result['status'] = 'scraped'
                # Still fall through to soup parsing for price/checkout
            else:
                print(f"  ⚠️ [Scrape] Wget failed, falling back to Playwright/Requests...")
                use_wget = False
        
        if not use_wget:
            # First try with requests (fast, works for simple pages)
            proxies = get_proxies()
            resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True, proxies=proxies)
            simple_html = resp.text if resp.status_code == 200 else ""
            
            if "Access Denied" in simple_html or "don't have permission to access" in simple_html:
                simple_html = "" 
            
            is_spa = len(simple_html) < 5000 or 'id="__NEXT_DATA__"' in simple_html or 'data-nextjs-data' in simple_html

            if is_spa or len(simple_html) < 10000:
                html_content, pw_metadata = scrape_with_playwright(url, output_dir, timeout=90)
                
                is_blocked = False
                if html_content:
                    if "Access Denied" in html_content or "don't have permission to access" in html_content:
                        is_blocked = True
                
                if not html_content or is_blocked:
                    html_content, api_metadata = scrape_with_apify(url)
                    if html_content:
                        pw_metadata = api_metadata
                    else:
                        if not html_content and not is_blocked:
                            result['status'] = 'failed'
                            result['scrape_error'] = "No content received"
                            return result
                
                if html_content:
                    result['headline'] = pw_metadata.get('headline') or result['headline']
                    result['price_text'] = pw_metadata.get('price_text') or result['price_text']
                    result['price_amount'] = pw_metadata.get('price_amount') or result['price_amount']
                    result['checkout_type'] = pw_metadata.get('checkout_type') or result['checkout_type']
                else:
                    result['status'] = 'failed'
                    result['scrape_error'] = "Blocking/Scraping failure"
                    return result
            else:
                html_content = simple_html

        # Parse HTML
        soup = BeautifulSoup(html_content, 'lxml')

        # Extract metadata if not already set
        if not result['headline']:
            og_title = soup.find('meta', property='og:title')
            title_tag = soup.find('title')
            result['headline'] = og_title['content'].strip() if og_title and og_title.get('content') else (title_tag.get_text(strip=True)[:200] if title_tag else None)

        # Price extraction
        if not result['price_text']:
            price_match = re.search(r'[\$€£¥]\s*[\d,]+(?:\.\d{2})?|[\d,]+(?:\.\d{2})?\s*(?:USD|EUR|GBP|\$|€|£)', html_content)
            if price_match:
                result['price_text'] = price_match.group(0)
                nums = re.findall(r'[\d,]+(?:\.\d+)?', price_match.group(0))
                if nums:
                    try:
                        result['price_amount'] = float(nums[0].replace(',', ''))
                    except ValueError:
                        pass
                    if '€' in price_match.group(0):
                        result['currency'] = 'EUR'
                    elif '£' in price_match.group(0):
                        result['currency'] = 'GBP'

        # Checkout detection
        if not result['checkout_type']:
            html_lower = html_content.lower()
            checkouts = {
                'stripe': ['stripe', 'js.stripe.com', 'checkout.stripe.com'],
                'gumroad': ['gumroad', 'gum.co', 'gumroad.com/l/'],
                'paddle': ['paddle', 'paddle.com', 'cdn.paddle.com'],
                'shopify': ['shopify', 'cdn.shopify.com'],
                'woocommerce': ['woocommerce', 'wp-content/plugins/woocommerce'],
                'systeme': ['systeme.io', 'systeme.fr'],
                'kajabi': ['kajabi', 'cdn.kajabi.com'],
            }
            for platform, signatures in checkouts.items():
                if any(sig in html_lower for sig in signatures):
                    result['checkout_type'] = platform
                    break

        # If we used wget, we are done with scraping and asset collection
        if use_wget:
            result['scraped_html'] = html_content # Store full HTML for rebranding
            # Upload final HTML to R2
            try:
                from r2_storage import upload_landing_page
                r2_url = upload_landing_page(result['local_html_path'], ad_archive_id)
                if r2_url:
                    result['r2_url'] = r2_url
                    print(f"  ☁️ [R2] Final Landing page (Wget): {r2_url}")
            except Exception as e:
                print(f"  ⚠️ R2 Upload error: {e}")
            
            result['status'] = 'scraped'
            return result

        # --- LEGACY ASSET INLINING (Only if NOT using wget) ---
        asset_count = 0
        # ...

        # Assets to inline (by tag and attribute)
        asset_tags = {
            'link': 'href',      # CSS files
            'script': 'src',     # JS files
            'img': 'src',        # Images
            'source': 'src',     # Video/audio
            'video': 'src',      # Video
            'audio': 'src',      # Audio
            'embed': 'src',      # Embeds
            'iframe': 'src',     # Iframes
        }

        # Fonts to download and inline
        font_extensions = ['.woff2', '.woff', '.ttf', '.otf', '.eot']

        def is_inlineable(content, mime, max_size=2*1024*1024):
            """Check if asset is inlineable (under max_size)"""
            if not mime or not mime.strip():
                return False
            if not content or len(content) > max_size:
                return False
            inlineable_types = ['text/css', 'application/javascript', 'image/', 'font/', 'audio/', 'video/']
            return any(t in mime for t in inlineable_types)

        assets_to_download = []
        for tag_name, attr in asset_tags.items():
            for el in soup.find_all(tag_name):
                src = el.get(attr) or el.get('data-src') or el.get('data-lazy-src') or el.get('data-original')
                if not src:
                    continue

                # Force src attribute if we found it in a data attribute
                el[attr] = src

                # Handle root-relative URLs (/path)
                if src.startswith('/'):
                    base_domain = urlparse(url).netloc
                    src = f"https://{base_domain}{src}"
                    el[attr] = src

                full_url = urljoin(url, src)
                parsed = urlparse(full_url)

                # Skip external domains for downloading (keep as original links)
                # except for CDNs and Fonts which we want to inline/store
                base_domain = urlparse(url).netloc
                if parsed.netloc and parsed.netloc != base_domain:
                    is_cdn = any(cdn in parsed.netloc for cdn in ['cdn.', 'assets.', 'static.', 'cloudflare', 'kajabi-cdn'])
                    is_font = any(ext in src.lower() for ext in font_extensions)
                    is_video = any(vd in parsed.netloc for vd in ['wistia', 'youtube', 'vimeo', 'vimeocdn', 'googlevideo'])
                    
                    if not (is_cdn or is_font or (is_video and tag_name != 'iframe')):
                        # Keep original external URL in the tag, but don't download
                        continue

                # IMPORTANT: Do NOT try to download/inline iframes or complex scripts. 
                # They must remain as external links to function correctly.
                if tag_name in ['iframe', 'embed']:
                    continue
                if tag_name == 'script' and any(vd in full_url for vd in ['wistia', 'youtube', 'vimeo']):
                    continue

                assets_to_download.append({
                    'el': el,
                    'attr': attr,
                    'url': full_url,
                    'type': 'tag'
                })

        # Process inline styles
        for elem in soup.find_all(style=True):
            style = elem.get('style', '')
            url_pattern = re.compile(r'url\([\'"]?([^\'"()]+)[\'"]?\)')
            matches = url_pattern.findall(style)
            for match in matches:
                if match.startswith('data:'):
                    continue
                if match.startswith('/'):
                    base_domain = urlparse(url).netloc
                    match = f"https://{base_domain}{match}"
                full_url = urljoin(url, match)
                assets_to_download.append({
                    'el': elem,
                    'url': full_url,
                    'original_match': match,
                    'type': 'style'
                })
        
        if assets_to_download:
            print(f"  📥 [Scrape] Downloading {len(assets_to_download)} assets in parallel for {url}...")

        def download_and_store(asset):
            try:
                content, mime = download_file(asset['url'], timeout=15)
                asset['content'] = content
                asset['mime'] = mime
            except:
                asset['content'] = None
                asset['mime'] = None
            return asset

        with ThreadPoolExecutor(max_workers=20) as executor:
            downloaded_assets = list(executor.map(download_and_store, assets_to_download))

        from r2_storage import upload_bytes

        for asset in downloaded_assets:
            try:
                # 1. Download
                if not asset['content']:
                    continue
                
                # 2. Save locally for rebranding/local viewing
                parsed_asset = urlparse(asset['url'])
                filename = os.path.basename(parsed_asset.path)
                if not filename or '.' not in filename:
                    ext = mimetypes.guess_extension(asset['mime']) or '.bin'
                    import hashlib
                    filename = hashlib.md5(asset['url'].encode()).hexdigest() + ext
                
                # Clean filename
                filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                local_asset_path = os.path.join(output_dir, filename)
                
                with open(local_asset_path, 'wb') as f:
                    f.write(asset['content'])
                
                # Update HTML to point to local file
                final_url = filename # Relative path for local index.html
                
                # 3. Optional: Still upload to R2 for cloud viewing if large
                is_large = len(asset['content']) > 500*1024 # > 500KB
                if is_large:
                    r2_key = f"scrape/landing_pages/{ad_archive_id}/assets/{filename}"
                    upload_bytes(asset['content'], r2_key, asset['mime'])
                    print(f"  ☁️ [Asset R2] Uploaded large/video asset: {asset['url']}")

                if asset['type'] == 'tag':
                    el = asset['el']
                    attr = asset['attr']
                    el[attr] = final_url
                    asset_count += 1
                elif asset['type'] == 'style':
                    el = asset['el']
                    match = asset['original_match']
                    style = el.get('style', '')
                    pattern = re.compile(re.escape(f'url({match})'), re.IGNORECASE)
                    new_style = pattern.sub(f'url({final_url})', style)
                    el['style'] = new_style
                    asset_count += 1
            except Exception as e:
                print(f"  ⚠️ Error processing asset {asset['url']}: {e}")

        # Save HTML
        html_path = os.path.join(output_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        result['local_html_path'] = html_path

        # Upload final HTML to R2
        try:
            from r2_storage import upload_landing_page
            # upload_landing_page also uploads any local assets if we had them, 
            # but we've already uploaded large ones and inlined small ones.
            r2_url = upload_landing_page(html_path, ad_archive_id)
            if r2_url:
                result['r2_url'] = r2_url
                print(f"  ☁️ [R2] Final Landing page: {r2_url}")
        except Exception as e:
            print(f"  ⚠️ R2 Upload error: {e}")

        # Store first 50k of html for DB
        result['scraped_html'] = str(soup)[:50000]
        result['status'] = 'scraped'
        print(f"  ✅ [Scraped] Success: {url} ({asset_count} assets processed)")

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
        {'ad_archive_id': 'test123', 'link_url': 'https://example.com'},
        {'ad_archive_id': 'zalando_test', 'link_url': 'https://www.zalando.de/swedemount-lofoten-stretch-zip-off-stoffhose-black-charcoal-00e21a01c-q11.html'}
    ]
    for item in test_items:
        result = scrape_landing_page(item['ad_archive_id'], item['link_url'])
        print(f"Result: {result['status']} - {result.get('domain')} - {result.get('headline', '')[:50] if result.get('headline') else 'N/A'}")