import os
import time
import requests
import json
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

APIFY_KEY = os.getenv("APIFY_KEY")

# Apify Actor IDs
TIKTOK_ACTOR = "data_xplorer~tiktok-ads-library-fast"
FACEBOOK_ACTOR = "curious_coder~facebook-ads-library-scraper"
FACEBOOK_ADVERTISER_ACTOR = "20nRTxLD3a3jIlZbZ"  # facebook-ads-scraper-pro
ETSY_ACTOR = "JOUStaVgex0lqbRnk"
AMAZON_ACTOR = "junglee~Amazon-crawler"

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

def start_apify_actor(actor_id, input_data):
    """Start an Apify actor and wait for completion"""
    resp = requests.post(
        f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_KEY}",
        json=input_data,
        timeout=30
    )

    if resp.status_code not in [200, 201]:
        return {"error": f"Failed to start: {resp.status_code} - {resp.text}"}

    result = resp.json()
    run_id = result.get("data", {}).get("id")

    if not run_id:
        return {"error": f"No run ID returned: {result}"}

    # Poll for completion
    for i in range(24):  # max 120 seconds
        time.sleep(5)
        status_resp = requests.get(
            f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}?token={APIFY_KEY}",
            timeout=30
        )
        status_data = status_resp.json()
        status = status_data.get("data", {}).get("status", "")

        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "ABORTED", "TIMED_OUT"]:
            return {"error": f"Actor failed with status: {status}"}

    # Get dataset
    run_resp = requests.get(
        f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}?token={APIFY_KEY}",
        timeout=30
    )
    run_info = run_resp.json()
    dataset_id = run_info.get("data", {}).get("defaultDatasetId")

    if not dataset_id:
        return {"error": "No dataset returned"}

    items_resp = requests.get(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_KEY}",
        timeout=60
    )

    return {"ads": items_resp.json()}

def search_tiktok(search_term, region="all", max_ads=20):
    input_data = {
        "fetchDetails": True,
        "proxyConfiguration": {"useApifyProxy": True},
        "query": search_term,
        "queryType": "1",
        "region": region,
        "startDate": "2024-01-01",
        "maxAds": min(max_ads, 100)
    }
    result = start_apify_actor(TIKTOK_ACTOR, input_data)
    if "error" in result: return [], result["error"]
    
    ads = []
    for item in result.get("ads", []):
        if "error" in item: continue
        image_urls = []
        videos = []
        media = item.get("Ad Media", [])
        for m in media:
            is_vid = False
            if isinstance(m, str):
                is_vid = m.lower().startswith("video")
                url = m.split(": ", 1)[1] if ": " in m else m
            else:
                url = m.get("Image 1") or m.get("Cover 1") or m.get("Video 1") or ""
                is_vid = bool(m.get("Video 1"))
            
            if not url: continue
            if is_vid or "video" in url.lower() or ".mp4" in url.lower(): 
                videos.append({"url": url})
            else: 
                image_urls.append(url)
        
        ad_id = item.get("AD ID", "") or item.get("id", "")
        # Extraire l'avatar de l'annonceur si possible
        advertiser_avatar = item.get("Advertiser Logo") or item.get("Advertiser Profile") or ""
        
        ad_entry = {
            "id": ad_id, "platform": "tiktok", "image_urls": image_urls, "videos": videos,
            "has_images": len(image_urls) > 0, "has_videos": len(videos) > 0,
            "first_shown_date": item.get("Ad Dates", [{}])[0].get("FirstShown", "N/A"),
            "last_shown_date": item.get("Ad Dates", [{}])[0].get("LastShown", "N/A"),
            "reach": item.get("Ad Audience", "N/A"),
            "advertiser_name": item.get("Advertiser Name", "Unknown"),
            "advertiser_avatar": advertiser_avatar,
            "body_text": item.get("Ad Sponsor", "") or item.get("Advertiser Name", ""),
            "_raw": item
        }
        ads.append(ad_entry)
    return ads, None

def search_facebook(search_term, country="ALL", max_ads=20):
    search_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q={search_term}&search_type=keyword_unordered"
    input_data = {
        "count": min(max_ads, 100), "scrapeAdDetails": True,
        "scrapePageAds.activeStatus": "all", "scrapePageAds.countryCode": "ALL",
        "urls": [{"url": search_url}]
    }
    result = start_apify_actor(FACEBOOK_ACTOR, input_data)
    if "error" in result: return [], result["error"]
    
    ads = []
    for item in result.get("ads", []):
        if "error" in item: continue
        snapshot = item.get("snapshot", {})
        cards = snapshot.get("cards", [])
        image_urls = []
        videos = []
        for card in cards:
            if card.get("originalImageUrl"): image_urls.append(card.get("originalImageUrl"))
            if card.get("videoSdUrl") or card.get("videoHdUrl"):
                videos.append({"url": card.get("videoHdUrl") or card.get("videoSdUrl")})
        for img in snapshot.get("images", []): 
            if img and img not in image_urls: image_urls.append(img)
        
        ad_id = item.get("ad_archive_id") or item.get("adArchiveId", "")
        ad_entry = {
            "id": ad_id, "platform": "facebook", "image_urls": image_urls, "videos": videos,
            "has_images": len(image_urls) > 0, "has_videos": len(videos) > 0,
            "first_shown_date": item.get("start_date_formatted", "N/A")[:10],
            "last_shown_date": item.get("end_date_formatted", "N/A")[:10],
            "status": "active" if item.get("is_active") else "inactive",
            "reach": item.get("impressions_with_index", {}).get("impressionsText", "N/A"),
            "advertiser_name": item.get("page_name", "Unknown"),
            "body_text": cards[0].get("body", "") if cards else snapshot.get("body", ""),
            "_raw": item
        }
        ads.append(ad_entry)
    return ads, None

