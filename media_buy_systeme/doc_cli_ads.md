# Meta Ads CLI — Guide complet pour l'IA

> **Objectif :** Créer des campagnes Meta complètes (Campaign → AdSet → Creative → Ad) de façon automatisée, en récupérant les créas depuis Cloudflare R2, avec le Pixel et la Page connectés.

---

## 1. Installation & Configuration

### Prérequis

- Python 3.12+
- pip ou uv

### Installation

```bash
pip install meta-ads-cli
# ou avec uv
uv tool install meta-ads-cli
```

### Variables d'environnement (depuis le .env)

Le CLI utilise des variables d'environnement pour éviter de mettre les secrets en clair dans les commandes.

```bash
export META_ACCESS_TOKEN="EAFZCXp5ZAZByRUBRQcAMs0jLcq1fR9H1RgpZA36eTk94pPEgLPDsRCz1AICYutaacH32kG3K4x72ECNZBJjER5mUercqCPBZCAQ9k5kOdrrbv9mZBckowr2g0GdnqyGx7yEBtGVOMVjAVsOB90uuUg9YsKCkZCfIPGopH09t3Qjpw7rDKtApdLSMhh1TFSGvXcR2VVQKZCSYwKcOGeUVAZCQPVRODZCArJDZAR7q6AePK9bD0PIDZADxVRqOaeLc4dVO2ZCQ3b9a3m3TywXbkWxcZBS5TzCv9whhhZBbggnxn3kZD"
export META_AD_ACCOUNT_ID="1034387189758630"
export META_PIXEL_ID="1369571204982537"
export META_PAGE_ID="1110205078842924"

# Cloudflare R2
export R2_ACCESS_KEY_ID="be5a65bbb8f5936c629421e9d00d5e3d"
export R2_SECRET_ACCESS_KEY="e44b182d44ec140da2cfc0e6296682b99d3b420b07fb0c74b509993d893ef77f"
export R2_ENDPOINT="https://c299aec68b696628e4c7ec8b4a98dbd2.r2.cloudflarestorage.com"
export R2_BUCKET="launch-engine-creatives"
export R2_PUBLIC_URL="https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev"
```

> **Important :** Toujours charger ces variables avant d'exécuter des commandes CLI. En CI/CD ou script, sourcer le `.env` avec `set -a && source .env && set +a`.

---

## 2. Architecture d'une campagne complète

```
Campaign  (budget, objectif)
  └── AdSet  (ciblage, enchères, schedule)
        └── Creative  (image/vidéo depuis R2 + page + pixel)
              └── Ad  (lie l'AdSet au Creative)
```

Tout est créé en statut **PAUSED** par défaut. On active à la fin.

---

## 3. Étape 0 — Récupérer les créas depuis Cloudflare R2

Les créas sont stockées dans le bucket R2 `launch-engine-creatives`. L'URL publique de chaque fichier suit le format :

```
https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev/<nom_du_fichier>
```

### Télécharger une créa localement (pour upload via CLI)

Le CLI `meta ads creative create` accepte un chemin local (`./image.jpg`) ou une URL publique selon la version. Pour garantir la compatibilité, télécharger d'abord localement avec AWS CLI (compatible S3/R2) :

```bash
# Configurer AWS CLI pour R2
aws configure set aws_access_key_id "be5a65bbb8f5936c629421e9d00d5e3d"
aws configure set aws_secret_access_key "e44b182d44ec140da2cfc0e6296682b99d3b420b07fb0c74b509993d893ef77f"

# Lister les fichiers dans le bucket
aws s3 ls s3://launch-engine-creatives/ \
  --endpoint-url https://c299aec68b696628e4c7ec8b4a98dbd2.r2.cloudflarestorage.com

# Télécharger une créa spécifique
aws s3 cp s3://launch-engine-creatives/<nom_fichier.jpg> ./creative.jpg \
  --endpoint-url https://c299aec68b696628e4c7ec8b4a98dbd2.r2.cloudflarestorage.com

# Télécharger toutes les créas d'un dossier
aws s3 sync s3://launch-engine-creatives/batch_01/ ./creatives/ \
  --endpoint-url https://c299aec68b696628e4c7ec8b4a98dbd2.r2.cloudflarestorage.com
```

