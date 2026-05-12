#!/usr/bin/env python3
"""
meta_bulk_campaigns.py
─────────────────────────────────────────────────────────────
Bulk campaign creator via Meta Ads CLI
- Données    : PostgreSQL (Neon)
- Creatives  : Cloudflare R2
- Launcher   : meta-ads CLI

Usage:
  python meta_bulk_campaigns.py            # run normal
  python meta_bulk_campaigns.py --dry-run  # preview sans rien créer
  python meta_bulk_campaigns.py --list-creatives  # liste les fichiers R2
  python meta_bulk_campaigns.py --retry   # active le retry 3x sur CLI

Schema DB attendu:
  TABLE campaigns (
    id                SERIAL PRIMARY KEY,
    name              TEXT NOT NULL,
    objective         TEXT DEFAULT 'OUTCOME_LEADS',
    budget            INT  DEFAULT 5000,   -- centimes (5000 = 50€)
    budget_type       TEXT DEFAULT 'DAILY',
    countries         TEXT DEFAULT 'FR',
    age_min           INT  DEFAULT 18,
    age_max           INT  DEFAULT 65,
    creative_key      TEXT,               -- nom du fichier dans R2
    ad_title          TEXT,
    ad_body           TEXT,
    cta_link          TEXT,
    status            TEXT DEFAULT 'PAUSED',
    meta_campaign_id  TEXT,
    launched          BOOLEAN DEFAULT FALSE,
    launched_at       TIMESTAMP
  );
─────────────────────────────────────────────────────────────
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.r2 import R2Client
from app.services.campaign_launcher import CampaignLauncher
from app.models import Campaign

# ─────────────────────────────────────────────
#  TERMINAL COLORS
# ─────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):    print(f"{GREEN}  ✓  {msg}{RESET}")
def err(msg):   print(f"{RED}  ✗  {msg}{RESET}")
def info(msg):  print(f"{CYAN}  →  {msg}{RESET}")
def warn(msg):  print(f"{YELLOW}  ⚠  {msg}{RESET}")
def title(msg): print(f"\n{BOLD}{msg}{RESET}\n{'─'*50}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def run(dry_run=False, max_retries=1):
    title("🚀 Meta Bulk Campaign Launcher")

    info("Connexion à la base de données...")
    try:
        campaigns = Campaign.fetch_pending()
    except Exception as e:
        err(f"Erreur DB : {e}")
        sys.exit(1)

    if not campaigns:
        warn("Aucune campagne en attente (launched = FALSE)")
        return

    ok(f"{len(campaigns)} campagne(s) à lancer")

    launcher = CampaignLauncher(max_retries=max_retries, dry_run=dry_run)
    results = launcher.launch_all_pending()

    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    title("📊 Résumé")
    ok(f"{success_count} campagne(s) lancée(s)")
    if fail_count:
        err(f"{fail_count} campagne(s) en erreur")
        for r in results:
            if not r["success"]:
                print(f"  {DIM}{r['name']}{RESET} → {r.get('error', 'unknown')}")

    if dry_run:
        warn("Mode DRY RUN — rien n'a été créé sur Meta")


# ─────────────────────────────────────────────
#  ENTRYPOINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Meta Bulk Campaign Launcher")
    parser.add_argument("--dry-run",        action="store_true", help="Preview sans créer")
    parser.add_argument("--retry",          action="store_true", help="Activer retry 3x sur CLI")
    parser.add_argument("--list-creatives", action="store_true", help="Lister les fichiers R2")
    args = parser.parse_args()

    if args.list_creatives:
        title("📁 Creatives dans R2")
        try:
            r2 = R2Client()
            files = r2.list_creatives()
            if not files:
                warn("Bucket vide")
            for f in files:
                print(f"  {DIM}{f['size_kb']} KB{RESET}  {f['key']}")
                print(f"         {DIM}{f['url']}{RESET}")
        except Exception as e:
            err(f"Erreur R2 : {e}")
        sys.exit(0)

    max_retries = 3 if args.retry else 1
    run(dry_run=args.dry_run, max_retries=max_retries)