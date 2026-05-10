#!/usr/bin/env python3
"""
Test de connexion TikTok API
Récupère l'access token et teste les endpoints de base
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")

if not CLIENT_KEY or not CLIENT_SECRET:
    print("❌ Credentials manquantes dans .env")
    print("   Assure-toi d'avoir ajouté TIKTOK_CLIENT_KEY et TIKTOK_CLIENT_SECRET")
    sys.exit(1)

print("=" * 50)
print("TIKTOK API - Test de connexion")
print("=" * 50)

# 1. Obtenir le Access Token
print("\n📡 Étape 1: Récupération du Access Token...")

token_url = "https://open.tiktokapis.com/v2/oauth/token/"
headers = {"Content-Type": "application/x-www-form-urlencoded"}
data = {
    "client_key": CLIENT_KEY,
    "client_secret": CLIENT_SECRET,
    "grant_type": "client_credentials"
}

try:
    response = requests.post(token_url, headers=headers, data=data, timeout=30)
    token_result = response.json()

    if "access_token" in token_result:
        access_token = token_result["access_token"]
        print(f"✅ Token obtenu avec succès")
        print(f"   Token: {access_token[:20]}...")
        print(f"   Expire dans: {token_result.get('expires_in', 'N/A')} secondes")

        # Sauvegarder le token pour usage后续
        with open(".tiktok_token.json", "w") as f:
            json.dump(token_result, f)
        print("   Token sauvegardé dans .tiktok_token.json")
    else:
        print(f"❌ Erreur token: {token_result}")
        sys.exit(1)

except requests.exceptions.RequestException as e:
    print(f"❌ Erreur de connexion: {e}")
    sys.exit(1)

# 2. Tester un endpoint simple - info utilisateur
print("\n📡 Étape 2: Test de l'API (User Info)...")

user_url = "https://open.tiktokapis.com/v2/user/info/"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
body = {"fields": ["open_id", "union_id", "avatar_url"]}

try:
    response = requests.post(user_url, headers=headers, json=body, timeout=30)
    result = response.json()

    if response.status_code == 200:
        print(f"✅ Connexion API réussie!")
        print(f"   Données utilisateur: {json.dumps(result, indent=2)}")
    else:
        print(f"⚠️  Réponse API: {result}")
        print(f"   Status code: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"❌ Erreur lors du test API: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("TEST TERMINÉ")
print("=" * 50)