### Construire l'URL publique directement (sans téléchargement)

Si le fichier est public dans R2, utiliser directement l'URL dans les commandes :

```bash
CREATIVE_URL="https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev/nom_du_fichier.jpg"
```

---

## 4. Étape 1 — Créer la Campaign

```bash
meta ads campaign create \
  --name "NOM_CAMPAGNE" \
  --objective OUTCOME_SALES \
  --daily-budget 5000 \
  --no-input
```

### Paramètres clés

| Paramètre | Description | Valeurs possibles |
|-----------|-------------|-------------------|
| `--name` | Nom de la campagne | string |
| `--objective` | Objectif pub | `OUTCOME_SALES`, `OUTCOME_LEADS`, `OUTCOME_TRAFFIC`, `OUTCOME_AWARENESS`, `OUTCOME_ENGAGEMENT`, `OUTCOME_APP_PROMOTION` |
| `--daily-budget` | Budget quotidien en centimes | ex: `5000` = 50.00€ |
| `--lifetime-budget` | Budget total en centimes | ex: `100000` = 1000.00€ |
| `--status` | Statut initial | `PAUSED` (défaut), `ACTIVE` |
| `--no-input` | Pas de prompt interactif | flag |

### Capturer le Campaign ID

```bash
CAMPAIGN_ID=$(meta ads campaign create \
  --name "Launch Engine - Batch 01" \
  --objective OUTCOME_SALES \
  --daily-budget 5000 \
  --no-input \
  --output json | jq -r '.id')

echo "Campaign créée : $CAMPAIGN_ID"
```

---

## 5. Étape 2 — Créer l'AdSet

L'AdSet définit le ciblage, les enchères et le pixel de conversion.

```bash
meta ads adset create "$CAMPAIGN_ID" \
  --name "NOM_ADSET" \
  --optimization-goal LINK_CLICKS \
  --billing-event IMPRESSIONS \
  --bid-amount 500 \
  --targeting-countries US \
  --pixel-id "$META_PIXEL_ID" \
  --no-input
```

### Paramètres clés

| Paramètre | Description | Valeurs possibles |
|-----------|-------------|-------------------|
| `--name` | Nom de l'adset | string |
| `--optimization-goal` | Objectif d'optimisation | `LINK_CLICKS`, `LANDING_PAGE_VIEWS`, `LEAD_GENERATION`, `CONVERSIONS`, `REACH`, `IMPRESSIONS` |
| `--billing-event` | Événement de facturation | `IMPRESSIONS`, `LINK_CLICKS` |
| `--bid-amount` | Enchère en centimes | ex: `500` = 5.00€ |
| `--targeting-countries` | Pays cible | codes ISO : `US`, `FR`, `ID`, `GB`… |
| `--pixel-id` | ID du pixel Meta | `$META_PIXEL_ID` = `1369571204982537` |
| `--start-time` | Date de début | ISO 8601 : `2026-05-01T00:00:00Z` |
| `--end-time` | Date de fin | ISO 8601 |
| `--daily-budget` | Budget quotidien adset | en centimes |
| `--no-input` | Pas de prompt interactif | flag |

### Capturer l'AdSet ID

```bash
ADSET_ID=$(meta ads adset create "$CAMPAIGN_ID" \
  --name "Launch Engine - Adset FR 18-45" \
  --optimization-goal CONVERSIONS \
  --billing-event IMPRESSIONS \
  --bid-amount 500 \
  --targeting-countries FR \
  --pixel-id "$META_PIXEL_ID" \
  --no-input \
  --output json | jq -r '.id')

echo "AdSet créé : $ADSET_ID"
```

---

## 6. Étape 3 — Créer le Creative (avec Page + Pixel)

Le Creative lie l'image/vidéo, le texte, la Page Facebook et le Pixel.

### Avec une image depuis R2 (chemin local après téléchargement)

