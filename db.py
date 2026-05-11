import os
import json
import psycopg2
from psycopg2.extras import DictCursor
from psycopg2.extras import Json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://anon-404@localhost/analyse_ad")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def stringify(val):
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    return str(val)

def is_r2_url(url):
    """Check if URL is a Cloudflare R2 public URL"""
    if not url or not isinstance(url, str):
        return False
    return url.startswith('http://') or url.startswith('https://')

def get_media_url(local_path, platform="facebook", ad_id=None):
    """
    Get the correct media URL whether stored as local path or R2 URL.
    Compatible with both local storage and R2 cloud storage.
    """
    if not local_path:
        return ""

    if is_r2_url(local_path):
        return local_path  # Already a full R2 URL

    # Local path format - construct frontend path
    if platform == "facebook" and ad_id:
        parts = local_path.split('/')
        filename = parts[-1] if parts else local_path
        return f"/media/fb/{ad_id}/{filename}"
    elif platform == "tiktok" and ad_id:
        parts = local_path.split('/')
        filename = parts[-1] if parts else local_path
        return f"/media/tiktok/{ad_id}/{filename}"

    return f"/media/{local_path}"

def init_db():
    # Execute schema.sql if needed, or assume it's run externally
    pass

def get_setting(key, default=None):
    """Retrieve a setting from the settings table"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT value FROM settings WHERE key = %s", (key,))
        row = cursor.fetchone()
        if row:
            return row[0]
        return default
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return default
    finally:
        cursor.close()
        conn.close()

def set_setting(key, value):
    """Update or insert a setting in the settings table"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO settings (key, value, updated_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (key) DO UPDATE SET
                value = EXCLUDED.value,
                updated_at = CURRENT_TIMESTAMP
        """, (key, value))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error setting {key}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()




def save_etsy_products(products, search_keyword):
    """Save Etsy products to database"""
    if not products:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0
    try:
        for p in products:
            listing_id = p.get('id', '') or p.get('listing_id', '')
            if not listing_id:
                continue  # Skip products without listing ID

            # Parse price amount
            price_amount = None
            try:
                price_str = str(p.get('price', '')).replace('$', '').replace(',', '').strip()
                if price_str:
                    price_amount = float(price_str)
            except:
                pass

            # Parse rating
            rating_val = None
            try:
                rating_val = float(p.get('rating', 0)) if p.get('rating') else None
            except:
                pass

            # Parse review count
            review_val = None
            try:
                rc_raw = p.get('review_count') or p.get('reviewCount') or p.get('reviews') or p.get('reviewsCount')
                if isinstance(rc_raw, (int, float)):
                    review_val = int(rc_raw)
                else:
                    rc = str(rc_raw or '').replace(",", "").strip()
                    if rc.isdigit():
                        review_val = int(rc)
            except:
                pass

            cursor.execute("""
                INSERT INTO etsy_products
                (listing_id, title, price, currency, price_amount, shop_name, rating, review_count, url, search_keyword, image_url, search_keywords, raw_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (listing_id)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    price = EXCLUDED.price,
                    price_amount = EXCLUDED.price_amount,
                    rating = EXCLUDED.rating,
                    review_count = EXCLUDED.reVIEW_COUNT,
                    image_url = EXCLUDED.image_url,
                    last_updated_at = CURRENT_TIMESTAMP,
                    search_keywords = (SELECT array_agg(DISTINCT k) FROM unnest(COALESCE(etsy_products.search_keywords, '{}') || EXCLUDED.search_keywords) k),
                    raw_json = EXCLUDED.raw_json
            """, (
                listing_id,
                p.get('title', ''),
                p.get('price', ''),
                p.get('currency', '$'),
                price_amount,
                p.get('shop_name', ''),
                rating_val,
                review_val,
                p.get('url', ''),
                search_keyword,
                p.get('imageUrl') or p.get('mainImage') or p.get('image') or p.get('thumbnail') or '',
                [search_keyword],
                Json(p)
            ))
            saved += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving Etsy products: {e}")
    finally:
        cursor.close()
        conn.close()
    return saved


def get_top_etsy_products(min_rating=4.5, min_reviews=100, limit=50):
    """Get best performing Etsy products by rating and review count"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM etsy_products
            WHERE rating >= %s AND review_count >= %s
            ORDER BY rating DESC, review_count DESC
            LIMIT %s
        """, (min_rating, min_reviews, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_etsy_products_by_shop(shop_name, limit=20):
    """Get all products from a specific Etsy shop"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM etsy_products
            WHERE shop_name = %s
            ORDER BY rating DESC, review_count DESC
            LIMIT %s
        """, (shop_name, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_etsy_products_by_keyword(keyword, limit=50):
    """Get Etsy products saved for a specific search keyword"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM etsy_products
            WHERE search_keyword = %s
            ORDER BY rating DESC, review_count DESC
            LIMIT %s
        """, (keyword, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_amazon_products_by_keyword(keyword, limit=50):
    """Get Amazon products saved for a specific search keyword"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM amazon_products
            WHERE search_keyword = %s
            ORDER BY stars DESC, reviews_count DESC
            LIMIT %s
        """, (keyword, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def save_amazon_products(products, search_keyword):
    """Save Amazon products to database"""
    if not products:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    saved = 0
    try:
        for p in products:
            asin = p.get('asin', '') or p.get('id', '')
            if not asin:
                continue

            # Parse stars
            stars_val = p.get('stars_float')
            if stars_val is None or stars_val == 0:
                try:
                    import re
                    stars_str = str(p.get('stars', 0))
                    m = re.search(r'([\d\.]+)', stars_str)
                    stars_val = float(m.group(1)) if m else None
                except:
                    stars_val = None

            # Parse reviews
            reviews_val = 0
            try:
                rc_raw = p.get('reviews_count') or p.get('reviewsCount') or p.get('reviews')
                if isinstance(rc_raw, (int, float)):
                    reviews_val = int(rc_raw)
                else:
                    import re
                    reviews_str = str(rc_raw or '0')
                    reviews_str = re.sub(r'[^\d]', '', reviews_str)
                    reviews_val = int(reviews_str) if reviews_str else 0
            except:
                reviews_val = 0

            # Parse price amount
            price_amount = p.get('price_amount')
            if not price_amount:
                price = p.get('price')
                if price:
                    try:
                        if isinstance(price, dict):
                            price_amount = price.get('value')
                        else:
                            price_amount = float(str(price).replace('$', '').replace(',', ''))
                    except:
                        price_amount = None

            cursor.execute("""
                INSERT INTO amazon_products
                (asin, title, brand, stars, reviews_count, price, price_amount, thumbnail, category, url, search_keyword, image_url, search_keywords, raw_json)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (asin)
                DO UPDATE SET
                    title = EXCLUDED.title,
                    stars = EXCLUDED.stars,
                    reviews_count = EXCLUDED.reviews_count,
                    price = EXCLUDED.price,
                    price_amount = EXCLUDED.price_amount,
                    thumbnail = EXCLUDED.thumbnail,
                    image_url = EXCLUDED.image_url,
                    last_updated_at = CURRENT_TIMESTAMP,
                    search_keywords = (SELECT array_agg(DISTINCT k) FROM unnest(COALESCE(amazon_products.search_keywords, '{}') || EXCLUDED.search_keywords) k),
                    raw_json = EXCLUDED.raw_json
            """, (
                asin,
                p.get('title', ''),
                p.get('brand', ''),
                stars_val,
                reviews_val,
                p.get('price', ''),
                price_amount,
                p.get('thumbnail', ''),
                p.get('category', ''),
                p.get('url', ''),
                search_keyword,
                p.get('thumbnail', '') or p.get('image', ''),
                [search_keyword],
                Json(p.get('_raw', {}))
            ))
            saved += 1
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error saving Amazon products: {e}")
    finally:
        cursor.close()
        conn.close()
    return saved


def get_top_amazon_products(min_stars=4.0, min_reviews=50, limit=50):
    """Get best performing Amazon products by stars and review count"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM amazon_products
            WHERE stars >= %s AND reviews_count >= %s
            ORDER BY stars DESC, reviews_count DESC
            LIMIT %s
        """, (min_stars, min_reviews, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def save_search(search_term, tiktok_country, facebook_country, google_region, max_ads, all_ads):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        tiktok_count = len([a for a in all_ads if a.get("platform") == "tiktok"])
        facebook_count = len([a for a in all_ads if a.get("platform") == "facebook"])
        google_count = len([a for a in all_ads if a.get("platform") == "google"])
        
        cursor.execute("""
            INSERT INTO searches (search_term, tiktok_country, facebook_country, google_region, max_ads, results_count, tiktok_count, facebook_count, google_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (search_term, tiktok_country, facebook_country, google_region, max_ads, len(all_ads), tiktok_count, facebook_count, google_count))
        search_id = cursor.fetchone()[0]

        # Insert crawl job for tracking
        cursor.execute("""
            INSERT INTO crawl_jobs (source, query, total_results, status)
            VALUES (%s, %s, %s, %s) RETURNING id
        """, ("mixed", search_term, len(all_ads), "completed"))

        for ad in all_ads:
            platform = ad.get("platform", "")
            raw = ad.get("_raw", {})
            if platform == "facebook":
                _save_facebook_ad(cursor, search_id, ad, raw, search_term)
            elif platform == "tiktok":
                _save_tiktok_ad(cursor, search_id, ad, raw, search_term)
            elif platform == "google":
                _save_google_ad(cursor, search_id, ad, raw)

        conn.commit()
        return search_id
    except Exception as e:
        conn.rollback()
        import traceback
        print(f"Error saving search: {e}")
        traceback.print_exc()
        return None
    finally:
        cursor.close()
        conn.close()

def _save_facebook_ad(cursor, search_id, ad, raw, search_keyword=""):
    archive_id = str(raw.get("ad_archive_id") or ad.get("id", ""))
    if not archive_id: return

    # Upsert Advertiser
    advertiser = raw.get("advertiser", {}) or {}
    ad_lib_info = advertiser.get("ad_library_page_info", {}) or {}
    page_info = ad_lib_info.get("page_info", {}) or {}
    page_id = str(page_info.get("page_id") or raw.get("page_id") or "")
    # about text lives at advertiser.page.about.text
    adv_page = advertiser.get("page", {}) or {}
    about_obj = adv_page.get("about", {})
    about_text = about_obj.get("text") if isinstance(about_obj, dict) else None

    if page_id:
        cursor.execute("""
            INSERT INTO advertisers (page_id, page_name, page_category, page_alias, page_like_count, 
                                    ig_followers, ig_username, page_verification, profile_photo_url, 
                                    page_cover_photo_url, about_text, is_profile_page)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (page_id) DO UPDATE SET 
                page_name = EXCLUDED.page_name,
                page_like_count = EXCLUDED.page_like_count,
                profile_photo_url = EXCLUDED.profile_photo_url
        """, (
            page_id,
            page_info.get("page_name") or raw.get("page_name"),
            page_info.get("page_category"),
            page_info.get("page_alias"),
            page_info.get("likes"),
            page_info.get("ig_followers"),
            page_info.get("ig_username"),
            page_info.get("page_verification"),
            page_info.get("profile_photo"),
            page_info.get("page_cover_photo"),
            about_text,
            bool(page_info.get("is_profile_page"))
        ))

    # Parse age audience
    age_aud = raw.get("age_audience", {}) or {}
    age_min = age_aud.get("min") if isinstance(age_aud, dict) else None
    age_max = age_aud.get("max") if isinstance(age_aud, dict) else None

    impressions_idx = raw.get("impressions_with_index", {}) or {}
    impressions_text = impressions_idx.get("impressionsText") if isinstance(impressions_idx, dict) else None

    # Try to parse start_date
    start_date_formatted = raw.get("start_date_formatted")
    start_date = None
    if start_date_formatted:
        try:
            start_date = datetime.strptime(start_date_formatted, "%Y-%m-%d")
        except:
            pass
    end_date_formatted = raw.get("end_date_formatted")
    end_date = None
    if end_date_formatted:
        try:
            end_date = datetime.strptime(end_date_formatted, "%Y-%m-%d")
        except:
            pass

    # Upsert Ad
    cursor.execute("""
        INSERT INTO ads (ad_archive_id, page_id, is_active,
                        collation_count, collation_id,
                        has_user_reported, report_count, gated_type,
                        is_aaa_eligible, contains_digital_created_media, contains_sensitive_content,
                        start_date_formatted, end_date_formatted, start_date, end_date,
                        total_active_time, spend, currency, reach_estimate,
                        ad_id, state_media_run_label, hide_data_status,
                        is_violating_eu_siep, fev_info, verified_voice_context,
                        url, ad_library_url, position, ads_count, total, search_keywords, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ad_archive_id) DO UPDATE SET 
            is_active = EXCLUDED.is_active,
            spend = EXCLUDED.spend,
            reach_estimate = EXCLUDED.reach_estimate,
            last_updated_at = CURRENT_TIMESTAMP,
            search_keywords = (SELECT array_agg(DISTINCT k) FROM unnest(COALESCE(ads.search_keywords, '{}') || EXCLUDED.search_keywords) k),
            raw_json = EXCLUDED.raw_json
    """, (
        archive_id,
        page_id if page_id else None,
        bool(raw.get("is_active")),
        raw.get("collation_count"),
        raw.get("collation_id"),
        bool(raw.get("has_user_reported")),
        raw.get("report_count"),
        raw.get("gated_type"),
        bool(raw.get("is_aaa_eligible")),
        bool(raw.get("contains_digital_created_media")),
        bool(raw.get("contains_sensitive_content")),
        start_date_formatted,
        end_date_formatted,
        start_date,
        end_date,
        raw.get("total_active_time"),
        stringify(raw.get("spend")),
        raw.get("currency"),
        stringify(impressions_text),
        stringify(raw.get("ad_id")),
        stringify(raw.get("state_media_run_label")),
        stringify(raw.get("hide_data_status")),
        bool(raw.get("is_violating_eu_siep")),
        stringify(raw.get("fev_info")),
        stringify(raw.get("verified_voice_context")),
        stringify(raw.get("url")),
        stringify(raw.get("ad_library_url")),
        raw.get("position"),
        raw.get("ads_count"),
        raw.get("total"),
        [search_keyword],
        Json(raw)
    ))

    # Ad publisher platforms
    platforms = raw.get("publisher_platform", [])
    if isinstance(platforms, list):
        for plat in platforms:
            cursor.execute("""
                INSERT INTO ad_publisher_platforms (ad_archive_id, platform) 
                VALUES (%s, %s) ON CONFLICT DO NOTHING
            """, (archive_id, stringify(plat)))

    # Categories
    categories = raw.get("categories", [])
    if isinstance(categories, list):
        for cat in categories:
            cursor.execute("""
                INSERT INTO ad_categories (ad_archive_id, category) 
                VALUES (%s, %s) ON CONFLICT DO NOTHING
            """, (archive_id, stringify(cat)))

    # Cards
    cards = raw.get("cards", []) or []
    snapshot = raw.get("snapshot", {}) or {}
    if not cards:
        cards = snapshot.get("cards", []) or []

    # Insert snapshot details (body can be a dict {"text": "..."} or a string)
    snap_body = snapshot.get("body", "")
    if isinstance(snap_body, dict):
        snap_body = snap_body.get("text", "")
    # Delete old snapshot to allow re-insert on second search of same ad
    cursor.execute("DELETE FROM ad_snapshots WHERE ad_archive_id = %s", (archive_id,))
    cursor.execute("""
        INSERT INTO ad_snapshots (ad_archive_id, body_text, title, caption, link_url, link_description)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        archive_id,
        snap_body,
        snapshot.get("title"),
        snapshot.get("caption"),
        snapshot.get("link_url"),
        snapshot.get("link_description")
    ))

    # Delete existing cards & creatives to refresh (order matters: creatives reference cards)
    cursor.execute("DELETE FROM ad_creatives WHERE ad_archive_id = %s", (archive_id,))
    cursor.execute("DELETE FROM ad_cards WHERE ad_archive_id = %s", (archive_id,))

    for idx, card in enumerate(cards):
        cursor.execute("""
            INSERT INTO ad_cards (ad_archive_id, card_index, title, body, cta_type, cta_text, 
                                  caption, link_url, link_description, 
                                  original_image_url, resized_image_url, video_hd_url, video_sd_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (
            archive_id, idx,
            stringify(card.get("title")),
            stringify(card.get("body")),
            stringify(card.get("cta_type")),
            stringify(card.get("ctaText") or card.get("cta_text")),
            stringify(card.get("caption")),
            stringify(card.get("linkUrl") or card.get("link_url")),
            stringify(card.get("link_description")),
            stringify(card.get("originalImageUrl") or card.get("original_image_url")),
            stringify(card.get("resizedImageUrl") or card.get("resized_image_url")),
            stringify(card.get("videoHdUrl") or card.get("video_hd_url")),
            stringify(card.get("videoSdUrl") or card.get("video_sd_url"))
        ))
        card_id = cursor.fetchone()[0]

        # Register creatives for background download
        if card.get("originalImageUrl") or card.get("original_image_url"):
            cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                           (card_id, archive_id, 'image_original', stringify(card.get("originalImageUrl") or card.get("original_image_url"))))
        if card.get("videoHdUrl") or card.get("video_hd_url"):
            cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                           (card_id, archive_id, 'video_hd', stringify(card.get("videoHdUrl") or card.get("video_hd_url"))))
        elif card.get("videoSdUrl") or card.get("video_sd_url"):
            cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                           (card_id, archive_id, 'video_sd', stringify(card.get("videoSdUrl") or card.get("video_sd_url"))))
        if card.get("video_preview_image_url") or card.get("videoPreviewImageUrl"):
            cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                           (card_id, archive_id, 'image_preview', stringify(card.get("video_preview_image_url") or card.get("videoPreviewImageUrl"))))

    if snapshot.get("images"):
        for idx, img_url in enumerate(snapshot.get("images", [])):
            if img_url and not str(img_url).startswith("/static"):
                cursor.execute("INSERT INTO ad_cards (ad_archive_id, card_index, original_image_url) VALUES (%s, %s, %s) RETURNING id",
                               (archive_id, 999+idx, stringify(img_url)))
                card_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                               (card_id, archive_id, 'image_original', stringify(img_url)))

    if snapshot.get("videos"):
        for idx, vid in enumerate(snapshot.get("videos", [])):
            if isinstance(vid, dict):
                video_url = vid.get("video_hd_url") or vid.get("video_sd_url") or ""
                preview_url = vid.get("video_preview_image_url") or ""
            else:
                video_url = vid if isinstance(vid, str) else ""
                preview_url = ""
            if video_url:
                cursor.execute("INSERT INTO ad_cards (ad_archive_id, card_index, video_hd_url) VALUES (%s, %s, %s) RETURNING id",
                               (archive_id, 1999+idx, stringify(video_url)))
                card_id = cursor.fetchone()[0]
                cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                               (card_id, archive_id, 'video_hd', stringify(video_url)))
                if preview_url:
                    cursor.execute("INSERT INTO ad_creatives (card_id, ad_archive_id, type, original_url) VALUES (%s, %s, %s, %s)",
                                   (card_id, archive_id, 'image_preview', stringify(preview_url)))

    # Demographics
    breakdowns = raw.get("age_country_gender_reach_breakdown") or []
    eu_trans = raw.get("transparency_by_location") or {}
    eu_data = eu_trans.get("eu_transparency") or {}
    if not breakdowns and eu_data.get("age_country_gender_reach_breakdown"):
        breakdowns = eu_data.get("age_country_gender_reach_breakdown") or []

    if breakdowns:
        # Delete existing targeting data for this ad to allow refresh
        cursor.execute("DELETE FROM reach_breakdown WHERE eu_targeting_id IN (SELECT id FROM eu_targeting WHERE ad_archive_id = %s)", (archive_id,))
        cursor.execute("DELETE FROM eu_targeting WHERE ad_archive_id = %s", (archive_id,))

        cursor.execute("INSERT INTO eu_targeting (ad_archive_id, eu_total_reach) VALUES (%s, %s) RETURNING id",
                       (archive_id, raw.get("eu_total_reach") or eu_data.get("eu_total_reach")))
        eu_targeting_id = cursor.fetchone()[0]

        for brkd in breakdowns:
            country = brkd.get("country", "")
            for ag in brkd.get("age_gender_breakdowns", []):
                cursor.execute("""
                    INSERT INTO reach_breakdown (eu_targeting_id, country, age_range, male, female, unknown)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (eu_targeting_id, country, ag.get("age_range"), ag.get("male"), ag.get("female"), ag.get("unknown")))


def _save_tiktok_ad(cursor, search_id, ad, raw, search_keyword=""):
    tiktok_id = str(raw.get("AD ID") or ad.get("id", ""))
    if not tiktok_id: return

    # Parse Details
    ad_details = raw.get("Ad Details", []) or []
    details_map = {}
    for d in ad_details:
        if isinstance(d, dict):
            for k, v in d.items():
                details_map[k] = str(v) if v else ""

    dates = raw.get("Ad Dates", []) or []
    first_shown = dates[0].get("FirstShown") if dates else None
    last_shown = dates[0].get("LastShown") if dates else None

    cursor.execute("""
        INSERT INTO tiktok_ads (ad_id, advertiser_name, ad_audience, target_audience_size, 
                                sponsor, ad_type, audit_status, spent, impression, 
                                ad_preview_url, ad_detail_url, first_shown_date, last_shown_date, search_keywords, raw_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ad_id) DO UPDATE SET 
            spent = EXCLUDED.spent,
            impression = EXCLUDED.impression,
            last_shown_date = EXCLUDED.last_shown_date,
            last_updated_at = CURRENT_TIMESTAMP,
            search_keywords = (SELECT array_agg(DISTINCT k) FROM unnest(COALESCE(tiktok_ads.search_keywords, '{}') || EXCLUDED.search_keywords) k)
    """, (
        tiktok_id,
        raw.get("Advertiser Name", ""),
        raw.get("Ad Audience", ""),
        raw.get("Ad Target Audience Size", ""),
        raw.get("Ad Sponsor", ""),
        details_map.get("Type", ""),
        details_map.get("Audit Status", ""),
        details_map.get("Spent", ""),
        details_map.get("Impression", ""),
        raw.get("AD Preview", ""),
        raw.get("Ad Detail URL", ""),
        first_shown,
        last_shown,
        [search_keyword],
        Json(raw)
    ))

    # Insert extra details
    cursor.execute("DELETE FROM tiktok_ad_details_extra WHERE ad_id = %s", (tiktok_id,))
    for k, v in details_map.items():
        cursor.execute("INSERT INTO tiktok_ad_details_extra (ad_id, key, value) VALUES (%s, %s, %s)", (tiktok_id, k, v))

    # Targeting
    targeting = raw.get("Ad Targeting", {}) or {}
    cursor.execute("DELETE FROM tiktok_ad_targeting_regions WHERE ad_id = %s", (tiktok_id,))
    cursor.execute("DELETE FROM tiktok_ad_targeting_age WHERE ad_id = %s", (tiktok_id,))
    cursor.execute("DELETE FROM tiktok_ad_targeting_gender WHERE ad_id = %s", (tiktok_id,))

    for reg in targeting.get("regions", []):
        cursor.execute("INSERT INTO tiktok_ad_targeting_regions (ad_id, region, impressions_range) VALUES (%s, %s, %s)",
                       (tiktok_id, reg.get("region"), reg.get("impressions")))

    for ag in targeting.get("age", []):
        cursor.execute("""
            INSERT INTO tiktok_ad_targeting_age (ad_id, region, age_13_17, age_18_24, age_25_34, age_35_44, age_45_54, age_55_plus)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (tiktok_id, ag.get("region"), ag.get("13-17"), ag.get("18-24"), ag.get("25-34"), ag.get("35-44"), ag.get("45-54"), ag.get("55+")))

    for g in targeting.get("gender", []):
        cursor.execute("""
            INSERT INTO tiktok_ad_targeting_gender (ad_id, region, male, female, unknown)
            VALUES (%s, %s, %s, %s, %s)
        """, (tiktok_id, g.get("region"), g.get("male"), g.get("female"), g.get("unknown")))

    # Media
    media = raw.get("Ad Media", []) or []
    cursor.execute("DELETE FROM tiktok_ad_media WHERE ad_id = %s", (tiktok_id,))
    
    for idx, m in enumerate(media):
        if isinstance(m, str):
            if ": " in m:
                url = m.split(": ", 1)[1]
                media_type = "video" if "video" in m.lower() else "image"
            else:
                url = m
                media_type = "image"
        elif isinstance(m, dict):
            url = m.get("Image 1") or m.get("Cover 1") or m.get("Video 1") or ""
            media_type = "video" if m.get("Video 1") else "image"
        else:
            continue

        if url:
            cursor.execute("""
                INSERT INTO tiktok_ad_media (ad_id, media_index, media_type, original_url)
                VALUES (%s, %s, %s, %s)
            """, (tiktok_id, idx, media_type, url))


