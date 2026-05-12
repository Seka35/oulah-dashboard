# Meta Media Buy System

Flask dashboard + CLI pour créer et lancer des campagnes Meta Ads depuis PostgreSQL (Neon) avec des créatives sur Cloudflare R2.

## Setup

```bash
cd media_buy_systeme
cp .env.example .env
# Édite .env avec tes credentials

pip install -r requirements.txt
python run.py
# → http://localhost:5000
```

## Variables d'environnement

| Variable | Description |
|----------|-------------|
| `META_AD_ACCOUNT_ID` | ID du compte Meta (sans `act_`) |
| `META_ACCESS_TOKEN` | Token d'accès Meta Marketing API |
| `META_PAGE_ID` | ID de la Page Facebook pour les ads |
| `META_PIXEL_ID` | ID du Pixel pour le tracking |
| `DATABASE_URL` | URL de connexion Neon PostgreSQL |
| `R2_ACCESS_KEY_ID` | Clé d'accès R2 |
| `R2_SECRET_ACCESS_KEY` | Clé secrète R2 |
| `R2_ENDPOINT` | Endpoint R2 (ex: `https://xxx.r2.dev`) |
| `R2_BUCKET` | Nom du bucket R2 |
| `R2_PUBLIC_URL` | URL publique du bucket |

## Lancer une campagne

1. Créer une campagne via `/campaigns/new`
2. Sélectionner une creative depuis R2
3. Choisir status : `DRAFT` (non lancé) ou `PAUSED` / `ACTIVE`
4. Cliquer **Launch** pour publier sur Meta

## CLI

```bash
# Dry run (preview sans créer)
python meta_bulk_campaigns.py --dry-run

# Lancer toutes les campagnes en attente
python meta_bulk_campaigns.py --retry

# Lister les créatives R2
python meta_bulk_campaigns.py --list-creatives
```

## Architecture

```
app/
├── config.py          # Chargement .env
├── models.py          # CRUD campagnes DB
├── routes/
│   ├── dashboard.py   # GET /
│   ├── campaigns.py   # CRUD /campaigns
│   └── launch.py      # POST /launch/<id>
├── services/
│   ├── meta_cli.py    # API Meta Marketing (direct)
│   ├── r2.py           # Client R2 + cache 30s
│   └── campaign_launcher.py  # Lancement transactionnel
└── templates/         # Bootstrap UI
```

## Schema DB

Voir `schema.sql` — table `campaigns` avec tous les champs nécessaires.

## Note

- Le launch utilise l'API Meta directe (plus stable que le CLI `meta-ads`)
- Retry 3x avec backoff exponentiel
- Rollback automatique si échec après création campaign