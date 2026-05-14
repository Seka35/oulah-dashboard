#!/usr/bin/env python3
"""
Ad Intelligence - TikTok + Facebook via Apify
"""

import os
import time
import requests
import sqlite3
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

APIFY_KEY = os.getenv("APIFY_KEY")
DB_PATH = "search_history.db"
MEDIA_DIR = "static/media"

# ============ DATABASE & MEDIA ============
import db
from db import init_db, save_search, get_search_history, get_search_results, save_ai_analysis, get_product_metadata
import ai_analyzer

def download_and_save_media(url, platform, item_id, media_type):
    if not url or "..." in url:
        return None
    
    ext = 'mp4' if media_type == 'video' else 'jpg'
    filename = f"{media_type}_{item_id}.{ext}"
    local_path = f"static/media/{platform}/{item_id}/{filename}"
    abs_path = os.path.join(os.getcwd(), local_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.facebook.com/" if platform == "facebook" else "https://www.tiktok.com/"
    }

    try:
        resp = requests.get(url, timeout=15, headers=headers, stream=True)
        if resp.status_code == 200:
            with open(abs_path, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            return "/" + local_path
    except:
        pass
    return None


# All countries for TikTok (from Apify doc)
TIKTOK_REGIONS = {
    "all": "All Countries",
    "FR": "France",
    "DE": "Germany",
    "GB": "United Kingdom",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BE": "Belgium",
    "AT": "Austria",
    "CH": "Switzerland",
    "PL": "Poland",
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
    "IE": "Ireland",
    "PT": "Portugal",
    "GR": "Greece",
    "CZ": "Czech Republic",
    "HU": "Hungary",
    "RO": "Romania",
    "SK": "Slovakia",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "SI": "Slovenia",
    "LT": "Lithuania",
    "LV": "Latvia",
    "EE": "Estonia",
    "MT": "Malta",
    "CY": "Cyprus",
    "LU": "Luxembourg",
    "IS": "Iceland",
    "LI": "Liechtenstein",
    "US": "United States",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "JP": "Japan",
    "KR": "South Korea",
    "IN": "India",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "PH": "Philippines",
    "SG": "Singapore",
    "TH": "Thailand",
    "VN": "Vietnam",
    "BR": "Brazil",
    "MX": "Mexico",
    "AR": "Argentina",
    "CO": "Colombia",
    "CL": "Chile",
    "PE": "Peru",
}

# Countries for Facebook
FACEBOOK_COUNTRIES = {
    "ALL": "All Countries",
    "FR": "France",
    "US": "United States",
    "GB": "United Kingdom",
    "DE": "Germany",
    "IT": "Italy",
    "ES": "Spain",
    "BR": "Brazil",
    "MX": "Mexico",
    "JP": "Japan",
    "KR": "South Korea",
    "IN": "India",
    "AU": "Australia",
    "CA": "Canada",
}

# Apify Actor IDs
TIKTOK_ACTOR = "data_xplorer~tiktok-ads-library-fast"
FACEBOOK_ACTOR = "curious_coder~facebook-ads-library-scraper"
ETSY_ACTOR = "JOUStaVgex0lqbRnk"
AMAZON_ACTOR = "junglee~Amazon-crawler"

# Etsy search categories
ETSY_CATEGORIES = {
    "all": "All Categories",
    "ebook": "eBooks",
    "template": "Templates",
    "course": "Courses",
    "digital": "Digital Products",
    "print": "Printables",
    "software": "Software",
    "graphics": "Graphics",
}

# Countries for Google Ads
GOOGLE_REGIONS = {
    "ALL": "All Countries",
    "FR": "France",
    "DE": "Germany",
    "GB": "United Kingdom",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BE": "Belgium",
    "AT": "Austria",
    "CH": "Switzerland",
    "PL": "Poland",
    "SE": "Sweden",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
    "IE": "Ireland",
    "PT": "Portugal",
    "GR": "Greece",
    "CZ": "Czech Republic",
    "HU": "Hungary",
    "RO": "Romania",
    "SK": "Slovakia",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "SI": "Slovenia",
    "LT": "Lithuania",
    "LV": "Latvia",
    "EE": "Estonia",
    "MT": "Malta",
    "CY": "Cyprus",
    "LU": "Luxembourg",
    "IS": "Iceland",
    "US": "United States",
    "CA": "Canada",
    "AU": "Australia",
    "NZ": "New Zealand",
    "JP": "Japan",
    "KR": "South Korea",
    "IN": "India",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "PH": "Philippines",
    "SG": "Singapore",
    "TH": "Thailand",
    "VN": "Vietnam",
    "BR": "Brazil",
    "MX": "Mexico",
    "AR": "Argentina",
    "CO": "Colombia",
    "CL": "Chile",
    "PE": "Peru",
}



# ============ SHARED SCRAPERS ============
import scrapers

# Proxy functions to keep compatibility if needed, or just use scrapers.search_xxx directly
search_tiktok = scrapers.search_tiktok
search_facebook = scrapers.search_facebook
search_etsy = scrapers.search_etsy
search_amazon = scrapers.search_amazon
search_facebook_by_advertiser = scrapers.search_facebook_by_advertiser


# ============ ROUTES ============


from flask import send_from_directory

@app.route('/media/<path:filename>')
def serve_media(filename):
    return send_from_directory('static/media', filename)

@app.route("/")
def index():
    return render_template("index.html", tiktok_regions=TIKTOK_REGIONS, fb_countries=FACEBOOK_COUNTRIES, etsy_categories=ETSY_CATEGORIES)


@app.route("/api/search", methods=["POST"])
def api_search():
    """Search TikTok, Facebook, and Etsy products"""
    data = request.json
    search_term = data.get("search_term", "")
    tiktok_country = data.get("tiktok_country", "all")
    facebook_country = data.get("facebook_country", "ALL")
    max_ads = min(int(data.get("max_ads", 20)), 50)
    media_filter = data.get("media_filter", "all")
    include_tiktok = data.get("include_tiktok", True)
    include_facebook = data.get("include_facebook", True)
    include_etsy = data.get("include_etsy", True)
    include_amazon = data.get("include_amazon", True)

    if not search_term:
        return jsonify({"error": "Keyword required"}), 400

    if not APIFY_KEY:
        return jsonify({"error": "Apify key not configured"}), 400

    errors = []
    all_ads = []
    etsy_products = []
    amazon_products = []
    # Facebook Apify actor requires at least 10 results
    fb_max_ads = max(10, max_ads)

    # Run all platform searches in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}

        # TikTok
        if include_tiktok:
            futures[executor.submit(search_tiktok, search_term, tiktok_country, max_ads)] = ('tiktok', 'ads')
        # Facebook
        if include_facebook:
            futures[executor.submit(search_facebook, search_term, facebook_country, fb_max_ads)] = ('facebook', 'ads')
        # Etsy
        if include_etsy:
            futures[executor.submit(search_etsy, search_term, max_ads)] = ('etsy', 'products')
        # Amazon
        if include_amazon:
            futures[executor.submit(search_amazon, search_term, max_ads)] = ('amazon', 'products')

        for future in as_completed(futures):
            platform, result_type = futures[future]
            try:
                result, err = future.result()
                if err:
                    errors.append(f"{platform.capitalize()}: {err}")
                elif result_type == 'ads':
                    all_ads.extend(result)
                elif platform == 'etsy':
                    etsy_products = result
                elif platform == 'amazon':
                    amazon_products = result
            except Exception as e:
                errors.append(f"{platform}: {str(e)}")

    # Save Etsy/Amazon products to DB
    if etsy_products:
        from db import save_etsy_products
        save_etsy_products(etsy_products, search_term)
    if amazon_products:
        from db import save_amazon_products
        save_amazon_products(amazon_products, search_term)

    # Filter by media type
    if media_filter == "images_only":
        all_ads = [a for a in all_ads if a["has_images"] and not a["has_videos"]]
    elif media_filter == "videos_only":
        all_ads = [a for a in all_ads if a["has_videos"] and not a["has_images"]]

    # Enrich results with metadata from DB (timestamps, AI, keywords) in bulk
    from db import get_bulk_product_metadata
    platforms_to_enrich = [
        ('facebook', [a['id'] for a in all_ads if a['platform'] == 'facebook']),
        ('tiktok', [a['id'] for a in all_ads if a['platform'] == 'tiktok']),
        ('amazon', [p.get('id') or p.get('asin') for p in amazon_products]),
        ('etsy', [p.get('id') or p.get('listing_id') for p in etsy_products])
    ]
    
    for plt, ids in platforms_to_enrich:
        if ids:
            metadata_map = get_bulk_product_metadata(plt, ids)
            target_list = all_ads if plt in ['facebook', 'tiktok'] else (amazon_products if plt == 'amazon' else etsy_products)
            id_key = 'id' if plt in ['facebook', 'tiktok', 'etsy'] else 'asin'
            if plt == 'amazon': id_key = 'id' # amazon uses 'id' in our list usually
            
            for item in target_list:
                item_id = str(item.get(id_key) or item.get('id') or item.get('asin') or item.get('listing_id'))
                if item_id in metadata_map:
                    m = metadata_map[item_id]
                    item['ai_analysis'] = m.get('ai_analysis')
                    item['last_updated_at'] = m.get('last_updated_at')
                    item['created_at'] = m.get('created_at')

    # Sort results for the UI
    def sort_key(x):
        val = x.get('last_updated_at')
        if val is None: return ""
        return val.isoformat() if hasattr(val, 'isoformat') else str(val)

    all_ads.sort(key=sort_key, reverse=True)
    etsy_products.sort(key=sort_key, reverse=True)
    amazon_products.sort(key=sort_key, reverse=True)

    print(f"✅ Search Success: {len(all_ads)} ads, {len(etsy_products)} Etsy, {len(amazon_products)} Amazon. Sending to UI...")

    # Everything else happens in background
    def finalize_search_task(ads_copy, etsy_copy, amz_copy, term, tk_c, fb_c, auto_flag, m_ads):
        print(f"🚀 [Background] Thread started for keyword: {term}")
        try:
            # 1. Save results to DB
            from db import save_search, save_etsy_products, save_amazon_products
            search_id = save_search(term, tk_c, fb_c, "", m_ads, ads_copy)
            save_etsy_products(etsy_copy, term)
            save_amazon_products(amz_copy, term)
            print(f"📦 [Background] Results saved to DB (ID: {search_id}).")

            # 2. Advertiser Enrichment (limit concurrency to 3)
            fb_ads = [a for a in ads_copy if a.get("platform") == "facebook"]
            if fb_ads:
                page_ids = set()
                for ad in fb_ads:
                    raw = ad.get("raw", {}) or ad.get("_raw", {})
                    pid = raw.get("page_id") or raw.get("snapshot", {}).get("page_id")
                    if pid: page_ids.add(str(pid))
                
                if page_ids:
                    print(f"📊 [Background] Enriching {len(page_ids)} FB advertisers (parallel max 3)...")
                    ads_by_page = {}
                    def fetch_adv(pid):
                        try:
                            # Use search_facebook_by_advertiser from outer scope
                            res, err = search_facebook_by_advertiser([pid], 50)
                            return res if not err else None
                        except Exception as e:
                            print(f"⚠️ Enrichment error for {pid}: {e}")
                            return None

                    with ThreadPoolExecutor(max_workers=3) as executor:
                        results = list(executor.map(fetch_adv, page_ids))
                        for r in results:
                            if r: ads_by_page.update(r)
                    
                    if ads_by_page:
                        from db import save_fb_advertiser_ads
                        saved = save_fb_advertiser_ads(ads_by_page)
                        print(f"✅ [Background] Saved {saved} enrichment ads.")

            # 3. AI Analysis
            if auto_flag:
                print(f"🤖 [Auto-Analyze] Starting background analysis for {len(ads_copy) + len(etsy_copy) + len(amz_copy)} items...")
                all_items = ads_copy + etsy_copy + amz_copy
                
                # Use a single connection for all analysis saves in this thread
                from db import get_connection, release_connection, save_ai_analysis
                batch_conn = get_connection()
                try:
                    def analyze_one(it):
                        plt = it.get("platform")
                        iid = it.get("id") or it.get("asin") or it.get("listing_id")
                        if not it.get("ai_analysis"):
                            res = ai_analyzer.analyze_product(it.get("_raw", it), plt)
                            if res and "error" not in res:
                                save_ai_analysis(plt, iid, res, conn=batch_conn)
                        return it

                    with ThreadPoolExecutor(max_workers=5) as ai_exec:
                        list(ai_exec.map(analyze_one, all_items))
                finally:
                    release_connection(batch_conn)
                print(f"✅ [Auto-Analyze] Done.")
        except Exception as e:
            import traceback
            print(f"❌ [Background Error] {e}")
            traceback.print_exc()

    threading.Thread(
        target=finalize_search_task,
        args=(all_ads[:], etsy_products[:], amazon_products[:], search_term, tiktok_country, facebook_country, data.get("auto_analyze"), max_ads),
        daemon=True
    ).start()

    return jsonify({
        "ads": all_ads,
        "amazon_products": amazon_products,
        "etsy_products": etsy_products,
        "stats": {"total": len(all_ads) + len(amazon_products) + len(etsy_products)}
    })


@app.route("/api/history", methods=["GET"])
def api_history():
    """Get search history"""
    history = get_search_history(limit=50)
    return jsonify({"history": history})


@app.route("/api/history/<int:search_id>", methods=["GET"])
def api_history_detail(search_id):
    """Get full results for a past search"""
    from db import get_search_results, get_etsy_products_by_keyword, get_amazon_products_by_keyword
    from db import get_search_history

    results = get_search_results(search_id)

    # Get search info to know the keyword
    history = get_search_history(limit=200)
    search_info = next((h for h in history if h.get('id') == search_id), None)
    keyword = search_info.get('search_term', '') if search_info else ''

    # Get Etsy/Amazon products for this keyword
    etsy_products = []
    amazon_products = []
    if keyword:
        etsy_products = get_etsy_products_by_keyword(keyword)
        amazon_products = get_amazon_products_by_keyword(keyword)

    # Handle both old format ({"ad": ..., "raw": ...}) and new format (direct ad object)
    ads = [r["ad"] if isinstance(r, dict) and "ad" in r else r for r in results]
    stats = {
        "total": len(ads),
        "tiktok": len([a for a in ads if a.get("platform") == "tiktok"]),
        "facebook": len([a for a in ads if a.get("platform") == "facebook"]),
        "etsy": len(etsy_products),
        "amazon": len(amazon_products),
        "images_only": len([a for a in ads if a.get("has_images") and not a.get("has_videos")]),
        "videos_only": len([a for a in ads if a.get("has_videos") and not a.get("has_images")]),
        "both": len([a for a in ads if a.get("has_images") and a.get("has_videos")]),
    }
    return jsonify({
        "ads": ads,
        "etsy_products": etsy_products,
        "amazon_products": amazon_products,
        "stats": stats
    })


@app.route("/api/analysis/<platform>/<external_id>")
def api_get_analysis(platform, external_id):
    from db import get_product_metadata
    analysis = get_product_metadata(platform, external_id)
    return jsonify({"ai_analysis": analysis})

@app.route("/api/analyze_product", methods=["POST"])
def api_analyze_product():
    """Trigger AI analysis for a specific product or ad"""
    data = request.json
    platform = data.get("platform")
    product_id = data.get("id")
    raw_data = data.get("raw_data")

    if not platform or not product_id or not raw_data:
        return jsonify({"error": "Missing required fields"}), 400

    # Call AI Analyzer
    verdict = ai_analyzer.analyze_product(raw_data, platform)
    
    if "error" in verdict:
        return jsonify(verdict), 500

    # Save to DB
    save_ai_analysis(platform, product_id, verdict)

    return jsonify(verdict)


@app.route("/api/batch_analyze", methods=["POST"])
def api_batch_analyze():
    """Trigger AI analysis for multiple products"""
    data = request.json
    items = data.get("items", []) # List of {id, platform, raw_data}

    if not items:
        return jsonify({"error": "No items provided"}), 400

    results = []
    for item in items:
        verdict = ai_analyzer.analyze_product(item["raw_data"], item["platform"])
        if "error" not in verdict:
            save_ai_analysis(item["platform"], item["id"], verdict)
        results.append({
            "id": item["id"],
            "platform": item["platform"],
            "verdict": verdict
        })

    return jsonify({"results": results})


@app.route("/api/opportunities", methods=["GET"])
def api_opportunities():
    """Get product opportunities with optional filters"""
    status = request.args.get("status")
    tier = request.args.get("tier")
    limit = min(int(request.args.get("limit", 1000)), 5000)

    from db import get_opportunities
    opportunities = get_opportunities(status=status, tier=tier, limit=limit)

    # Enrich with landing page data
    from db import get_connection
    from psycopg2.extras import DictCursor
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)

    for opp in opportunities:
        opp_id = opp.get('opportunity_id')
        if opp_id:
            cursor.execute("""
                SELECT hero_headline, price_text, checkout_type, trust_signals, scrape_error
                FROM landing_pages WHERE opportunity_id = %s LIMIT 1
            """, (opp_id,))
            lp = cursor.fetchone()
            if lp:
                opp['landing_page'] = {
                    'hero_headline': lp['hero_headline'],
                    'price_text': lp['price_text'],
                    'checkout_type': lp['checkout_type'],
                    'trust_signals': lp['trust_signals'],
                    'scrape_error': lp['scrape_error']
                }
            else:
                opp['landing_page'] = None

    cursor.close()
    db.release_connection(conn)

    # Stats
    stats = {
        "total": len(opportunities),
        "high": len([o for o in opportunities if o.get("scaling_tier") == "high"]),
        "medium": len([o for o in opportunities if o.get("scaling_tier") == "medium"]),
        "low": len([o for o in opportunities if o.get("scaling_tier") == "low"]),
        "scaling": len([o for o in opportunities if o.get("is_scaling")]),
    }

    return jsonify({"opportunities": opportunities, "stats": stats})


