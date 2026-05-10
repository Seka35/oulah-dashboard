# Ad Intelligence Dashboard

Analysez les publicités TikTok et Facebook via Apify avec une interface Flask.

## Prérequis

- Python 3.10+
- PostgreSQL (avec support Unix socket)
- Git

## Installation

```bash
# Cloner le repo
git clone https://github.com/Seka35/oulah-dashboard.git
cd oulah-dashboard

# Créer le venv
python3 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditez .env avec vos clés API
```

## Configuration (.env)

```env
# TikTok API
TIKTOK_CLIENT_KEY=your_tiktok_client_key
TIKTOK_CLIENT_SECRET=your_tiktok_client_secret

# Facebook API
FACEBOOK_ACCESS_TOKEN=your_facebook_access_token

# Apify API
APIFY_KEY=your_apify_api_key

# Open Router (IA)
OPENROUTER_KEY=your_openrouter_api_key
MODEL_OPENROUTER=minimax/minimax-m2.7

# Database PostgreSQL (Unix socket)
DATABASE_URL=postgresql://user@/database_name
```

## Lancer l'application

```bash
# Activer le venv
source .venv/bin/activate

# Lancer Flask (dashboard)
python app.py

# Dans un autre terminal: lancer le worker pour download les médias
python media_worker.py
```

**Note:** `media_worker.py` doit tourner en parallèle pour download automatiquement les images/vidéos des publicités.

L'application sera accessible sur `http://localhost:5000`

## Structure du projet

```
├── app.py              # Application Flask principale
├── db.py               # Couche base de données
├── ai_analyzer.py      # Analyse IA des publicités
├── scrapers.py         # Scrapers TikTok/Facebook
├── pipeline.py         # Pipeline de traitement
├── classifier.py       # Classification des produits
├── requirements.txt    # Dépendances Python
├── migrations/         # Migrations SQL
├── templates/          # Templates HTML
└── static/             # Assets CSS/JS/media
```

## Commandes utiles

```bash
# Voir les logs
tail -f app.log

# Arrêter l'application
pkill -f "python app.py"

# Se connecter à PostgreSQL
psql -U anon-404 -d analyse_ad
```

## API Endpoints principaux

- `GET /` - Dashboard
- `POST /search` - Lancer une recherche
- `GET /results/<search_id>` - Voir les résultats
- `GET /history` - Historique des recherches