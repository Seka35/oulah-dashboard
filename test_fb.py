
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
APIFY_KEY = os.getenv("APIFY_KEY")
FACEBOOK_ACTOR = "curious_coder~facebook-ads-library-scraper"

def test_facebook():
    search_term = "nike"
    search_url = f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&q={search_term}&search_type=keyword_unordered&media_type=all"
    
    input_data = {
        "count": 5,
        "scrapeAdDetails": True,
        "scrapePageAds.activeStatus": "all",
        "scrapePageAds.countryCode": "ALL",
        "scrapePageAds.sortBy": "impressions_desc",
        "urls": [{"url": search_url}]
    }
    
    print(f"Starting actor {FACEBOOK_ACTOR}...")
    resp = requests.post(
        f"https://api.apify.com/v2/acts/{FACEBOOK_ACTOR}/runs?token={APIFY_KEY}",
        json=input_data
    )
    print(f"Status: {resp.status_code}")
    print(resp.json())

if __name__ == "__main__":
    test_facebook()