```bash
meta ads creative create \
  --name "NOM_CREATIVE" \
  --page-id "$META_PAGE_ID" \
  --image ./creative.jpg \
  --body "Texte du body de la pub" \
  --title "Titre accrocheur" \
  --link-url "https://example.com/landing" \
  --call-to-action SHOP_NOW \
  --no-input
```

### Avec une URL publique R2 (sans téléchargement)

```bash
meta ads creative create \
  --name "NOM_CREATIVE" \
  --page-id "$META_PAGE_ID" \
  --image-url "https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev/nom_fichier.jpg" \
  --body "Texte du body de la pub" \
  --title "Titre accrocheur" \
  --link-url "https://example.com/landing" \
  --call-to-action SHOP_NOW \
  --no-input
```

### Paramètres clés

| Paramètre | Description | Valeurs |
|-----------|-------------|---------|
| `--name` | Nom du creative | string |
| `--page-id` | Page Facebook liée | `$META_PAGE_ID` = `1110205078842924` |
| `--image` | Chemin local de l'image | `./creative.jpg` |
| `--image-url` | URL publique de l'image | URL R2 publique |
| `--body` | Texte principal de la pub | string |
| `--title` | Titre de la pub | string |
| `--description` | Description sous le titre | string |
| `--link-url` | URL de destination du clic | URL complète |
| `--call-to-action` | Bouton CTA | `SHOP_NOW`, `LEARN_MORE`, `SIGN_UP`, `DOWNLOAD`, `CONTACT_US`, `GET_QUOTE`, `BOOK_NOW` |
| `--no-input` | Pas de prompt interactif | flag |

### Capturer le Creative ID

```bash
CREATIVE_ID=$(meta ads creative create \
  --name "Hero Banner - Batch01 v1" \
  --page-id "$META_PAGE_ID" \
  --image-url "https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev/creative_01.jpg" \
  --body "Découvrez notre offre exclusive 🔥" \
  --title "Profitez maintenant" \
  --link-url "https://example.com/offre" \
  --call-to-action SHOP_NOW \
  --no-input \
  --output json | jq -r '.id')

echo "Creative créé : $CREATIVE_ID"
```

---

## 7. Étape 4 — Connecter le Pixel au Creative / Dataset

Connecter le Pixel (Dataset) à l'Ad Account pour le tracking des conversions :

```bash
# Connecter le pixel à l'ad account
meta ads dataset connect "$META_PIXEL_ID" \
  --ad-account-id "$META_AD_ACCOUNT_ID" \
  --no-input
```

