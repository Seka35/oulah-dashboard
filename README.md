# Ad Intelligence Dashboard

Analysez les publicités TikTok et Facebook via Apify avec une interface Flask.

## Prérequis

- Python 3.10+
- PostgreSQL (ou SQLite pour test)
- Clé API Apify
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
APIFY_KEY=votre_cle_apify
DATABASE_URL=postgresql://user:password@localhost:5432/ads_db
FLASK_SECRET=your_secret_key_here
```

## Lancer l'application

```bash
# Mode développement
source .venv/bin/activate
python app.py

# Mode production (avec nohup)
nohup python app.py > app.log 2>&1 &
```

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
├── static/             # Assets CSS/JS/media
├── templates/          # Templates HTML
└── migrations/         # Migrations SQL
```

## Commandes utiles

```bash
# Voir les logs
tail -f app.log

# Arrêter l'application
pkill -f "python app.py"

# Backup de la DB
sqlite3 search_history.db ".backup full_db_backup.sql"
```

## API Endpoints principaux

- `GET /` - Dashboard
- `POST /search` - Lancer une recherche
- `GET /results/<search_id>` - Voir les résultats
- `GET /history` - Historique des recherches