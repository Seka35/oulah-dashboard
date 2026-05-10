#!/usr/bin/env python3
"""
TikTok Ad Intelligence - Collecte des ads (images + texte uniquement)
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

TOKEN_FILE = ".tiktok_token.json"
DATA_FILE = "ads_collected.json"


def get_access_token():
    """Récupère ou renouvelle le access token"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        # Check si expiré (avec buffer de 5 min)
        if token_data.get("expires_at", 0) > time.time() + 300:
            return token_data["access_token"]

    print("📡 Récupération nouveau Access Token...")
    resp = requests.post(
        "https://open.tiktokapis.com/v2/oauth/token/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "client_key": CLIENT_KEY,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
        },
        timeout=30
    )
    result = resp.json()

    if "access_token" not in result:
        print(f"❌ Erreur token: {result}")
        return None

    result["expires_at"] = time.time() + result.get("expires_in", 7200)

    with open(TOKEN_FILE, "w") as f:
        json.dump(result, f)

    print("✅ Token sauvegardé")
    return result["access_token"]


def search_ads(access_token, search_term, country="FR", max_count=50):
    """Recherche les ads par terme"""
    url = "https://open.tiktokapis.com/v2/research/adlib/ad/query/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "filters": {
            "ad_published_date_range": {
                "min": "20260401",
                "max": "20260430"
            },
            "country_code": country
        },
        "search_term": search_term,
        "max_count": max_count
    }

    resp = requests.post(url, headers=headers, params={"fields": "ad.id"}, json=body, timeout=30)
    return resp.json()


def get_ad_details(access_token, ad_id):
    """Récupère les détails d'un ad"""
    url = "https://open.tiktokapis.com/v2/research/adlib/ad/detail/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "fields": "ad.id,ad.image_urls,ad.videos,ad.first_shown_date,ad.last_shown_date,ad.status,advertiser.business_name,advertiser.follower_count,advertiser.avatar_url,ad.reach"
    }
    body = {"ad_id": ad_id}

    resp = requests.post(url, headers=headers, params=params, json=body, timeout=30)
    return resp.json()


def collect_ads(search_term, country="FR", max_ads=100):
    """Collecte les ads avec images uniquement (pas de vidéo)"""
    print(f"\n🔍 Recherche: '{search_term}' ({country})")

    access_token = get_access_token()
    if not access_token:
        return []

    if max_ads > 50:
        max_ads = 50
    print(f"📡 Recherche de {max_ads} ads...")
    search_result = search_ads(access_token, search_term, country)

    if "error" in search_result and search_result["error"]["code"] != "ok":
        print(f"❌ Erreur recherche: {search_result}")
        return []

    ads_ids = [a["ad"]["id"] for a in search_result.get("data", {}).get("ads", [])]
    print(f"   Trouvé {len(ads_ids)} ads")

    if not ads_ids:
        return []

    # Phase 2: Détails de chaque ad
    print("📡 Phase 2: Récupération détails...")
    collected = []
    image_only_count = 0
    video_count = 0

    for i, ad_id in enumerate(ads_ids):
        print(f"   [{i+1}/{len(ads_ids)}] Ad {ad_id}...", end=" ", flush=True)

        details = get_ad_details(access_token, ad_id)
        ad_data = details.get("data", {}).get("ad", {})
        advertiser = details.get("data", {}).get("advertiser", {})

        # Filtrer: on veut QUE images, pas de vidéo
        has_images = ad_data.get("image_urls") and len(ad_data["image_urls"]) > 0
        has_videos = ad_data.get("videos") and len(ad_data["videos"]) > 0

        if has_images and not has_videos:
            image_only_count += 1
            collected.append({
                "id": ad_id,
                "image_urls": ad_data["image_urls"],
                "first_shown_date": ad_data.get("first_shown_date"),
                "last_shown_date": ad_data.get("last_shown_date"),
                "status": ad_data.get("status"),
                "reach": ad_data.get("reach", {}),
                "advertiser_name": advertiser.get("business_name"),
                "advertiser_followers": advertiser.get("follower_count"),
                "advertiser_avatar": advertiser.get("avatar_url"),
            })
            print("✅ IMAGE ONLY")
        else:
            video_count += 1
            print("⏭️  (a vidéo, ignoré)")

    print(f"\n📊 Résultats:")
    print(f"   Total ads trouvés: {len(ads_ids)}")
    print(f"   Avec images uniquement: {image_only_count}")
    print(f"   Avec vidéo (ignoré): {video_count}")

    return collected


def main():
    if not CLIENT_KEY or not CLIENT_SECRET:
        print("❌ .env non configuré")
        print("   Ajoute TIKTOK_CLIENT_KEY et TIKTOK_CLIENT_SECRET")
        sys.exit(1)

    print("=" * 60)
    print("TIKTOK AD INTELLIGENCE")
    print("Collecte des ads photo + texte uniquement")
    print("=" * 60)

    # Collecte
    search_term = input("\n🔍 Mot-clé de recherche: ") or "coffee"
    country = input("🌍 Code pays (défaut FR): ") or "FR"
    max_ads = int(input("📦 Nombre max d'ads à collecter (défaut 50): ") or "50")

    ads = collect_ads(search_term, country, max_ads)

    # Sauvegarde
    if ads:
        with open(DATA_FILE, "w") as f:
            json.dump({
                "search_term": search_term,
                "country": country,
                "collected_at": datetime.now().isoformat(),
                "ads": ads
            }, f, indent=2)
        print(f"\n💾 {len(ads)} ads sauvegardés dans {DATA_FILE}")

        # Aperçu
        print("\n" + "=" * 60)
        print("APERÇU DES ADS COLLECTÉS")
        print("=" * 60)
        for i, ad in enumerate(ads[:5]):
            print(f"\n📌 Ad #{i+1}")
            print(f"   ID: {ad['id']}")
            print(f"   Annonceur: {ad['advertiser_name']}")
            print(f"   Images: {len(ad['image_urls'])}")
            print(f"   Dates: {ad['first_shown_date']} → {ad['last_shown_date']}")
            print(f"   Status: {ad['status']}")
            if ad['reach']:
                print(f"   Reach: {ad['reach'].get('unique_users_seen', 'N/A')}")
    else:
        print("\n⚠️  Aucun ad collecté")


if __name__ == "__main__":
    main()