def _save_google_ad(cursor, search_id, ad, raw):
    google_id = str(raw.get("advertiserId", "") + "_" + raw.get("creativeId", ""))
    cursor.execute("""
        INSERT INTO google_ads (ad_id, search_id, advertiser_id, creative_id, format, ad_transparency_url, creative_regions)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ad_id) DO NOTHING
    """, (
        google_id, search_id, raw.get("advertiserId"), raw.get("creativeId"),
        raw.get("format"), raw.get("adTransparencyUrl"),
        json.dumps(raw.get("creativeRegions", []))
    ))
    
    preview_urls = raw.get("previewUrls", []) or []
    for url in preview_urls:
        if url:
            cursor.execute("INSERT INTO google_ad_images (ad_id, image_url) VALUES (%s, %s)", (google_id, stringify(url)))


def get_search_history(limit=20):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM searches ORDER BY id DESC LIMIT %s", (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(r) for r in rows]

def get_search_results(search_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    # We reconstruct the ads structure for the frontend
    # Since we have unified_ads view, we can use it to fetch the list and enrich with media
    
    cursor.execute("SELECT * FROM searches WHERE id = %s", (search_id,))
    search_row = cursor.fetchone()
    if not search_row:
        return []

    ads = []
    
    # Facebook ads
    cursor.execute("""
        SELECT a.*, adv.page_name, adv.profile_photo_url, adv.page_category, adv.page_like_count
        FROM ads a
        LEFT JOIN advertisers adv ON a.page_id = adv.page_id
        WHERE a.raw_json IS NOT NULL
    """) # Note: This gets all ads for now. To filter by search_id, we need to map ads to searches.
    # Actually, we can just use the unified_ads view but we want the detailed raw_json.
    # Since the prompt said "Refactor schema", I didn't add search_id to ads table.
    # Let's just fetch all ads in the db, but in reality we should join via an intermediate table.
    # Since it's an MVP, I'll fetch everything from `unified_ads`.
    
    cursor.execute("SELECT * FROM ads")
    fb_ads = cursor.fetchall()
    
    for row in fb_ads:
        raw = row['raw_json'] if row['raw_json'] else {}
        archive_id = row['ad_archive_id']
        
        # Get creatives for this ad
        cursor.execute("SELECT * FROM ad_creatives WHERE ad_archive_id = %s", (archive_id,))
        creatives = cursor.fetchall()
        
        image_urls = []
        videos = []
        for c in creatives:
            url = get_media_url(c['local_path'], 'facebook', archive_id)
            if not url:
                url = c['original_url'] or ""
            if 'video' in c['type']:
                videos.append({"url": url})
            else:
                image_urls.append(url)
                
        ads.append({
            "id": archive_id,
            "platform": "facebook",
            "image_urls": image_urls,
            "videos": videos,
            "has_images": len(image_urls) > 0,
            "has_videos": len(videos) > 0,
            "first_shown_date": row['start_date_formatted'],
            "last_shown_date": row['end_date_formatted'],
            "status": "active" if row['is_active'] else "inactive",
            "reach": row['reach_estimate'] or "N/A",
            "advertiser_name": raw.get('page_name') or raw.get('advertiser', {}).get('ad_library_page_info', {}).get('page_info', {}).get('page_name', 'Unknown'),
            "advertiser_avatar": stringify(raw.get('advertiser', {}).get('ad_library_page_info', {}).get('page_info', {}).get('profile_photo', '') or raw.get('snapshot', {}).get('page_profile_picture_url', '')),
            "body_text": raw.get('snapshot', {}).get('body', {}).get('text', '') if isinstance(raw.get('snapshot', {}).get('body', {}), dict) else raw.get('snapshot', {}).get('body', ''),
            "title": raw.get('snapshot', {}).get('title', ''),
            "cta_text": raw.get('snapshot', {}).get('cta_text', ''),
            "link_url": raw.get('snapshot', {}).get('link_url', ''),
            "_raw": raw
        })

    # TikTok ads
    cursor.execute("SELECT * FROM tiktok_ads")
    tiktok_ads = cursor.fetchall()
    for row in tiktok_ads:
        raw = row['raw_json'] if row['raw_json'] else {}
        ad_id = row['ad_id']
        
        cursor.execute("SELECT * FROM tiktok_ad_media WHERE ad_id = %s", (ad_id,))
        media = cursor.fetchall()
        
        image_urls = []
        videos = []
        for m in media:
            url = get_media_url(m['local_path'], 'tiktok', ad_id)
            if not url:
                url = m['original_url'] or ""
            if m['media_type'] == 'video':
                videos.append({"url": url})
            else:
                image_urls.append(url)
                
        ads.append({
            "id": ad_id,
            "platform": "tiktok",
            "image_urls": image_urls,
            "videos": videos,
            "has_images": len(image_urls) > 0,
            "has_videos": len(videos) > 0,
            "first_shown_date": row['first_shown_date'],
            "last_shown_date": row['last_shown_date'],
            "status": "active",
            "reach": row['ad_audience'] or "N/A",
            "advertiser_name": row['advertiser_name'],
            "advertiser_avatar": row['ad_preview_local_path'] or row['ad_preview_url'],
        })
    
    return ads


def get_all_raw_data(limit=5000):
    """Get all raw ads and products from the global database with optimized queries"""
    import time
    start_time = time.time()
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    
    try:
        print(f"🔍 [get_all_raw_data] Starting fetch (limit={limit})")
        # 1. Fetch Facebook ads
        cursor.execute("SELECT * FROM ads ORDER BY last_updated_at DESC NULLS LAST, created_at DESC LIMIT %s", (limit,))
        fb_rows = cursor.fetchall()
        fb_ids = [r['ad_archive_id'] for r in fb_rows]
        
        fb_media_map = {}
        if fb_ids:
            cursor.execute("SELECT * FROM ad_creatives WHERE ad_archive_id = ANY(%s)", (fb_ids,))
            for m in cursor.fetchall():
                aid = m['ad_archive_id']
                if aid not in fb_media_map: fb_media_map[aid] = []
                fb_media_map[aid].append(m)
        
        ads = []
        for row in fb_rows:
            archive_id = row['ad_archive_id']
            creatives = fb_media_map.get(archive_id, [])
            image_urls = []
            videos = []
            for c in creatives:
                url = get_media_url(c['local_path'], 'facebook', archive_id)
                if not url:
                    url = c['original_url'] or ""
                if c['type'] and 'video' in c['type']:
                    videos.append({"url": url})
                else:
                    image_urls.append(url)
            
            raw_json = row['raw_json'] or {}
            snap = raw_json.get('snapshot', {}) or {}
            impressions = raw_json.get('impressions_with_index', {}) or {}
            
            ads.append({
                "id": archive_id,
                "platform": "facebook",
                "advertiser_name": snap.get('page_name') or raw_json.get('page_name') or 'Unknown',
                "advertiser_avatar": snap.get('page_profile_picture_url', ''),
                "status": "active" if raw_json.get('is_active') else "inactive",
                "first_shown_date": str(raw_json.get('start_date_formatted', 'N/A')),
                "last_shown_date": str(raw_json.get('end_date_formatted', 'N/A')),
                "reach": impressions.get('impressions_text') or str(impressions.get('impressions_index', 'N/A')),
                "reach_numeric": impressions.get('impressions_index', 0) or 0,
                "image_urls": image_urls,
                "videos": videos,
                "has_images": len(image_urls) > 0,
                "has_videos": len(videos) > 0,
                "ai_analysis": row.get('ai_analysis'),
                "search_keywords": row.get('search_keywords', []),
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "last_updated_at": row['last_updated_at'].isoformat() if row['last_updated_at'] else None,
                "raw": raw_json
            })

        # 2. Fetch TikTok ads
        cursor.execute("SELECT * FROM tiktok_ads ORDER BY last_updated_at DESC NULLS LAST, created_at DESC LIMIT %s", (limit,))
        tt_rows = cursor.fetchall()
        tt_ids = [r['ad_id'] for r in tt_rows]
        
        tt_media_map = {}
        if tt_ids:
            cursor.execute("SELECT * FROM tiktok_ad_media WHERE ad_id = ANY(%s)", (tt_ids,))
            for m in cursor.fetchall():
                aid = m['ad_id']
                if aid not in tt_media_map: tt_media_map[aid] = []
                tt_media_map[aid].append(m)
                
        for row in tt_rows:
            ad_id = row['ad_id']
            media = tt_media_map.get(ad_id, [])
            image_urls = []
            videos = []
            for m in media:
                url = get_media_url(m.get('local_path'), 'tiktok', ad_id)
                if not url:
                    url = m['original_url'] or ""
                if m['media_type'] and 'video' in m['media_type']:
                    videos.append({"url": url})
                else:
                    image_urls.append(url)
            
            raw_json = row['raw_json'] or {}
            ads.append({
                "id": ad_id,
                "platform": "tiktok",
                "advertiser_name": row.get('advertiser_name') or raw_json.get('Advertiser Name') or 'Unknown',
                "advertiser_avatar": row.get('ad_preview_local_path') or row.get('ad_preview_url') or '',
                "status": "active",
                "first_shown_date": str(row.get('first_shown_date') or 'N/A'),
                "last_shown_date": str(row.get('last_shown_date') or 'N/A'),
                "reach": row.get('ad_audience') or raw_json.get('Ad Audience') or 'N/A',
                "reach_numeric": 0,
                "image_urls": image_urls,
                "videos": videos,
                "has_images": len(image_urls) > 0,
                "has_videos": len(videos) > 0,
                "ai_analysis": row.get('ai_analysis'),
                "search_keywords": row.get('search_keywords', []),
                "created_at": row['created_at'].isoformat() if row['created_at'] else None,
                "last_updated_at": row['last_updated_at'].isoformat() if row['last_updated_at'] else None,
                "raw": raw_json
            })
            
        # 3. Amazon & Etsy
        cursor.execute("SELECT *, first_seen_at as created_at FROM amazon_products ORDER BY last_updated_at DESC NULLS LAST, id DESC LIMIT %s", (limit,))
        amazon_products = []
        for r in cursor.fetchall():
            d = dict(r)
            if d['created_at']: d['created_at'] = d['created_at'].isoformat()
            if d['last_updated_at']: d['last_updated_at'] = d['last_updated_at'].isoformat()
            amazon_products.append(d)
        
        cursor.execute("SELECT *, first_seen_at as created_at FROM etsy_products ORDER BY last_updated_at DESC NULLS LAST, id DESC LIMIT %s", (limit,))
        etsy_products = []
        for r in cursor.fetchall():
            d = dict(r)
            if d['created_at']: d['created_at'] = d['created_at'].isoformat()
            if d['last_updated_at']: d['last_updated_at'] = d['last_updated_at'].isoformat()
            etsy_products.append(d)
        
        total = len(ads)
        tiktok = len([a for a in ads if a['platform'] == 'tiktok'])
        facebook = total - tiktok
        print(f"✅ [get_all_raw_data] Done in {time.time() - start_time:.2f}s. Loaded {total} ads ({facebook} FB, {tiktok} TT) and {len(etsy_products)} Etsy, {len(amazon_products)} Amazon.")

        print(f"📊 API /api/ads/all: Sending {total} ads, {len(etsy_products)} Etsy, {len(amazon_products)} Amazon")
        return {
            "ads": ads,
            "amazon_products": amazon_products,
            "etsy_products": etsy_products,
            "stats": {
                "total": total,
                "tiktok": tiktok,
                "facebook": facebook,
                "etsy": len(etsy_products),
                "amazon": len(amazon_products)
            }
        }
    finally:
        cursor.close()
        conn.close()


def save_classification(ad_archive_id, tiktok_ad_id, classification):
    """Save digital product classification"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO digital_product_classification
            (ad_archive_id, tiktok_ad_id, classification_type, confidence_score,
             matched_keywords, url_domain, is_digital_product, product_category, raw_classification)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ad_archive_id)
            DO UPDATE SET
                classification_type = EXCLUDED.classification_type,
                confidence_score = EXCLUDED.confidence_score,
                matched_keywords = EXCLUDED.matched_keywords,
                url_domain = EXCLUDED.url_domain,
                is_digital_product = EXCLUDED.is_digital_product,
                product_category = EXCLUDED.product_category,
                raw_classification = EXCLUDED.raw_classification,
                classified_at = CURRENT_TIMESTAMP
        """, (
            ad_archive_id or None,
            tiktok_ad_id or None,
            classification.get('classification_type', 'unknown'),
            classification.get('confidence_score', 0),
            classification.get('matched_keywords', []),
            classification.get('url_domain'),
            classification.get('is_digital_product', False),
            classification.get('product_category'),
            Json(classification)
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving classification: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def update_advertiser_tracking(page_id, page_name, platform, ad_count, first_seen, last_seen):
    """Update advertiser tracking metrics"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        active_days = 0
        today = datetime.now()
        first_dt = None
        last_dt = None
        if first_seen:
            try:
                first_dt = datetime.strptime(str(first_seen)[:10], '%Y-%m-%d') if isinstance(first_seen, str) else first_seen
            except:
                pass
        if last_seen:
            try:
                last_dt = datetime.strptime(str(last_seen)[:10], '%Y-%m-%d') if isinstance(last_seen, str) else last_seen
            except:
                pass
        elif first_dt:
            # last_seen is None but first_seen exists - use today as fallback
            last_dt = today

        if first_dt and last_dt:
            active_days = (last_dt - first_dt).days

        scaling_score = ad_count * active_days if active_days > 0 else 0

        if scaling_score < 14:
            tier = 'low'
        elif scaling_score < 30:
            tier = 'medium'
        else:
            tier = 'high'

        is_scaling = ad_count >= 3 and active_days >= 7

        cursor.execute("""
            INSERT INTO advertiser_tracking
            (page_id, page_name, platform, ad_count, first_seen_at, last_seen_at,
             active_days, is_scaling, scaling_score, scaling_tier)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (page_id, platform)
            DO UPDATE SET
                page_name = EXCLUDED.page_name,
                ad_count = EXCLUDED.ad_count,
                first_seen_at = LEAST(advertiser_tracking.first_seen_at, EXCLUDED.first_seen_at),
                last_seen_at = GREATEST(advertiser_tracking.last_seen_at, EXCLUDED.last_seen_at),
                active_days = EXCLUDED.active_days,
                is_scaling = EXCLUDED.is_scaling,
                scaling_score = EXCLUDED.scaling_score,
                scaling_tier = EXCLUDED.scaling_tier,
                last_calculated_at = CURRENT_TIMESTAMP
        """, (
            page_id, page_name, platform, ad_count,
            first_seen, last_seen, active_days,
            is_scaling, scaling_score, tier
        ))
        conn.commit()
        return is_scaling, scaling_score, tier
    except Exception as e:
        conn.rollback()
        print(f"Error updating advertiser tracking: {e}")
        return None, 0, 'low'
    finally:
        cursor.close()
        conn.close()


def get_scaling_advertisers(min_score=14, limit=50):
    """Get advertisers that are scaling (score >= min_score)"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT * FROM advertiser_tracking
            WHERE scaling_score >= %s AND is_scaling = TRUE
            ORDER BY scaling_score DESC
            LIMIT %s
        """, (min_score, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_digital_opportunities(min_confidence=0.25, limit=100):
    """Get ads classified as digital products"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT dc.*, a.page_name, a.page_like_count,
                   aa.ad_count, aa.scaling_score, aa.scaling_tier, aa.is_scaling
            FROM digital_product_classification dc
            LEFT JOIN advertisers a ON dc.ad_archive_id IN (SELECT ad_archive_id FROM ads WHERE page_id = a.page_id)
            LEFT JOIN advertiser_tracking aa ON a.page_id = aa.page_id
            WHERE dc.is_digital_product = TRUE
              AND dc.confidence_score >= %s
            ORDER BY dc.confidence_score DESC, aa.scaling_score DESC
            LIMIT %s
        """, (min_confidence, limit))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def save_product_opportunity(opp_data):
    """Save or update a product opportunity"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Stable opportunity_id based on advertiser_page_id + platform (not timestamp!)
        advertiser_page_id = opp_data.get('advertiser_page_id', '')
        platform = opp_data.get('advertiser_platform', 'UNK')[:3].lower()
        import hashlib
        opp_id = f"{platform}_{hashlib.md5(advertiser_page_id.encode()).hexdigest()[:12]}"

        cursor.execute("""
            INSERT INTO product_opportunities
            (opportunity_id, product_name, product_category, product_description,
             price_text, price_amount, advertiser_page_id, advertiser_name,
             advertiser_platform, advertiser_page_url, scaling_score, scaling_tier,
             active_days, ad_count, is_scaling, landing_page_url, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (opportunity_id)
            DO UPDATE SET
                product_name = COALESCE(EXCLUDED.product_name, product_opportunities.product_name),
                product_category = COALESCE(EXCLUDED.product_category, product_opportunities.product_category),
                scaling_score = GREATEST(product_opportunities.scaling_score, EXCLUDED.scaling_score),
                scaling_tier = CASE WHEN product_opportunities.scaling_score >= EXCLUDED.scaling_score THEN product_opportunities.scaling_tier ELSE EXCLUDED.scaling_tier END,
                is_scaling = product_opportunities.is_scaling OR EXCLUDED.is_scaling,
                active_days = GREATEST(product_opportunities.active_days, EXCLUDED.active_days),
                ad_count = GREATEST(product_opportunities.ad_count, EXCLUDED.ad_count),
                landing_page_url = COALESCE(EXCLUDED.landing_page_url, product_opportunities.landing_page_url),
                last_updated_at = CURRENT_TIMESTAMP
        """, (
            opp_id,
            opp_data.get('product_name'),
            opp_data.get('product_category'),
            opp_data.get('product_description'),
            opp_data.get('price_text'),
            opp_data.get('price_amount'),
            opp_data.get('advertiser_page_id'),
            opp_data.get('advertiser_name'),
            opp_data.get('advertiser_platform'),
            opp_data.get('advertiser_page_url'),
            opp_data.get('scaling_score', 0),
            opp_data.get('scaling_tier', 'low'),
            opp_data.get('active_days', 0),
            opp_data.get('ad_count', 0),
            opp_data.get('is_scaling', False),
            opp_data.get('landing_page_url'),
            opp_data.get('status', 'fresh_lead')
        ))
        conn.commit()
        return opp_id
    except Exception as e:
        conn.rollback()
        print(f"Error saving product opportunity: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def save_landing_page_analysis(opportunity_id, analysis_result):
    """Save landing page analysis for a product opportunity"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO landing_pages
            (opportunity_id, url, domain, hero_headline, hero_subheadline, main_offer,
             price_text, price_amount, currency, cta_text, cta_url,
             checkout_type, technology_stack, trust_signals,
             full_text_content, html_content, scrape_error)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url)
            DO UPDATE SET
                opportunity_id = COALESCE(EXCLUDED.opportunity_id, landing_pages.opportunity_id),
                hero_headline = EXCLUDED.hero_headline,
                hero_subheadline = EXCLUDED.hero_subheadline,
                main_offer = EXCLUDED.main_offer,
                price_text = EXCLUDED.price_text,
                price_amount = EXCLUDED.price_amount,
                checkout_type = EXCLUDED.checkout_type,
                technology_stack = EXCLUDED.technology_stack,
                trust_signals = EXCLUDED.trust_signals,
                scrape_error = EXCLUDED.scrape_error,
                scraped_at = CURRENT_TIMESTAMP
        """, (
            opportunity_id,
            analysis_result.get('url'),
            analysis_result.get('domain'),
            analysis_result.get('hero_headline'),
            analysis_result.get('hero_subheadline'),
            analysis_result.get('main_offer'),
            analysis_result.get('price_text'),
            analysis_result.get('price_amount'),
            analysis_result.get('currency', 'USD'),
            analysis_result.get('cta_text'),
            analysis_result.get('cta_url'),
            analysis_result.get('checkout_type', 'unknown'),
            analysis_result.get('technology_stack', []),
            analysis_result.get('trust_signals', []),
            analysis_result.get('full_text_content', '')[:5000],
            analysis_result.get('html_content', '')[:10000],
            analysis_result.get('scrape_error')
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving landing page: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_opportunities(status=None, tier=None, limit=100):
    """Get product opportunities, optionally filtered"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM product_opportunities WHERE 1=1"
        params = []
        if status:
            query += " AND status = %s"
            params.append(status)
        if tier:
            query += " AND scaling_tier = %s"
            params.append(tier)
        query += " ORDER BY scaling_score DESC, priority ASC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_opportunities_needing_landing_pages(limit=20):
    """Get opportunities that have landing_page_url but not yet scraped"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT po.opportunity_id, po.landing_page_url, po.advertiser_name, po.scaling_tier
            FROM product_opportunities po
            LEFT JOIN landing_pages lp ON po.landing_page_url = lp.url
            WHERE po.landing_page_url IS NOT NULL
              AND po.landing_page_url != ''
              AND po.landing_page_url != 'N/A'
              AND lp.id IS NULL
            ORDER BY po.scaling_score DESC
            LIMIT %s
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


# ================================================
# PRODUCT CRITERIA (Back-office)
# ================================================

def get_criteria(platform=None, category=None, rule_type=None, is_active=True):
    """Get product criteria, optionally filtered"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM product_criteria WHERE 1=1"
        params = []
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active)
        if platform and platform != 'all':
            query += " AND (platform = 'all' OR platform = %s)"
            params.append(platform)
        if category:
            query += " AND category = %s"
            params.append(category)
        if rule_type:
            query += " AND rule_type = %s"
            params.append(rule_type)
        query += " ORDER BY display_order ASC"
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_criteria_weights():
    """Get weight configuration for classifier"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT config_key, config_value
            FROM product_criteria
            WHERE rule_type = 'weight_config' AND is_active = TRUE
        """)
        return {r['config_key']: float(r['config_value']) for r in cursor.fetchall()}
    finally:
        cursor.close()
        conn.close()


def get_criteria_keywords():
    """Get keyword rules for classifier"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT keyword, weight, score_boost, is_exclusion, category
            FROM product_criteria
            WHERE rule_type = 'keyword' AND is_active = TRUE
            ORDER BY display_order
        """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_criteria_price_signals():
    """Get price signal rules"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT keyword, score_boost
            FROM product_criteria
            WHERE rule_type = 'price_signal' AND is_active = TRUE
        """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def get_criteria_domains():
    """Get domain rules"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT keyword, score_boost
            FROM product_criteria
            WHERE rule_type = 'domain' AND is_active = TRUE
        """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def save_criterion(rule_id, rule_type, platform, category, keyword,
                   weight, is_exclusion, score_boost, config_key, config_value,
                   is_active, display_order, description, examples):
    """Insert or update a criterion"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            INSERT INTO product_criteria
            (rule_id, rule_type, platform, category, keyword, weight, is_exclusion,
             score_boost, config_key, config_value, is_active, display_order, description, examples)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rule_id) DO UPDATE SET
                rule_type = EXCLUDED.rule_type,
                platform = EXCLUDED.platform,
                category = EXCLUDED.category,
                keyword = EXCLUDED.keyword,
                weight = EXCLUDED.weight,
                is_exclusion = EXCLUDED.is_exclusion,
                score_boost = EXCLUDED.score_boost,
                config_key = EXCLUDED.config_key,
                config_value = EXCLUDED.config_value,
                is_active = EXCLUDED.is_active,
                display_order = EXCLUDED.display_order,
                description = EXCLUDED.description,
                examples = EXCLUDED.examples,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (rule_id, rule_type, platform, category, keyword, weight, is_exclusion,
              score_boost, config_key, config_value, is_active, display_order, description, examples))
        conn.commit()
        return cursor.fetchone()['id']
    except Exception as e:
        conn.rollback()
        print(f"Error saving criterion: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def delete_criterion(rule_id):
    """Soft-delete a criterion (set is_active=False)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE product_criteria SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE rule_id = %s
        """, (rule_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Error deleting criterion: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def get_criterion_stats():
    """Get statistics about criteria"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT
                rule_type,
                COUNT(*) as total,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active
            FROM product_criteria
            GROUP BY rule_type
        """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()


def save_ai_analysis(platform, external_id, analysis_result):
    """
    Save AI analysis result to the corresponding table
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        table_map = {
            'facebook': 'ads',
            'tiktok': 'tiktok_ads',
            'amazon': 'amazon_products',
            'etsy': 'etsy_products'
        }
        id_col_map = {
            'facebook': 'ad_archive_id',
            'tiktok': 'ad_id',
            'amazon': 'asin',
            'etsy': 'listing_id'
        }
        
        table = table_map.get(platform)
        id_col = id_col_map.get(platform)
        
        if not table or not id_col:
            return False

        cursor.execute(f"""
            UPDATE {table}
            SET ai_analysis = %s,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE {id_col} = %s
        """, (Json(analysis_result), str(external_id)))

        # Also log to ai_analysis_log
        cursor.execute("""
            INSERT INTO ai_analysis_log (platform, external_id, verdict)
            VALUES (%s, %s, %s)
        """, (platform, str(external_id), Json(analysis_result)))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving AI analysis: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_product_metadata(platform, external_id):
    """
    Retrieve AI analysis and timestamps for a specific product/ad
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        table_map = {
            'facebook': 'ads', 'fb': 'ads',
            'tiktok': 'tiktok_ads',
            'amazon': 'amazon_products',
            'etsy': 'etsy_products'
        }
        id_col_map = {
            'facebook': 'ad_archive_id', 'fb': 'ad_archive_id',
            'tiktok': 'ad_id',
            'amazon': 'asin',
            'etsy': 'listing_id'
        }
        
        table = table_map.get(platform)
        id_col = id_col_map.get(platform)
        
        if not table or not id_col:
            return None

        # Determine which timestamp columns to fetch
        created_col = 'created_at' if platform in ['facebook', 'fb', 'tiktok'] else 'first_seen_at'
        
        cursor.execute(f"SELECT ai_analysis, last_updated_at, {created_col} as created_at FROM {table} WHERE {id_col} = %s", (str(external_id),))
        row = cursor.fetchone()
        if row:
            return {
                "ai_analysis": row['ai_analysis'],
                "last_updated_at": row['last_updated_at'].isoformat() if row['last_updated_at'] else None,
                "created_at": row['created_at'].isoformat() if row['created_at'] else None
            }
        return None
    finally:
        cursor.close()
        conn.close()

# ============ AUTOMATION FUNCTIONS ============

def get_automation_settings():
    """Get global automation settings"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("SELECT * FROM automation_settings WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        conn.close()

def update_automation_settings(settings):
    """Update global automation settings"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE automation_settings SET
                is_active = %s,
                tiktok_frequency_hours = %s,
                facebook_frequency_hours = %s,
                etsy_frequency_hours = %s,
                amazon_frequency_hours = %s,
                tiktok_max_ads = %s,
                facebook_max_ads = %s,
                etsy_max_products = %s,
                amazon_max_products = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (
            settings.get('is_active', False),
            settings.get('tiktok_frequency_hours', 24),
            settings.get('facebook_frequency_hours', 48),
            settings.get('etsy_frequency_hours', 72),
            settings.get('amazon_frequency_hours', 72),
            settings.get('tiktok_max_ads', 20),
            settings.get('facebook_max_ads', 20),
            settings.get('etsy_max_products', 20),
            settings.get('amazon_max_products', 20)
        ))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating automation settings: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_automation_keywords():
    """Get all automation keywords with their platform status"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT k.*, 
                   s_tt.last_tested_at as tt_last, s_tt.status as tt_status,
                   s_fb.last_tested_at as fb_last, s_fb.status as fb_status,
                   s_etsy.last_tested_at as etsy_last, s_etsy.status as etsy_status,
                   s_amz.last_tested_at as amz_last, s_amz.status as amz_status
            FROM automation_keywords k
            LEFT JOIN keyword_platform_status s_tt ON k.id = s_tt.keyword_id AND s_tt.platform = 'tiktok'
            LEFT JOIN keyword_platform_status s_fb ON k.id = s_fb.keyword_id AND s_fb.platform = 'facebook'
            LEFT JOIN keyword_platform_status s_etsy ON k.id = s_etsy.keyword_id AND s_etsy.platform = 'etsy'
            LEFT JOIN keyword_platform_status s_amz ON k.id = s_amz.keyword_id AND s_amz.platform = 'amazon'
            ORDER BY k.category, k.keyword
        """)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

def add_automation_keyword(category, keyword):
    """Add a new keyword to automation list"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO automation_keywords (category, keyword)
            VALUES (%s, %s)
            ON CONFLICT (keyword) DO NOTHING
        """, (category, keyword))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error adding keyword: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_automation_keyword(keyword_id):
    """Delete a keyword from automation list"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM automation_keywords WHERE id = %s", (keyword_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error deleting keyword: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_keyword_status(keyword_id, platform, status):
    """Update the status of a keyword for a specific platform"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO keyword_platform_status (keyword_id, platform, last_tested_at, status)
            VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
            ON CONFLICT (keyword_id, platform) 
            DO UPDATE SET 
                last_tested_at = CURRENT_TIMESTAMP,
                status = EXCLUDED.status
        """, (keyword_id, platform, status))
        
        # Update last run in settings
        cursor.execute(f"UPDATE automation_settings SET last_run_{platform} = CURRENT_TIMESTAMP WHERE id = 1")
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error updating keyword status: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_next_keyword_for_platform(platform):
    """Get the next keyword to scrape for a platform, cycling through categories"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        # Strategy: find categories, then find the one with the oldest/least tested keywords for this platform
        cursor.execute("""
            SELECT k.id, k.category, k.keyword
            FROM automation_keywords k
            LEFT JOIN keyword_platform_status s ON k.id = s.keyword_id AND s.platform = %s
            WHERE k.is_active = TRUE
            ORDER BY s.last_tested_at NULLS FIRST, k.category, k.id
            LIMIT 1
        """, (platform,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        cursor.close()
        conn.close()

# ================================================
# PRODUCTS TABLE (Scraping pipeline)
# ================================================

def save_product_from_scraping(ai_result, platform, source_ad_id, source_tag=""):
    """
    Insert or update a product after AI analysis during scraping.
    Called by pipeline after ai_analyzer.analyze_product().

    Args:
        ai_result: Dict from ai_analyzer (with ai_analysis nested)
        platform: 'facebook', 'tiktok', 'etsy', 'amazon'
        source_ad_id: ad_archive_id or ad_id
        source_tag: keyword that triggered the scrape

    Returns:
        product id or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        analysis = ai_result.get('ai_analysis', ai_result)
        if not analysis:
            analysis = ai_result

        platform_map = {'facebook': 'meta', 'tiktok': 'tiktok'}
        store_platform = platform_map.get(platform, platform)

        product_name = ai_result.get('product_name', '') or analysis.get('what_is_it', '') or ''
        niche = analysis.get('product_category', '') or analysis.get('niche', '') or ''
        what_is_it = analysis.get('what_is_it', '')
        relevance_reason = analysis.get('relevance_reason', '')
        repackage_idea = analysis.get('digital_repackage_idea', '')
        demand_level = analysis.get('demand_level', 'MEDIUM')
        production_effort = analysis.get('production_effort', 'MEDIUM')
        verdict_priority = analysis.get('priority', 'MEDIUM')
        suggested_concepts = analysis.get('suggested_concepts', [])
        warnings = analysis.get('warnings', [])

        price_text = analysis.get('our_suggested_price', '')
        price_min = None
        price_max = None
        if price_text:
            import re
            matches = re.findall(r'\$?([\d]+)', price_text.replace(',', ''))
            if len(matches) >= 2:
                price_min = float(matches[0])
                price_max = float(matches[1])
            elif len(matches) == 1:
                price_min = float(matches[0])
                price_max = price_min

        cursor.execute("""
            INSERT INTO products (
                name, niche, status, origin_type, source_ad_id, source_platform, source_tag,
                what_is_it, repackage_idea, demand_level, production_effort,
                suggested_price_min, suggested_price_max,
                relevance_reason, suggested_ad_concepts, warnings, verdict_priority,
                scaling_score, ad_count, days_active
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_platform, source_ad_id) DO UPDATE SET
                name = COALESCE(EXCLUDED.name, products.name),
                what_is_it = COALESCE(EXCLUDED.what_is_it, products.what_is_it),
                repackage_idea = COALESCE(EXCLUDED.repackage_idea, products.repackage_idea),
                demand_level = COALESCE(EXCLUDED.demand_level, products.demand_level),
                verdict_priority = COALESCE(EXCLUDED.verdict_priority, products.verdict_priority),
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            product_name,
            niche,
            'scraping_pending',
            'scrape',
            str(source_ad_id),
            store_platform,
            source_tag,
            what_is_it,
            repackage_idea,
            demand_level,
            production_effort,
            price_min,
            price_max,
            relevance_reason,
            Json(suggested_concepts),
            Json(warnings),
            verdict_priority,
            0,  # scaling_score
            0,  # ad_count
            0   # days_active
        ))

        conn.commit()
        result = cursor.fetchone()
        return str(result[0]) if result else None
    except Exception as e:
        conn.rollback()
        print(f"Error saving product from scraping: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def get_products(status=None, platform=None, limit=100):
    """Get products for dashboard"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        if status:
            query += " AND status = %s"
            params.append(status)
        if platform:
            query += " AND source_platform = %s"
            params.append(platform)
        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)
        cursor.execute(query, params)
        return [dict(r) for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

def update_product_status(source_platform, source_ad_id, status):
    """Update product status"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE products SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE source_platform = %s AND source_ad_id = %s
        """, (status, source_platform, str(source_ad_id)))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()

def add_product_tag(source_platform, source_ad_id, tag):
    """Add a tag to a product"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM products WHERE source_platform = %s AND source_ad_id = %s", (source_platform, str(source_ad_id)))
        row = cursor.fetchone()
        if not row:
            return False
        product_id = row[0]
        cursor.execute("""
            INSERT INTO product_tags (product_id, tag) VALUES (%s, %s)
            ON CONFLICT (product_id, tag) DO NOTHING
        """, (product_id, tag))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error adding product tag: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def get_product_tags(source_platform, source_ad_id):
    """Get all tags for a product"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute("""
            SELECT t.tag, t.created_at
            FROM product_tags t
            JOIN products p ON t.product_id = p.id
            WHERE p.source_platform = %s AND p.source_ad_id = %s
            ORDER BY t.created_at
        """, (source_platform, str(source_ad_id)))
        return [r['tag'] for r in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

def save_product_after_analysis(platform, source_ad_id, ai_result, source_tag=""):
    """
    Wrapper to save a product after AI analysis.
    Call this from the pipeline after save_ai_analysis().

    Args:
        platform: 'facebook', 'tiktok', etc.
        source_ad_id: ad_archive_id or ad_id
        ai_result: full AI analysis result dict
        source_tag: keyword that triggered the scrape
    """
    try:
        save_product_from_scraping(ai_result, platform, source_ad_id, source_tag)
    except Exception as e:
        print(f"Warning: could not save product after analysis: {e}")

def save_system_prompt_history(previous_value, new_value):
    """Save system prompt change history"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO system_prompt_history (previous_value, new_value)
            VALUES (%s, %s)
        """, (previous_value, new_value))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error saving system prompt history: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
