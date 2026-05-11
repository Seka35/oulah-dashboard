# Ad Intelligence Dashboard

Analysez les publicités TikTok et Facebook via Apify avec une interface Flask.

## Prérequis

- Python 3.10+
- PostgreSQL (Neon ou local)
- Git
- Cloudflare R2 (stockage média)

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
# ======= API KEYS =======
# Apify API (scraping TikTok, Facebook, Etsy, Amazon)
APIFY_KEY=your_apify_api_key

# Open Router (IA - Analyse des produits)
OPENROUTER_KEY=your_openrouter_api_key
MODEL_OPENROUTER=anthropic/claude-3.5-sonnet

# ======= DATABASE (Neon PostgreSQL) =======
DATABASE_URL=postgresql://neondb_owner:xxx@ep-hidden-xxx.neon.tech/neondb?sslmode=require&channel_binding=require

# ======= R2 STORAGE (Cloudflare) =======
# Pour les créatives: scrape/meta/<ad_id>/creative-<n>.ext
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_ENDPOINT=https://xxxx.r2.cloudflarestorage.com
R2_BUCKET=launch-engine-creatives
R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

## Lancer l'application

```bash
# Activer le venv
source .venv/bin/activate

# Lancer Flask (dashboard)
python app.py

# Dans un autre terminal: lancer le worker pour download/upload les médias vers R2
python media_worker.py

# Optionnel: lancer le pipeline d'analyse
python pipeline.py
```

**Note:** `media_worker.py` doit tourner en parallèle pour download automatiquement les images/vidéos et les uploader vers Cloudflare R2.

L'application sera accessible sur `http://localhost:5000`

## Structure du projet

```
├── app.py              # Application Flask principale
├── db.py               # Couche base de données
├── ai_analyzer.py      # Analyse IA des publicités
├── scrapers.py         # Scrapers TikTok/Facebook
├── pipeline.py         # Pipeline de traitement
├── classifier.py       # Classification des produits
├── r2_storage.py       # Intégration Cloudflare R2
├── media_worker.py     # Worker download/upload média
├── requirements.txt    # Dépendances Python
├── migrations/         # Migrations SQL
├── templates/          # Templates HTML
└── static/             # Assets CSS/JS
```

## Commandes utiles

```bash
# Voir les logs
tail -f app.log

# Arrêter l'application
pkill -f "python app.py"

# Exécuter les migrations SQL sur Neon
psql $DATABASE_URL -f migrations/004_products_and_settings.sql
```

## API Endpoints principaux

- `GET /` - Dashboard
- `POST /api/search` - Lancer une recherche
- `GET /api/history` - Historique des recherches
- `GET /api/ads/all` - Toutes les ads avec média
- `GET /api/opportunities` - Opportunités produits
- `GET /api/products` - Produits du pipeline scraping
- `POST /api/products/<opportunity_id>/tag` - Ajouter un tag à un produit

## Workflow

1. **Scraping**: Apify récupère les ads TikTok/FB/Etsy/Amazon
2. **Download**: `media_worker.py` download les créatives → upload vers R2
3. **AI Analysis**: `ai_analyzer.py` analyse chaque produit
4. **Pipeline**: `pipeline.py` classifie et crée les opportunités
5. **Dashboard**: Frontend affiche via les API endpoints