@app.route("/api/advertisers/scaling", methods=["GET"])
def api_scaling_advertisers():
    """Get top scaling advertisers"""
    from db import get_scaling_advertisers
    min_score = int(request.args.get("min_score", 14))
    limit = min(int(request.args.get("limit", 20)), 100)
    advertisers = get_scaling_advertisers(min_score=min_score, limit=limit)
    return jsonify({"advertisers": advertisers})


@app.route("/api/facebook-advertiser/<page_id>", methods=["GET"])
def api_facebook_advertiser_ads(page_id):
    """
    Get all Facebook ads for a specific advertiser page_id.
    Optionally trigger a refresh by scraping via dz_omar/facebook-ads-scraper-pro.
    """
    if not APIFY_KEY:
        return jsonify({"error": "Apify key not configured"}), 400

    refresh = request.args.get("refresh", "false").lower() == "true"

    # If refresh requested, scrape new data
    if refresh:
        ads_by_page, error = search_facebook_by_advertiser(page_id)
        if error:
            return jsonify({"error": error}), 500

        from db import save_fb_advertiser_ads
        saved = save_fb_advertiser_ads(ads_by_page)
        print(f"📊 Scraped and saved {saved} ads for page_id {page_id}")

    # Return ads from database
    from db import get_fb_advertiser_ads
    ads = get_fb_advertiser_ads(page_id, limit=50)
    return jsonify({
        "page_id": page_id,
        "ad_count": len(ads),
        "ads": ads
    })