def search_facebook_by_advertiser(page_ids, max_results_per_query=200):
    """
    Search Facebook ads by advertiser page IDs using dz_omar/facebook-ads-scraper-pro.
    page_ids: list of page_id strings (e.g. ["726736070734872"])
    Returns: dict with page_id -> list of ads
    """
    if not page_ids:
        return {}, None

    # Build input for the actor - search up to max_results_per_query ads per advertiser
    # Note: maxResultsPerQuery must be >= 10
    input_data = {
        "adType": "ALL",
        "enrichWithAdDetails": False,
        "maxResultsPerQuery": max(10, min(max_results_per_query, 200)),
        "searchAdvertisers": page_ids if isinstance(page_ids, list) else [page_ids]
    }

    result = start_apify_actor(FACEBOOK_ADVERTISER_ACTOR, input_data)
    if "error" in result:
        return {}, result["error"]

    ads_by_page = {}
    items = result.get("ads", [])

    for item in items:
        if not item or "error" in str(item):
            continue

        # Get the page_id from the ad data
        ad_page_id = str(item.get("page_id", "") or item.get("pageId", ""))
        if not ad_page_id:
            continue

        # Parse media
        media = item.get("media", {}) or {}
        primary_thumbnail = media.get("primary_thumbnail", "")

        # Build the ad entry (similar structure to other search functions)
        ad_entry = {
            "id": item.get("id", "") or item.get("ad_archive_id", ""),
            "platform": "facebook",
            "ad_url": item.get("ad_url", ""),
            "page_name": item.get("page_name", "Unknown"),
            "title": item.get("title", ""),
            "text": item.get("text", ""),
            "media_type": media.get("type", "image"),
            "primary_thumbnail": primary_thumbnail,
            "is_active": item.get("is_active", True),
            "page_likes": item.get("page_likes", 0),
            "platforms": item.get("platforms", []),
            "start_date": item.get("start_date", ""),
            "end_date": item.get("end_date", ""),
            "ad_category": item.get("ad_category", "UNKNOWN"),
            "scraped_at": item.get("scraped_at", ""),
            "_raw": item
        }

        if ad_page_id not in ads_by_page:
            ads_by_page[ad_page_id] = []
        ads_by_page[ad_page_id].append(ad_entry)

    return ads_by_page, None

def search_etsy(search_term, max_items=20):
    input_data = {"searchQueries": [search_term], "maxItems": min(max_items, 50)}
    result = start_apify_actor(ETSY_ACTOR, input_data)
    if "error" in result: return [], result["error"]
    
    products = []
    items = result.get("ads", [])
    for item in items:
        if not item or "error" in str(item): continue
        products.append({
            "id": item.get("listingId", "") or item.get("id", ""),
            "title": item.get("title", ""), 
            "price": item.get("price", "") or item.get("price_value", ""),
            "shop_name": item.get("shopName", "") or item.get("shop_name", ""), 
            "rating": item.get("rating", 0) or item.get("stars", 0) or item.get("rating_value", 0),
            "review_count": item.get("reviewCount") or item.get("reviewsCount") or item.get("reviews_count") or item.get("reviews", 0),
            "imageUrl": item.get("thumbnailImage") or item.get("thumbnail") or item.get("image") or item.get("mainImage") or item.get("imageUrl") or "",
            "url": item.get("url", ""), 
            "platform": "etsy", 
            "_raw": item
        })
    return products, None

def search_amazon(search_term, max_items=20):
    input_data = {
        "categoryOrProductUrls": [{"url": f"https://www.amazon.com/s?k={search_term}"}],
        "maxItemsPerStartUrl": min(max_items, 50),
        "scrapeProductDetails": True
    }
    result = start_apify_actor(AMAZON_ACTOR, input_data)
    if "error" in result: return [], result["error"]
    
    products = []
    items = result.get("ads", [])
    for item in items:
        if not item or "error" in str(item): continue
        products.append({
            "id": item.get("asin", "") or item.get("id", ""),
            "title": item.get("title", ""), 
            "brand": item.get("brand", "Unknown"),
            "price": item.get("price", {}).get("value") if isinstance(item.get("price"), dict) else item.get("price", "N/A"),
            "stars": item.get("stars", 0) or item.get("rating", 0),
            "reviews_count": item.get("reviewsCount", 0) or item.get("reviews_count", 0) or item.get("reviews", 0),
            "thumbnail": item.get("thumbnailImage") or item.get("thumbnail") or item.get("image") or item.get("mainImage") or "",
            "url": item.get("url", ""),
            "platform": "amazon", 
            "_raw": item
        })
    return products, None