> **Note :** Cette connexion est généralement déjà établie si le pixel a été créé dans le Business Manager. La relancer est idempotente (pas d'erreur si déjà connecté).

---

## 8. Étape 5 — Créer l'Ad (liaison AdSet + Creative)

```bash
meta ads ad create "$ADSET_ID" \
  --name "NOM_AD" \
  --creative-id "$CREATIVE_ID" \
  --no-input
```

### Capturer l'Ad ID

```bash
AD_ID=$(meta ads ad create "$ADSET_ID" \
  --name "Hero Banner Ad - v1" \
  --creative-id "$CREATIVE_ID" \
  --no-input \
  --output json | jq -r '.id')

echo "Ad créée : $AD_ID"
```

---

## 9. Étape 6 — Activer la campagne

Tout est en PAUSED. Activer dans l'ordre :

```bash
# 1. Activer la Campaign
meta ads campaign update "$CAMPAIGN_ID" --status ACTIVE --no-input

# 2. Activer l'AdSet
meta ads adset update "$ADSET_ID" --status ACTIVE --no-input

# 3. Activer l'Ad
meta ads ad update "$AD_ID" --status ACTIVE --no-input

echo "✅ Campagne live : $CAMPAIGN_ID"
```

---

## 10. Script complet — Pipeline automatisé R2 → Meta

Script bash prêt à l'emploi pour créer une campagne complète depuis une créa R2.

```bash
#!/bin/bash
set -euo pipefail

# ─── CONFIG ────────────────────────────────────────
export META_ACCESS_TOKEN="EAFZCXp5ZAZByRUBRQcAMs0jLcq1fR9H1RgpZA36eTk94pPEgLPDsRCz1AICYutaacH32kG3K4x72ECNZBJjER5mUercqCPBZCAQ9k5kOdrrbv9mZBckowr2g0GdnqyGx7yEBtGVOMVjAVsOB90uuUg9YsKCkZCfIPGopH09t3Qjpw7rDKtApdLSMhh1TFSGvXcR2VVQKZCSYwKcOGeUVAZCQPVRODZCArJDZAR7q6AePK9bD0PIDZADxVRqOaeLc4dVO2ZCQ3b9a3m3TywXbkWxcZBS5TzCv9whhhZBbggnxn3kZD"
export META_AD_ACCOUNT_ID="1034387189758630"
export META_PIXEL_ID="1369571204982537"
export META_PAGE_ID="1110205078842924"
export R2_PUBLIC_URL="https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev"

# ─── PARAMÈTRES À PERSONNALISER ─────────────────────
CAMPAIGN_NAME="Launch Engine - $(date +%Y%m%d)"
ADSET_NAME="Adset FR - $(date +%Y%m%d)"
CREATIVE_NAME="Creative - $(date +%Y%m%d)"
AD_NAME="Ad - $(date +%Y%m%d)"

R2_FILE="nom_du_fichier.jpg"        # nom du fichier dans R2
CREATIVE_URL="${R2_PUBLIC_URL}/${R2_FILE}"

AD_BODY="Texte de la pub ici 🔥"
AD_TITLE="Titre accrocheur"
AD_LINK="https://example.com/landing"
AD_CTA="SHOP_NOW"

DAILY_BUDGET=5000                    # en centimes (50.00€)
TARGET_COUNTRIES="FR"
BID_AMOUNT=500                       # en centimes (5.00€)

# ─── STEP 1 : CAMPAIGN ─────────────────────────────
echo "📦 Création de la campagne..."
CAMPAIGN_ID=$(meta ads campaign create \
  --name "$CAMPAIGN_NAME" \
  --objective OUTCOME_SALES \
  --daily-budget "$DAILY_BUDGET" \
  --no-input \
  --output json | jq -r '.id')
echo "✅ Campaign ID : $CAMPAIGN_ID"

# ─── STEP 2 : ADSET ────────────────────────────────
echo "🎯 Création de l'adset..."
ADSET_ID=$(meta ads adset create "$CAMPAIGN_ID" \
  --name "$ADSET_NAME" \
  --optimization-goal CONVERSIONS \
  --billing-event IMPRESSIONS \
  --bid-amount "$BID_AMOUNT" \
  --targeting-countries "$TARGET_COUNTRIES" \
  --pixel-id "$META_PIXEL_ID" \
  --no-input \
  --output json | jq -r '.id')
echo "✅ AdSet ID : $ADSET_ID"

# ─── STEP 3 : CONNECT PIXEL ────────────────────────
echo "🔗 Connexion du pixel à l'ad account..."
meta ads dataset connect "$META_PIXEL_ID" \
  --ad-account-id "$META_AD_ACCOUNT_ID" \
  --no-input || echo "⚠️  Pixel déjà connecté (OK)"

# ─── STEP 4 : CREATIVE ─────────────────────────────
echo "🖼️  Création du creative depuis R2..."
CREATIVE_ID=$(meta ads creative create \
  --name "$CREATIVE_NAME" \
  --page-id "$META_PAGE_ID" \
  --image-url "$CREATIVE_URL" \
  --body "$AD_BODY" \
  --title "$AD_TITLE" \
  --link-url "$AD_LINK" \
  --call-to-action "$AD_CTA" \
  --no-input \
  --output json | jq -r '.id')
echo "✅ Creative ID : $CREATIVE_ID"

# ─── STEP 5 : AD ───────────────────────────────────
echo "📣 Création de l'ad..."
AD_ID=$(meta ads ad create "$ADSET_ID" \
  --name "$AD_NAME" \
  --creative-id "$CREATIVE_ID" \
  --no-input \
  --output json | jq -r '.id')
echo "✅ Ad ID : $AD_ID"

# ─── STEP 6 : ACTIVATION ───────────────────────────
echo "🚀 Activation de la campagne..."
meta ads campaign update "$CAMPAIGN_ID" --status ACTIVE --no-input
meta ads adset update "$ADSET_ID" --status ACTIVE --no-input
meta ads ad update "$AD_ID" --status ACTIVE --no-input

echo ""
echo "═══════════════════════════════════════════"
echo "✅ CAMPAGNE LIVE"
echo "Campaign ID : $CAMPAIGN_ID"
echo "AdSet ID    : $ADSET_ID"
echo "Creative ID : $CREATIVE_ID"
echo "Ad ID       : $AD_ID"
echo "═══════════════════════════════════════════"
```

---

## 11. Script multi-créas — Batch depuis R2

Pour lancer plusieurs créas en boucle depuis une liste de fichiers R2 :

```bash
#!/bin/bash
set -euo pipefail

# Source les variables d'env
set -a && source .env && set +a

R2_PUBLIC_URL="https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev"

# Liste des créas à lancer (fichiers dans R2)
CREATIVES=(
  "creative_01.jpg|Offre spéciale 🔥|Achetez maintenant|https://example.com/p1|SHOP_NOW"
  "creative_02.jpg|Découvrez notre service|En savoir plus|https://example.com/p2|LEARN_MORE"
  "creative_03.jpg|Inscription gratuite 🎁|Rejoindre|https://example.com/p3|SIGN_UP"
)

# Créer UNE campagne pour tout le batch
CAMPAIGN_ID=$(meta ads campaign create \
  --name "Batch $(date +%Y%m%d-%H%M)" \
  --objective OUTCOME_SALES \
  --daily-budget 15000 \
  --no-input --output json | jq -r '.id')
echo "📦 Campaign : $CAMPAIGN_ID"

for ENTRY in "${CREATIVES[@]}"; do
  IFS='|' read -r FILE BODY TITLE LINK CTA <<< "$ENTRY"

  # AdSet par créa
  ADSET_ID=$(meta ads adset create "$CAMPAIGN_ID" \
    --name "Adset - $FILE" \
    --optimization-goal CONVERSIONS \
    --billing-event IMPRESSIONS \
    --bid-amount 500 \
    --targeting-countries FR \
    --pixel-id "$META_PIXEL_ID" \
    --no-input --output json | jq -r '.id')

  # Creative depuis R2
  CREATIVE_ID=$(meta ads creative create \
    --name "Creative - $FILE" \
    --page-id "$META_PAGE_ID" \
    --image-url "${R2_PUBLIC_URL}/${FILE}" \
    --body "$BODY" \
    --title "$TITLE" \
    --link-url "$LINK" \
    --call-to-action "$CTA" \
    --no-input --output json | jq -r '.id')

  # Ad
  AD_ID=$(meta ads ad create "$ADSET_ID" \
    --name "Ad - $FILE" \
    --creative-id "$CREATIVE_ID" \
    --no-input --output json | jq -r '.id')

  # Activer
  meta ads adset update "$ADSET_ID" --status ACTIVE --no-input
  meta ads ad update "$AD_ID" --status ACTIVE --no-input

  echo "✅ [$FILE] → Campaign=$CAMPAIGN_ID | Adset=$ADSET_ID | Ad=$AD_ID"
done

# Activer la campagne globale
meta ads campaign update "$CAMPAIGN_ID" --status ACTIVE --no-input
echo "🚀 Batch live : $CAMPAIGN_ID"
```

---

## 12. Commandes de monitoring & insights

### Lister les campagnes

```bash
meta ads campaign list --output table
meta ads campaign list --output json | jq '.[].name'
```

### Lister les adsets d'une campagne

```bash
meta ads adset list --campaign-id "$CAMPAIGN_ID" --output table
```

### Lister les ads d'un adset

```bash
meta ads ad list --adset-id "$ADSET_ID" --output table
```

### Insights de performance

```bash
# Résultats des 7 derniers jours
meta ads insights get \
  --campaign-id "$CAMPAIGN_ID" \
  --fields impressions,clicks,spend,ctr,conversions \
  --date-preset last_7d

# Breakdown par âge et genre
meta ads insights get \
  --campaign-id "$CAMPAIGN_ID" \
  --fields impressions,spend,conversions \
  --date-preset last_30d \
  --breakdown age,gender

# Export JSON pour parsing
meta ads insights get \
  --campaign-id "$CAMPAIGN_ID" \
  --fields impressions,clicks,spend,ctr,cpc,roas \
  --date-preset last_7d \
  --output json | jq '.[] | {campaign: .campaign_name, spend: .spend, roas: .purchase_roas}'
```

### Vérifier le statut du pixel

```bash
meta ads dataset list --output table
```

---

## 13. Gestion des erreurs & codes de sortie

| Code | Signification |
|------|--------------|
| `0` | Succès |
| `3` | Erreur d'authentification (token expiré ou invalide) |
| `4` | Erreur API Meta (mauvais paramètre, limite atteinte) |

### Gestion dans un script

```bash
meta ads campaign create --name "Test" --objective OUTCOME_SALES --daily-budget 5000 --no-input
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "✅ Succès" ;;
  3) echo "❌ Token invalide — renouveler META_ACCESS_TOKEN" ;;
  4) echo "❌ Erreur API Meta — vérifier les paramètres" ;;
  *) echo "❌ Erreur inconnue (code $EXIT_CODE)" ;;
esac
```

---

## 14. Formats d'output

| Flag | Format | Usage |
|------|--------|-------|
| `--output table` | Tableau lisible | Debug interactif |
| `--output json` | JSON complet | Parsing avec `jq`, scripts |
| `--output plain` | Tab-séparé | `awk`, `cut`, `sort` |

### Exemples de parsing JSON

```bash
# Extraire l'ID d'une entité créée
ID=$(meta ads campaign create ... --output json | jq -r '.id')

# Lister tous les IDs de campagnes actives
meta ads campaign list --output json | jq -r '.[] | select(.status == "ACTIVE") | .id'

# Extraire le spend total d'insights
meta ads insights get --campaign-id "$CAMPAIGN_ID" --fields spend --date-preset last_7d \
  --output json | jq -r '.[0].spend'
```

---

## 15. Flags globaux utiles

| Flag | Description |
|------|-------------|
| `--no-input` | Désactive tous les prompts interactifs (obligatoire en CI/CD) |
| `--force` | Confirme automatiquement les actions destructives |
| `--output json/table/plain` | Format de sortie |
| `--help` | Aide sur une commande |

---

## 16. Référence rapide — IDs du compte

| Variable | Valeur |
|----------|--------|
| `META_AD_ACCOUNT_ID` | `1034387189758630` |
| `META_PIXEL_ID` | `1369571204982537` |
| `META_PAGE_ID` | `1110205078842924` |
| `R2_BUCKET` | `launch-engine-creatives` |
| `R2_PUBLIC_URL` | `https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev` |

---

## 17. Checklist de lancement

- [ ] Variables d'env chargées (`META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, `META_PAGE_ID`, `META_PIXEL_ID`)
- [ ] Fichier créa disponible dans R2 bucket `launch-engine-creatives`
- [ ] URL publique R2 construite : `R2_PUBLIC_URL/nom_fichier.jpg`
- [ ] Campaign créée (PAUSED) → ID capturé
- [ ] AdSet créé avec `--pixel-id` (PAUSED) → ID capturé
- [ ] Pixel connecté à l'ad account (`meta ads dataset connect`)
- [ ] Creative créé avec `--page-id` et `--image-url` → ID capturé
- [ ] Ad créée en liant AdSet + Creative → ID capturé
- [ ] Activation Campaign → AdSet → Ad (`--status ACTIVE`)
- [ ] Vérification insights après 24h