@app.route("/api/etsy/top", methods=["GET"])
def api_etsy_top():
    """Get top Etsy products by rating and reviews"""
    from db import get_top_etsy_products
    min_rating = float(request.args.get("min_rating", 4.5))
    min_reviews = int(request.args.get("min_reviews", 100))
    limit = min(int(request.args.get("limit", 30)), 100)
    products = get_top_etsy_products(min_rating=min_rating, min_reviews=min_reviews, limit=limit)
    return jsonify({"products": products})


@app.route("/api/etsy/shop/<shop_name>", methods=["GET"])
def api_etsy_shop(shop_name):
    """Get all products from an Etsy shop"""
    from db import get_etsy_products_by_shop
    products = get_etsy_products_by_shop(shop_name, limit=50)
    return jsonify({"shop_name": shop_name, "products": products})


@app.route("/api/etsy/search", methods=["POST"])
def api_etsy_search():
    """Search Etsy and return products (standalone)"""
    data = request.json
    search_term = data.get("search_term", "")
    if not search_term:
        return jsonify({"error": "Search term required"}), 400
    if not APIFY_KEY:
        return jsonify({"error": "Apify key not configured"}), 400

    products, error = search_etsy(search_term, max_items=20)
    if error:
        return jsonify({"error": error}), 500

    from db import save_etsy_products
    saved = save_etsy_products(products, search_term)
    return jsonify({"products": products, "saved": saved})


