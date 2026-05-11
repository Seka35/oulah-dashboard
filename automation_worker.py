import time
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Add current directory to path
sys.path.append(os.getcwd())

import db
import scrapers
import ai_analyzer

load_dotenv()

MAX_AI_WORKERS = 8

def run_automation_cycle():
    print(f"[{datetime.now()}] Checking automation settings...")
    settings = db.get_automation_settings()

    if not settings or not settings.get('is_active'):
        print("Automation is disabled. Skipping.")
        return

    platforms = ['tiktok', 'facebook', 'etsy', 'amazon']

    for platform in platforms:
        freq_hours = settings.get(f'{platform}_frequency_hours', 24)
        last_run = settings.get(f'last_run_{platform}')

        # Check if it's time to run
        should_run = False
        if not last_run:
            should_run = True
        else:
            time_diff = datetime.now() - last_run
            if time_diff.total_seconds() >= freq_hours * 3600:
                should_run = True

        if should_run:
            print(f"Running automation for {platform}...")
            keyword_info = db.get_next_keyword_for_platform(platform)

            if not keyword_info:
                print(f"No more keywords to test for {platform}.")
                continue

            keyword = keyword_info['keyword']
            keyword_id = keyword_info['id']
            max_results = settings.get(f'{platform}_max_ads' if platform in ['tiktok', 'facebook'] else f'{platform}_max_products', 20)

            print(f"Scraping '{keyword}' on {platform} (limit: {max_results})...")

            try:
                results = []
                error = None

                if platform == 'tiktok':
                    results, error = scrapers.search_tiktok(keyword, max_ads=max_results)
                    if not error:
                        db.save_search(keyword, "all", "ALL", "", max_results, results)
                elif platform == 'facebook':
                    results, error = scrapers.search_facebook(keyword, max_ads=max_results)
                    if not error:
                        db.save_search(keyword, "all", "ALL", "", max_results, results)
                elif platform == 'etsy':
                    results, error = scrapers.search_etsy(keyword, max_items=max_results)
                    if not error:
                        db.save_etsy_products(results, keyword)
                elif platform == 'amazon':
                    results, error = scrapers.search_amazon(keyword, max_items=max_results)
                    if not error:
                        db.save_amazon_products(results, keyword)

                if error:
                    print(f"Error scraping {platform}: {error}")
                    db.update_keyword_status(keyword_id, platform, 'failed')
                else:
                    print(f"Successfully scraped {len(results)} items from {platform}.")
                    db.update_keyword_status(keyword_id, platform, 'completed')

                    # Run AI analysis on all scraped results
                    print(f"🤖 Running AI analysis on {len(results)} {platform} items...")
                    analyze_platform_results(results, platform)
                    print(f"✅ AI analysis complete for {platform}")

            except Exception as e:
                print(f"Exception during automation for {platform}: {e}")
                db.update_keyword_status(keyword_id, platform, 'failed')
        else:
            print(f"Next run for {platform} in {timedelta(hours=freq_hours) - (datetime.now() - last_run) if last_run else 'now'}")


def analyze_platform_results(results, platform):
    """Run AI analysis on all scraped results"""

    def analyze_single(item):
        try:
            iid = item.get('id') or item.get('asin') or item.get('listing_id')
            if not iid:
                return None

            # Check if already has ai_analysis
            if item.get('ai_analysis'):
                return None

            raw_data = item.get('_raw', item)
            print(f"  🤖 Analyzing {platform}/{iid}...")
            res = ai_analyzer.analyze_product(raw_data, platform)
            if res and 'error' not in res:
                db.save_ai_analysis(platform, iid, res)
                print(f"    ✅ Done: {res.get('ai_analysis', {}).get('priority', 'N/A')}")
                return res
            else:
                print(f"    ❌ Failed: {res.get('error', 'unknown') if res else 'no response'}")
                return None
        except Exception as e:
            print(f"    ❌ Error: {e}")
            return None

    # Process in parallel
    with ThreadPoolExecutor(max_workers=MAX_AI_WORKERS) as executor:
        list(executor.map(analyze_single, results))

    print(f"  📊 Analyzed {len(results)} items for {platform}")

def start_automation_worker():
    print("Automation worker thread started.")
    while True:
        try:
            run_automation_cycle()
        except Exception as e:
            print(f"Global worker error: {e}")
        
        # Wait 1 hour before checking again
        time.sleep(3600)

if __name__ == "__main__":
    start_automation_worker()
