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
from flask import Flask, render_template, request, jsonify, send_from_directory
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
    max_ads = int(data.get("max_ads", 10))
    # Facebook Apify actor requires at least 10 results
    fb_max_ads = max(10, max_ads)

    # Run all platform searches in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}

        # TikTok
        futures[executor.submit(search_tiktok, search_term, tiktok_country, max_ads)] = ('tiktok', 'ads')
        # Facebook
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

    # Enrich results with metadata from DB (timestamps, AI, keywords)
    from db import get_product_metadata
    for ad in all_ads:
        meta = get_product_metadata(ad['platform'], ad['id'])
        if meta:
            ad['ai_analysis'] = meta.get('ai_analysis')
            ad['last_updated_at'] = meta.get('last_updated_at')
            ad['created_at'] = meta.get('created_at')
            ad['search_keywords'] = meta.get('search_keywords', [])
    
    for p in etsy_products:
        meta = get_product_metadata('etsy', p.get('id'))
        if meta:
            p['ai_analysis'] = meta.get('ai_analysis')
            p['last_updated_at'] = meta.get('last_updated_at')
            p['created_at'] = meta.get('created_at')
            p['search_keywords'] = meta.get('search_keywords', [])

    for p in amazon_products:
        meta = get_product_metadata('amazon', p.get('id'))
        if meta:
            p['ai_analysis'] = meta.get('ai_analysis')
            p['last_updated_at'] = meta.get('last_updated_at')
            p['created_at'] = meta.get('created_at')
            p['search_keywords'] = meta.get('search_keywords', [])

    # Sort results by last_updated_at for the frontend response
    all_ads.sort(key=lambda x: x.get('last_updated_at') or '', reverse=True)
    etsy_products.sort(key=lambda x: x.get('last_updated_at') or '', reverse=True)
    amazon_products.sort(key=lambda x: x.get('last_updated_at') or '', reverse=True)

    print(f"✅ Search Success: {len(all_ads)} ads ({len([a for a in all_ads if a['platform']=='facebook'])} FB, {len([a for a in all_ads if a['platform']=='tiktok'])} TT), {len(etsy_products)} Etsy, {len(amazon_products)} Amazon")

    # Save to history DB
    search_id = save_search(search_term, tiktok_country, facebook_country, "", max_ads, all_ads)

    # Optional: Run AI analysis on ALL scraped results
    if data.get("auto_analyze"):
        print(f"🤖 [Auto-Analyze] Processing all scraped results...")
        all_to_analyze = []
        if all_ads:
            all_to_analyze.extend(all_ads)
        if etsy_products:
            all_to_analyze.extend(etsy_products)
        if amazon_products:
            all_to_analyze.extend(amazon_products)
            
        def analyze_and_save(it):
            plt = it.get("platform")
            iid = it.get("id") or it.get("asin") or it.get("listing_id")
            if not it.get("ai_analysis"):
                res = ai_analyzer.analyze_product(it.get("_raw", it), plt)
                if res and "error" not in res:
                    save_ai_analysis(plt, iid, res)
                    it["ai_analysis"] = res
            return it

        with ThreadPoolExecutor(max_workers=8) as ai_executor:
            list(ai_executor.map(analyze_and_save, all_to_analyze))

    # Stats
    stats = {
        "total": len(all_ads),
        "tiktok": len([a for a in all_ads if a.get("platform") == "tiktok"]),
        "facebook": len([a for a in all_ads if a.get("platform") == "facebook"]),
        "etsy": len(etsy_products),
        "amazon": len(amazon_products),
        "images_only": len([a for a in all_ads if a.get("has_images") and not a.get("has_videos")]),
        "videos_only": len([a for a in all_ads if a.get("has_videos") and not a.get("has_images")]),
        "both": len([a for a in all_ads if a.get("has_images") and a.get("has_videos")]),
    }

    return jsonify({
        "ads": all_ads,
        "etsy_products": etsy_products,
        "amazon_products": amazon_products,
        "stats": stats,
        "search_term": search_term,
        "search_id": search_id,
        "errors": errors if errors else None
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
    from db import get_ai_analysis
    analysis = get_ai_analysis(platform, external_id)
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
    conn.close()

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
    from db import get_all_raw_data
    try:
        data = get_all_raw_data(limit=500)
        
        # Calculate stats
        total = len(data["ads"])
        tiktok = len([a for a in data["ads"] if a["platform"] == "tiktok"])
        facebook = len([a for a in data["ads"] if a["platform"] == "facebook"])
        
        print(f"📊 API /api/ads/all: Sending {total} ads, {len(data['etsy_products'])} Etsy, {len(data['amazon_products'])} Amazon")
        return jsonify({
            "ads": data["ads"],
            "amazon_products": data["amazon_products"],
            "etsy_products": data["etsy_products"],
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
    
    success = db.set_setting("system_prompt", new_prompt)
    return jsonify({"success": success})

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