@app.route("/api/amazon/top", methods=["GET"])
def api_amazon_top():
    """Get top Amazon products by rating and reviews"""
    from db import get_top_amazon_products
    min_stars = float(request.args.get("min_stars", 4.0))
    min_reviews = int(request.args.get("min_reviews", 50))
    limit = min(int(request.args.get("limit", 30)), 100)
    products = get_top_amazon_products(min_stars=min_stars, min_reviews=min_reviews, limit=limit)
    return jsonify({"products": products})


@app.route("/api/ads/all", methods=["GET"])
def api_ads_all():
    """Get all global database raw ads and products"""
    from db import get_all_raw_data, get_all_fb_advertiser_counts
    try:
        data = get_all_raw_data(limit=500)
        fb_advertiser_counts = get_all_fb_advertiser_counts()

        # Calculate stats
        total = len(data["ads"])
        tiktok = len([a for a in data["ads"] if a["platform"] == "tiktok"])
        facebook = len([a for a in data["ads"] if a["platform"] == "facebook"])

        print(f"📊 API /api/ads/all: Sending {total} ads, {len(data['etsy_products'])} Etsy, {len(data['amazon_products'])} Amazon")
        return jsonify({
            "ads": data["ads"],
            "amazon_products": data["amazon_products"],
            "etsy_products": data["etsy_products"],
            "fb_advertiser_counts": fb_advertiser_counts,
            "stats": {
                "total": total,
                "tiktok": tiktok,
                "facebook": facebook,
                "etsy": len(data["etsy_products"]),
                "amazon": len(data["amazon_products"])
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/amazon/search", methods=["POST"])
def api_amazon_search():
    """Search Amazon and return products (standalone)"""
    data = request.json
    search_term = data.get("search_term", "")
    if not search_term:
        return jsonify({"error": "Search term required"}), 400
    if not APIFY_KEY:
        return jsonify({"error": "Apify key not configured"}), 400

    products, error = search_amazon(search_term, max_items=20)
    if error:
        return jsonify({"error": error}), 500

    from db import save_amazon_products
    saved = save_amazon_products(products, search_term)
    return jsonify({"products": products, "saved": saved})


@app.route("/api/facebook/import-manual", methods=["POST"])
def api_facebook_import_manual():
    """Manually import a Facebook ad by its Ad Library URL"""
    if not APIFY_KEY:
        return jsonify({"error": "Apify key not configured"}), 400

    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "URL required"}), 400

    if "facebook.com/ads/library" not in url:
        return jsonify({"error": "Invalid Facebook Ad Library URL"}), 400

    from scrapers import scrape_facebook_ads_by_urls
    ads, error = scrape_facebook_ads_by_urls([url])
    if error:
        return jsonify({"error": error}), 500

    if not ads:
        return jsonify({"error": "No ad found at this URL"}), 404

    from db import save_search, save_ai_analysis, save_product_opportunity
    import ai_analyzer
    import classifier
    
    # Save to database using a special keyword
    search_id = save_search("manual_import", "ALL", "ALL", "ALL", 1, ads)
    
    # Trigger AI analysis and classification for the imported ads
    results = []
    for ad in ads:
        # 1. AI Analysis
        verdict = ai_analyzer.analyze_product(ad["_raw"], "facebook")
        if "error" not in verdict:
            save_ai_analysis("facebook", ad["id"], verdict)
        
        # 2. Classification
        classification = classifier.classify_ad(ad)
        
        # 3. If it looks like a digital product, save as opportunity
        if classification['is_digital_product'] or verdict.get('confidence_score', 0) > 0.5:
            # Prepare data for save_product_opportunity
            opp_data = {
                'product_name': verdict.get('product_name') or ad.get('advertiser_name', 'Manual Product'),
                'product_category': classification.get('product_category') or verdict.get('category'),
                'product_description': verdict.get('description') or ad.get('body_text'),
                'price_text': verdict.get('price_text'),
                'price_amount': verdict.get('price_amount'),
                'advertiser_page_id': ad["_raw"].get("page_id") or ad["_raw"].get("pageId"),
                'advertiser_name': ad.get('advertiser_name'),
                'advertiser_platform': 'facebook',
                'advertiser_page_url': f"https://www.facebook.com/{ad['_raw'].get('page_id')}" if ad["_raw"].get("page_id") else None,
                'scaling_score': verdict.get('confidence_score', 0) * 10,
                'scaling_tier': 'high' if verdict.get('confidence_score', 0) > 0.7 else 'medium',
                'active_days': 1, # Default for manual
                'ad_count': 1,
                'is_scaling': verdict.get('confidence_score', 0) > 0.8,
                'landing_page_url': ad.get('link_url'),
                'status': 'new'
            }
            save_product_opportunity(opp_data)
            classification['is_opportunity'] = True
        
        results.append({
            "id": ad["id"],
            "verdict": verdict,
            "classification": classification
        })

    return jsonify({
        "success": True, 
        "ad_count": len(ads),
        "results": results,
        "ads": ads
    })


@app.route("/api/pipeline/run", methods=["POST"])
def api_run_pipeline():
    """Manually trigger the intelligence pipeline with filters"""
    import subprocess
    import tempfile
    import os
    import json
    
    data = request.json or {}
    
    # Save config to temp file
    fd, path = tempfile.mkstemp(suffix='.json', prefix='scoring_config_')
    try:
        with os.fdopen(fd, 'w') as tmp:
            json.dump(data, tmp)
        
        cmd = [".venv/bin/python3", "pipeline.py", "--config", path]
        
        # Run process and capture output
        print(f"🚀 Starting pipeline with config: {path}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        
        # Log to file for visibility
        with open("app.log", "a") as log_file:
            log_file.write(f"\n--- PIPELINE RUN {datetime.now()} ---\n")
            log_file.write(f"STDOUT:\n{stdout}\n")
            if stderr:
                log_file.write(f"STDERR:\n{stderr}\n")
            log_file.write("--- END PIPELINE RUN ---\n")

        if process.returncode != 0:
            print(f"❌ Pipeline failed: {stderr}")
            return jsonify({
                "status": "error",
                "error": stderr,
                "logs": stdout
            }), 500
            
        print("✅ Pipeline executed successfully")
        return jsonify({
            "status": "success",
            "message": "Pipeline executed successfully",
            "stdout": stdout
        })
    except Exception as e:
        print(f"🔥 Critical error in pipeline trigger: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500
    finally:
        if os.path.exists(path):
            os.remove(path)

@app.route("/api/pipeline/config/defaults", methods=["GET"])
def api_pipeline_defaults():
    """Return default scoring configuration"""
    defaults = {
        "tiktok": [
            { "field": "target_audience_min", "enabled": True, "min": 1000000, "weight": 8 },
            { "field": "duration_days", "enabled": True, "min": 7, "weight": 6 },
            { "field": "audit_status", "enabled": True, "value": 1, "weight": 5 },
            { "field": "ad_type_video", "enabled": False, "weight": 3 },
            { "field": "impression_min", "enabled": True, "min": 0, "weight": 4 },
            { "field": "target_countries", "enabled": False, "values": ["US","GB"], "weight": 5 },
            { "field": "advertiser_name_contains", "enabled": False, "keywords": [], "weight": 2 }
        ],
        "facebook": [
            { "field": "page_not_deleted", "enabled": True, "weight": 4 },
            { "field": "cta_type", "enabled": False, "values": ["SHOP_NOW","BUY_NOW"], "weight": 6 },
            { "field": "has_video", "enabled": False, "weight": 3 },
            { "field": "cards_count_min", "enabled": False, "min": 1, "weight": 2 },
            { "field": "eu_reach_min", "enabled": False, "min": 100, "weight": 5 },
            { "field": "targets_eu", "enabled": False, "weight": 4 },
            { "field": "no_violations", "enabled": True, "weight": 7 },
            { "field": "body_keywords", "enabled": False, "keywords": [], "weight": 5 },
            { "field": "title_keywords", "enabled": False, "keywords": [], "weight": 5 },
            { "field": "country_count_min", "enabled": False, "min": 2, "weight": 4 }
        ],
        "amazon": [
            { "field": "stars_min", "enabled": True, "min": 4.0, "weight": 8 },
            { "field": "reviews_min", "enabled": True, "min": 100, "weight": 7 },
            { "field": "brand_contains", "enabled": False, "keywords": [], "weight": 4 }
        ],
        "etsy": [
            { "field": "rating_min", "enabled": True, "min": 4.0, "weight": 8 },
            { "field": "reviews_min", "enabled": True, "min": 50, "weight": 7 }
        ],
        "fb_min_score": 5,
        "tt_min_score": 5,
        "amz_min_score": 5,
        "etsy_min_score": 5,
        "high_threshold": 20,
        "medium_threshold": 10,
        "scaling_threshold": 15,
        "min_ads_scaling": 5
    }
    return jsonify(defaults)


@app.route("/intelligence")
def intelligence_dashboard():
    """Product opportunities intelligence dashboard"""
    return render_template("intelligence.html")


@app.route("/api/scaling-advertisers")
def api_scaling():
    """Alias for scaling advertisers endpoint"""
    return api_scaling_advertisers()


# ================================================
# PRODUCT CRITERIA BACK-OFFICE API
# ================================================

@app.route("/api/criteria", methods=["GET"])
def api_criteria_list():
    """List all product criteria with optional filters"""
    platform = request.args.get("platform", "all")
    category = request.args.get("category")
    rule_type = request.args.get("type")
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"

    is_active = None if include_inactive else True
    from db import get_criteria
    criteria = get_criteria(platform=platform, category=category, rule_type=rule_type, is_active=is_active)
    return jsonify({"criteria": criteria})


@app.route("/api/criteria/stats", methods=["GET"])
def api_criteria_stats():
    """Get criteria statistics"""
    from db import get_criterion_stats
    stats = get_criterion_stats()
    return jsonify({"stats": stats})


@app.route("/api/criteria", methods=["POST"])
def api_criteria_save():
    """Create or update a criterion"""
    from db import save_criterion

    data = request.json
    required = ["rule_id", "rule_type", "platform"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    rule_id = data.get("rule_id")
    rule_type = data.get("rule_type")
    platform = data.get("platform")
    category = data.get("category")
    keyword = data.get("keyword")
    weight = data.get("weight")
    is_exclusion = data.get("is_exclusion", False)
    score_boost = data.get("score_boost", 0)
    config_key = data.get("config_key")
    config_value = data.get("config_value")
    is_active = data.get("is_active", True)
    display_order = data.get("display_order", 0)
    description = data.get("description", "")
    examples = data.get("examples", "")

    # Parse numeric fields
    try:
        weight = float(weight) if weight is not None else None
        score_boost = int(score_boost) if score_boost is not None else 0
        config_value = float(config_value) if config_value is not None else None
        display_order = int(display_order) if display_order is not None else 0
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid numeric value: {e}"}), 400

    criterion_id = save_criterion(
        rule_id, rule_type, platform, category, keyword,
        weight, is_exclusion, score_boost, config_key, config_value,
        is_active, display_order, description, examples
    )

    if criterion_id:
        return jsonify({"success": True, "id": criterion_id, "rule_id": rule_id})
    return jsonify({"error": "Failed to save criterion"}), 500


@app.route("/api/criteria/<rule_id>", methods=["DELETE"])
def api_criteria_delete(rule_id):
    """Delete (deactivate) a criterion"""
    from db import delete_criterion
    success = delete_criterion(rule_id)
    if success:
        return jsonify({"success": True, "rule_id": rule_id})
    return jsonify({"error": "Failed to delete criterion"}), 500


@app.route("/api/criteria/weights", methods=["GET"])
def api_criteria_weights():
    """Get weight configuration for classifier"""
    from db import get_criteria_weights
    weights = get_criteria_weights()
    return jsonify({"weights": weights})



# ============ AUTOMATION ROUTES ============

@app.route("/automation")
def automation_settings_page():
    return render_template("automation.html")

@app.route("/api/automation/settings", methods=["GET"])
def api_get_automation_settings():
    settings = db.get_automation_settings()
    return jsonify(settings)

@app.route("/api/automation/settings", methods=["POST"])
def api_update_automation_settings():
    data = request.json
    success = db.update_automation_settings(data)
    return jsonify({"success": success})

@app.route("/api/automation/keywords", methods=["GET"])
def api_get_automation_keywords():
    keywords = db.get_automation_keywords()
    return jsonify(keywords)

@app.route("/api/automation/keywords", methods=["POST"])
def api_add_automation_keyword():
    data = request.json
    success = db.add_automation_keyword(data.get('category'), data.get('keyword'))
    return jsonify({"success": success})

@app.route("/api/automation/keywords/<int:keyword_id>", methods=["DELETE"])
def api_delete_automation_keyword(keyword_id):
    success = db.delete_automation_keyword(keyword_id)
    return jsonify({"success": success})


# ============ SYSTEM PROMPT ROUTES ============

@app.route("/system_prompt")
def system_prompt_page():
    return render_template("system_prompt.html")

@app.route("/api/system_prompt", methods=["GET"])
def api_get_system_prompt():
    prompt = db.get_setting("system_prompt", ai_analyzer.SYSTEM_PROMPT)
    return jsonify({"system_prompt": prompt})

@app.route("/api/system_prompt", methods=["POST"])
def api_update_system_prompt():
    data = request.json
    new_prompt = data.get("system_prompt")
    if not new_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    # Get previous value for history
    previous = db.get_setting("system_prompt", "")
    if previous and previous != new_prompt:
        db.save_system_prompt_history(previous, new_prompt)

    success = db.set_setting("system_prompt", new_prompt)
    # Also update in system_prompts table if exists
    try:
        import ai_analyzer
        ai_analyzer.clear_prompt_cache()
    except:
        pass
    return jsonify({"success": success})

@app.route("/api/landing-pages/scrape", methods=["POST"])
def api_scrape_landing_pages():
    """Scrape one or more landing pages"""
    from landing_page_scraper import scrape_landing_page, save_landing_page, scrape_batch

    data = request.json
    items = data.get('items', [])

    if not items:
        return jsonify({"error": "No items provided"}), 400

    # Single or batch
    if len(items) == 1:
        item = items[0]
        result = scrape_landing_page(item['ad_archive_id'], item['link_url'])
        save_landing_page(item['ad_archive_id'], item['link_url'], metadata=result)
        return jsonify(result)
    else:
        results = scrape_batch(items)
        return jsonify({"results": results, "total": len(results)})


@app.route("/api/landing-pages/<ad_archive_id>", methods=["GET"])
def api_get_landing_page(ad_archive_id):
    """Get landing page info for an ad"""
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id, ad_archive_id, source_url, domain, headline, price_amount, price_text,
                   currency, checkout_type, status, scrape_error, local_html_path, scraped_at, r2_url
            FROM landing_pages WHERE ad_archive_id = %s
            ORDER BY scraped_at DESC LIMIT 1
        """, (ad_archive_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        return jsonify({
            "id": row[0],
            "ad_archive_id": row[1],
            "source_url": row[2],
            "domain": row[3],
            "headline": row[4],
            "price_amount": float(row[5]) if row[5] else None,
            "price_text": row[6],
            "currency": row[7],
            "checkout_type": row[8],
            "status": row[9],
            "scrape_error": row[10],
            "local_html_path": row[11],
            "scraped_at": row[12].isoformat() if row[12] else None,
            "r2_url": row[13]
        })
    finally:
        cursor.close()
        db.release_connection(conn)


@app.route("/api/landing-pages/<ad_archive_id>/download", methods=["GET"])
def api_download_landing_page(ad_archive_id):
    """Download landing page as ZIP"""
    from landing_page_scraper import create_download_zip
    import zipfile

    # Check if we have a scraped page
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT local_assets_path FROM landing_pages
            WHERE ad_archive_id = %s AND status = 'scraped'
            ORDER BY scraped_at DESC LIMIT 1
        """, (ad_archive_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        db.release_connection(conn)

    if not row or not row[0]:
        return jsonify({"error": "No scraped landing page found"}), 404

    assets_path = row[0]
    zip_path = create_download_zip(ad_archive_id)

    if not zip_path or not os.path.exists(zip_path):
        return jsonify({"error": "Failed to create ZIP"}), 500

    return send_file(zip_path, as_attachment=True, download_name=f"landing_page_{ad_archive_id}.zip")


@app.route("/api/landing-pages/<ad_archive_id>/view", methods=["GET"])
def api_view_landing_page(ad_archive_id):
    """View the scraped landing page HTML"""
    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT local_html_path FROM landing_pages
            WHERE ad_archive_id = %s AND status = 'scraped'
            ORDER BY scraped_at DESC LIMIT 1
        """, (ad_archive_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        db.release_connection(conn)

    if not row or not row[0]:
        return jsonify({"error": "No scraped landing page found"}), 404

    html_path = row[0]
    if not os.path.exists(html_path):
        return jsonify({"error": "HTML file not found"}), 404

    return send_file(html_path, mimetype='text/html')


@app.route("/api/landing-pages/scrape-pending", methods=["POST"])
def api_scrape_pending():
    """Scrape all ads that have link_url but no landing page yet"""
    from landing_page_scraper import scrape_landing_page, save_landing_page

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        # Find ads with link_url in cards that don't have a landing page yet
        cursor.execute("""
            SELECT DISTINCT a.ad_archive_id, ac.link_url
            FROM ads a
            JOIN ad_cards ac ON a.ad_archive_id = ac.ad_archive_id
            LEFT JOIN landing_pages lp ON a.ad_archive_id = lp.ad_archive_id
            WHERE ac.link_url IS NOT NULL
              AND ac.link_url NOT IN ('N/A', '', 'null', 'undefined')
              AND lp.id IS NULL
            LIMIT 50
        """)
        pending = cursor.fetchall()
    finally:
        cursor.close()
        db.release_connection(conn)

    if not pending:
        return jsonify({"message": "No pending landing pages to scrape", "count": 0})

    items = [{'ad_archive_id': row[0], 'link_url': row[1]} for row in pending]
    from landing_page_scraper import scrape_batch
    results = scrape_batch(items)

    return jsonify({
        "message": f"Scraped {len(results)} landing pages",
        "count": len(results),
        "results": results
    })


@app.route("/api/landing-pages/<ad_archive_id>/rebrand", methods=["POST"])
def api_rebrand_landing_page(ad_archive_id):
    """Rebrand a scraped landing page using AI"""
    import rebrand as rebrand_service
    import importlib
    importlib.reload(rebrand_service)

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT local_html_path FROM landing_pages
            WHERE ad_archive_id = %s AND status = 'scraped'
            ORDER BY scraped_at DESC LIMIT 1
        """, (ad_archive_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        db.release_connection(conn)

    if not row or not row[0]:
        return jsonify({"error": "No scraped landing page found"}), 404

    html_path = row[0]
    if not os.path.exists(html_path):
        return jsonify({"error": "HTML file not found"}), 404

    # Read the HTML
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        raw_html = f.read()

    if not raw_html:
        return jsonify({"error": "Empty HTML file"}), 400

    # Run rebrand
    try:
        # Use the new high-quality rebrand V2
        result = rebrand_service.rebrand_landing_v2(raw_html)
        
        if not result.get('success'):
            return jsonify({"error": result.get('error', 'Rebrand failed')}), 500

        # Save rebranded HTML and payment page to rebrand directory
        from datetime import datetime
        import shutil
        
        original_dir = os.path.dirname(html_path)
        rebrand_dir = os.path.join("static/landing_pages", f"{ad_archive_id}_rebranded")
        os.makedirs(rebrand_dir, exist_ok=True)
        rebrand_html_path = os.path.join(rebrand_dir, "index.html")
        checkout_html_path = os.path.join(rebrand_dir, "checkout.html")

        # Copy all assets from original directory to rebrand directory (excluding HTML files)
        if os.path.exists(original_dir):
            for item in os.listdir(original_dir):
                s = os.path.join(original_dir, item)
                d = os.path.join(rebrand_dir, item)
                if os.path.isfile(s) and not item.endswith('.html'):
                    shutil.copy2(s, d)
                elif os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)

        with open(rebrand_html_path, 'w', encoding='utf-8') as f:
            f.write(result.get("cleaned_html", ""))

        return jsonify({
            "success": True,
            "brand_name": result.get("brand_name", ""),
            "brand_tagline": result.get("brand_tagline", ""),
            "new_price": result.get("new_price", ""),
            "brand_color": result.get("brand_color", "#FF6B35"),
            "logo_text": result.get("logo_text", ""),
            "cta_text": result.get("cta_text", "Shop Now"),
            "slug": result.get("slug", ""),
            "local_html_path": rebrand_html_path,
            "checkout_url": result.get("stripe_url", "#"),
            "preview_url": f"/api/landing-pages/{ad_archive_id}/rebrand/preview"
        })
    except Exception as e:
        import traceback
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/api/landing-pages/<ad_archive_id>/rebrand/preview", methods=["GET"])
def api_rebrand_preview(ad_archive_id):
    """Preview the rebranded landing page"""
    rebrand_dir = os.path.join("static/landing_pages", f"{ad_archive_id}_rebranded")
    rebrand_html_path = os.path.join(rebrand_dir, "index.html")

    if not os.path.exists(rebrand_html_path):
        return jsonify({"error": "No rebranded page found. Run /rebrand first."}), 404

    return send_file(rebrand_html_path, mimetype='text/html')


@app.route("/api/landing-pages/<ad_archive_id>/rebrand/publish", methods=["POST"])
def api_rebrand_publish(ad_archive_id):
    """Publish the rebranded landing page to VPS"""
    import rebrand as rebrand_service

    rebrand_dir = os.path.join("static/landing_pages", f"{ad_archive_id}_rebranded")
    rebrand_html_path = os.path.join(rebrand_dir, "index.html")

    if not os.path.exists(rebrand_html_path):
        return jsonify({"error": "No rebranded page found. Run /rebrand first."}), 404

    with open(rebrand_html_path, 'r', encoding='utf-8', errors='ignore') as f:
        html_content = f.read()

    # Get slug from rebrand data if available, otherwise generate from ad_archive_id
    slug = ad_archive_id[:50].lower().replace(" ", "-").replace("_", "-")
    slug = re.sub(r'[^a-z0-9\-_]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')

    result = rebrand_service.publish_to_vps(slug=slug, html_content=html_content)

    if result.get("success"):
        return jsonify({
            "success": True,
            "url": result.get("url", ""),
            "slug": slug
        })
    else:
        return jsonify({"error": result.get("error", "Publish failed")}), 500


@app.route("/api/landing-pages/<ad_archive_id>/rebrand/view", methods=["GET"])
def api_rebrand_view(ad_archive_id):
    """View the rebranded landing page in browser"""
    rebrand_dir = os.path.join("static/landing_pages", f"{ad_archive_id}_rebranded")
    rebrand_html_path = os.path.join(rebrand_dir, "index.html")

    if not os.path.exists(rebrand_html_path):
        return jsonify({"error": "No rebranded page found. Run /rebrand first."}), 404

    return send_file(rebrand_html_path, mimetype='text/html')

@app.route("/api/landing-pages/<ad_archive_id>/rebrand/<path:filename>")
def serve_rebrand_assets(ad_archive_id, filename):
    """Serve assets for a rebranded landing page"""
    rebrand_dir = os.path.join("static/landing_pages", f"{ad_archive_id}_rebranded")
    return send_from_directory(rebrand_dir, filename)

@app.route("/api/landing-pages/<ad_archive_id>/view/<path:filename>")
def serve_original_assets(ad_archive_id, filename):
    """Serve assets for an original scraped landing page"""
    original_dir = os.path.join("static/landing_pages", ad_archive_id)
    return send_from_directory(original_dir, filename)


if __name__ == "__main__":
    init_db()
    
    # Start automation worker in a background thread
    try:
        from automation_worker import start_automation_worker
        threading.Thread(target=start_automation_worker, daemon=True).start()
        print("🚀 Automation worker started in background thread.")
    except Exception as e:
        print(f"⚠️ Could not start automation worker: {e}")

    print("=" * 50)
    print("AD INTELLIGENCE - TikTok + Facebook (via Apify)")
    print("=" * 50)
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False)
