# Database Schema - Analyse AD TikTok/Facebook

## Vue d'ensemble

```
┌─────────────────────┐       ┌─────────────────────┐
│    crawl_jobs        │       │    advertisers      │
├─────────────────────┤       ├─────────────────────┤
│ id (PK)             │       │ page_id (PK)        │
│ source              │◄──────│ page_name           │
│ query               │       │ page_alias          │
│ ran_at              │       │ page_category       │
│ total_results       │       │ page_like_count     │
│ ads_inserted        │       │ page_is_deleted     │
│ ads_updated         │       │ page_is_restricted  │
│ status              │       │ page_profile_uri    │
│ apify_run_id        │       │ page_verification   │
└─────────────────────┘       │ ig_followers         │
                              │ ig_username         │
                              │ about_text          │
                              │ profile_photo_url   │
                              │ page_cover_photo_url│
                              │ raw_json (JSONB)    │
                              └─────────┬───────────┘
                                        │
┌─────────────────────┐                 │
│       ads            │◄───────────────┘
├─────────────────────┤       (FK: page_id)
│ ad_archive_id (PK)  │
│ collation_count     │
│ collation_id       │
│ page_id (FK)        │
│ is_active           │
│ has_user_reported   │
│ report_count        │
│ gated_type          │
│ is_aaa_eligible     │
│ contains_digital_created_media │
│ contains_sensitive_content │
│ start_date          │
│ end_date            │
│ start_date_formatted│
│ end_date_formatted  │
│ total_active_time   │
│ reach_estimate      │
│ currency            │
│ spend               │
│ ad_id               │
│ state_media_run_label │
│ hide_data_status    │
│ is_violating_eu_siep │
│ fev_info            │
│ verified_voice_context │
│ url                 │
│ ad_library_url      │
│ position            │
│ ads_count           │
│ total               │
│ raw_json (JSONB)    │
└─────────┬───────────┘
          │
    ┌─────┴─────────┬───────────────┬────────────┐
    ▼               ▼               ▼            ▼
┌──────────┐ ┌──────────┐   ┌────────────┐ ┌─────────────┐
│ad_snapshots│ │ ad_cards │   │ad_creatives│ │eu_targeting │
├──────────┤ ├──────────┤   ├────────────┤ ├─────────────┤
│id (PK)   │ │id (PK)   │   │id (PK)     │ │id (PK)      │
│ad_arch(FK)│ │ad_arch(FK)│  │card_id(FK) │ │ad_arch(FK)  │
│body_text │ │card_index│   │ad_archive_id│ │targets_eu   │
│cta_type  │ │title     │   │type        │ │eu_total_reach│
│display_format│ │body    │   │original_url│ │gender_audience│
│link_url  │ │cta_text  │   │local_path  │ │age_min      │
│link_desc │ │caption   │   │downloaded_at│ │age_max      │
│title     │ │link_url  │   │file_size   │ │has_violating_payer│
│caption   │ │link_desc │   │mime_type   │ │is_ad_taken_down │
│byline    │ │video_hd  │   └────────────┘ └──────┬──────┘
│disclaimer│ │video_sd  │                        │
│is_reshared│ │image_urls│          ┌────────────┼────────────┐
│page_cats │ │image_crops│          ▼            ▼            ▼
└──────────┘ └───────────┘   ┌───────────┐ ┌────────────┐ ┌────────────────┐
                              │eu_payer_  │ │eu_location │ │reach_breakdown │
                              │beneficiary│ │_audience   │ ├────────────────┤
                              ├───────────┤ ├────────────┤ │id (PK)         │
                              │id (PK)    │ │id (PK)     │ │eu_targeting_id │
                              │eu_tgt(FK) │ │eu_tgt(FK)  │ │country (CHAR2) │
                              │payer      │ │name        │ │age_range       │
                              │beneficiary│ │type        │ │male/female/unkn│
                              └───────────┘ │excluded    │ │total           │
                                           │num_obfuscated│ └────────────────┘
                                           └────────────┘

┌─────────────────────┐
│    tiktok_ads        │
├─────────────────────┤
│ ad_id (PK)          │
│ advertiser_name     │
│ ad_preview_url      │
│ ad_preview_local_path│
│ first_shown_date    │
│ first_shown_timestamp│
│ last_shown_date     │
│ last_shown_timestamp │
│ ad_audience         │
│ ad_type             │
│ audit_status        │
│ spent               │
│ impression          │
│ sponsor             │
│ target_audience_size│
│ ad_detail_url       │
│ raw_json (JSONB)    │
└────────┬────────────┘
         │
    ┌────┴────────────┐
    ▼                 ▼
┌────────────┐  ┌─────────────┐
│tiktok_ad_  │  │tiktok_ad_    │
│media       │  │targeting_    │
├────────────┤  │regions       │
│id (PK)     │  ├─────────────┤
│ad_id (FK)  │  │id (PK)       │
│media_index │  │ad_id (FK)    │
│media_type  │  │region        │
│original_url│  │impressions_range│
│local_path  │  └─────────────┘
│file_size   │
│mime_type   │
└────────────┘
```

---

## Tables de Jointure (Many-to-Many)

| Table | Description |
|-------|-------------|
| `ad_publisher_platforms` | ads → plateformes (facebook, instagram, etc.) |
| `ad_categories` | ads → catégories de contenu |
| `violation_types` | ads → types de violations |
| `targeted_countries` | ads → codes pays ciblés |
| `ad_extra_content` | ads → liens, textes, images, vidéos additionnels |
| `tiktok_ad_targeting_age` | tiktok_ads → tranches d'âge par région |
| `tiktok_ad_targeting_gender` | tiktok_ads → genre par région |
| `tiktok_ad_details_extra` | tiktok_ads → paires key/value additionnelles |

---

## Vues SQL

### unified_ads (Vue combinée Facebook + TikTok)

```sql
CREATE OR REPLACE VIEW unified_ads AS
SELECT 
    ad_archive_id AS id,
    'facebook' AS source,
    ad_archive_id AS source_ad_id,
    a.page_name AS advertiser_name,
    start_date_formatted AS first_seen,
    end_date_formatted AS last_seen,
    is_active,
    (SELECT jsonb_agg(platform) FROM ad_publisher_platforms 
     WHERE ad_archive_id = ads.ad_archive_id) AS platform_list,
    reach_estimate,
    spend,
    NULL AS preview_local_path,
    ad_library_url AS detail_url,
    CURRENT_TIMESTAMP AS created_at
FROM ads
LEFT JOIN advertisers a ON ads.page_id = a.page_id

UNION ALL

SELECT 
    ad_id AS id,
    'tiktok' AS source,
    ad_id AS source_ad_id,
    advertiser_name,
    first_shown_date AS first_seen,
    last_shown_date AS last_seen,
    NULL AS is_active,
    '["tiktok"]'::jsonb AS platform_list,
    ad_audience AS reach_estimate,
    spent AS spend,
    ad_preview_local_path AS preview_local_path,
    ad_detail_url AS detail_url,
    CURRENT_TIMESTAMP AS created_at
FROM tiktok_ads;
```

| Champ | Type | Source Facebook | Source TikTok |
|-------|------|-----------------|---------------|
| id | VARCHAR | ad_archive_id | ad_id |
| source | TEXT | 'facebook' | 'tiktok' |
| source_ad_id | VARCHAR | ad_archive_id | ad_id |
| advertiser_name | TEXT | page_name | advertiser_name |
| first_seen | TEXT | start_date_formatted | first_shown_date |
| last_seen | TEXT | end_date_formatted | last_shown_date |
| is_active | BOOLEAN | is_active | NULL |
| platform_list | JSONB | platforms | ["tiktok"] |
| reach_estimate | TEXT | reach_estimate | ad_audience |
| spend | TEXT | spend | spent |
| preview_local_path | TEXT | NULL | ad_preview_local_path |
| detail_url | TEXT | ad_library_url | ad_detail_url |
| created_at | TIMESTAMP | CURRENT_TIMESTAMP | CURRENT_TIMESTAMP |

---

## Tables Additionnelles

### Google Ads

| Table | Description |
|-------|-------------|
| `google_ads` | Ads Google (ad_id, search_id, advertiser_id, creative_id, format) |
| `google_ad_images` | Images des ads Google |

### searches

| Table | Description |
|-------|-------------|
| `searches` | Historique des recherches (search_term, counts par plateforme, timestamps) |

---

## Digital Product Intelligence (Etsy, Amazon, Classification)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    product_opportunities                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│ id (PK)              │ opportunity_id (UNIQUE)  │ product_name              │
│ product_category     │ product_description      │ price_text / price_amount │
│ advertiser_page_id   │ advertiser_name          │ advertiser_platform       │
│ advertiser_page_url  │ scaling_score            │ scaling_tier              │
│ active_days          │ ad_count                 │ is_scaling                │
│ landing_page_url     │ landing_page_scraped     │ landing_page_score        │
│ status               │ priority                  │ first_detected_at          │
│ last_updated_at      │ notes                    │                            │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         │ (1:N)
         ▼
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│         landing_pages            │     │    opportunity_creatives        │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│ id (PK)                         │     │ id (PK)                        │
│ opportunity_id (FK)             │     │ opportunity_id (FK)            │
│ url (UNIQUE)                    │     │ source_ad_archive_id           │
│ domain                          │     │ source_tiktok_ad_id            │
│ hero_headline                   │     │ platform                       │
│ main_offer                      │     │ creative_type (image/video)    │
│ price_text / price_amount       │     │ original_url                   │
│ currency                        │     │ local_path                      │
│ cta_text / cta_url             │     │ downloaded                      │
│ checkout_type (stripe/gumroad)  │     │ ad_first_seen / ad_last_seen   │
│ checkout_domain                │     │ created_at                      │
│ technology_stack (TEXT[])       │     └─────────────────────────────────┘
│ trust_signals (TEXT[])          │
│ full_text_content               │
│ html_content                    │
│ screenshot_path                 │
│ scraped_at                      │
└─────────────────────────────────┘

┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│ digital_product_classification   │     │      advertiser_tracking        │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│ id (PK)                         │     │ id (PK)                        │
│ ad_archive_id (Facebook)        │     │ page_id                        │
│ tiktok_ad_id                    │     │ page_name                      │
│ classification_type             │     │ platform (facebook/tiktok/goog)│
│ confidence_score (DECIMAL)      │     │ ad_count                       │
│ matched_keywords (TEXT[])       │     │ first_seen_at                  │
│ url_domain                      │     │ last_seen_at                    │
│ is_digital_product              │     │ active_days                    │
│ product_category                │     │ total_spend_estimate           │
│ product_name                    │     │ is_scaling                     │
│ raw_classification (JSONB)      │     │ scaling_score                  │
│ classified_at                   │     │ scaling_tier (low/med/high)    │
│                                 │     │ last_calculated_at             │
└─────────────────────────────────┘     └─────────────────────────────────┘

┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│          etsy_products           │     │       amazon_products           │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│ id (PK)                         │     │ id (PK)                        │
│ listing_id (UNIQUE)             │     │ asin (UNIQUE)                  │
│ title                           │     │ title                           │
│ price / currency                │     │ brand                           │
│ price_amount (DECIMAL)          │     │ stars / reviews_count           │
│ shop_name / shop_url            │     │ price / price_amount            │
│ rating (DECIMAL)                │     │ thumbnail                       │
│ review_count                    │     │ category                        │
│ url (UNIQUE)                    │     │ url                             │
│ search_keyword                  │     │ search_keyword                  │
│ first_seen_at                   │     │ first_seen_at                   │
│ last_updated_at                 │     │ last_updated_at                 │
│ raw_json (JSONB)                │     │ raw_json (JSONB)                │
└─────────────────────────────────┘     └─────────────────────────────────┘
```

---

### Table: digital_product_classification

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| ad_archive_id | VARCHAR(255) | Facebook ad (mutually exclusive avec tiktok_ad_id) |
| tiktok_ad_id | VARCHAR(255) | TikTok ad (mutually exclusive) |
| classification_type | VARCHAR(50) | 'digital', 'physical', 'service', 'unknown' |
| confidence_score | DECIMAL(3,2) | 0.00 à 1.00 |
| matched_keywords | TEXT[] | Mots-clésMatched |
| url_domain | TEXT | Domaine de la landing page |
| is_digital_product | BOOLEAN | Flag digital product |
| product_category | VARCHAR(100) | 'ebook', 'template', 'course', 'saas', 'tool', 'plugin' |
| product_name | TEXT | Nom inféré du produit |
| raw_classification | JSONB | Données raw classification |
| classified_at | TIMESTAMP | Date classification |

### Table: advertiser_tracking

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| page_id | VARCHAR(255) | Référence advertisers.page_id |
| page_name | TEXT | Nom de la page |
| platform | VARCHAR(50) | 'facebook', 'tiktok', 'google' |
| ad_count | INTEGER | Nombre de ads actives distinctes |
| first_seen_at | TIMESTAMP | Première détection |
| last_seen_at | TIMESTAMP | Dernière détection |
| active_days | INTEGER | Jours entre first et last |
| total_spend_estimate | TEXT | Estimation spend total |
| is_scaling | BOOLEAN | TRUE si 3+ ads actives 7+ jours |
| scaling_score | INTEGER | ad_count * active_days |
| scaling_tier | VARCHAR(20) | 'low' (<14), 'medium' (14-30), 'high' (>30) |
| last_calculated_at | TIMESTAMP | Dernier calcul |

### Table: product_opportunities

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| opportunity_id | VARCHAR(100) UNIQUE | Ex: 'FB_prodigital_2024_001' |
| product_name | TEXT | Nom du produit |
| product_category | VARCHAR(100) | Catégorie produit |
| product_description | TEXT | Description |
| price_text | TEXT | ex: "$47" ou "€29" |
| price_amount | DECIMAL(10,2) | Montant numérique |
| advertiser_page_id | VARCHAR(255) | ID page annonceur |
| advertiser_name | TEXT | Nom annonceur |
| advertiser_platform | VARCHAR(50) | Platforme source |
| advertiser_page_url | TEXT | URL page annonceur |
| scaling_score | INTEGER | Score de scalabilité |
| scaling_tier | VARCHAR(20) | low/medium/high |
| active_days | INTEGER | Jours actifs |
| ad_count | INTEGER | Nombre de ads |
| is_scaling | BOOLEAN | Flag scaling |
| landing_page_url | TEXT | URL landing page |
| landing_page_scraped | BOOLEAN | Flag scrapé |
| landing_page_score | DECIMAL(3,2) | Score landing page |
| status | VARCHAR(50) | fresh_lead, analyzing, validated, duplicated, archived |
| priority | INTEGER | 1=highest, 5=lowest |
| first_detected_at | TIMESTAMP | Première détection |
| last_updated_at | TIMESTAMP | Dernière mise à jour |
| notes | TEXT | Notes additionnelles |

### Table: landing_pages

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| opportunity_id | VARCHAR(100) FK | Référence product_opportunities |
| url | TEXT UNIQUE | URL unique |
| domain | TEXT | Domaine |
| hero_headline | TEXT | Titre principal |
| hero_subheadline | TEXT | Sous-titre |
| main_offer | TEXT | Offre principale |
| price_text | TEXT | Texte prix |
| price_amount | DECIMAL(10,2) | Montant |
| currency | VARCHAR(10) | Devise |
| cta_text | TEXT | Texte call-to-action |
| cta_url | TEXT | URL call-to-action |
| checkout_type | VARCHAR(50) | stripe, gumroad, paddle, woocommerce, shopify |
| checkout_domain | VARCHAR(255) | Domaine checkout |
| technology_stack | TEXT[] | Technologies détectées |
| trust_signals | TEXT[] | 'money-back guarantee', 'ssl', 'testimonials' |
| full_text_content | TEXT | Contenu texte complet |
| html_content | TEXT | Contenu HTML |
| screenshot_path | TEXT | Chemin screenshot |
| scraped_at | TIMESTAMP | Date scrape |
| scrape_error | TEXT | Erreur éventuelle |

### Table: opportunity_creatives

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| opportunity_id | VARCHAR(100) FK | Référence product_opportunities |
| source_ad_archive_id | VARCHAR(255) | Source Facebook |
| source_tiktok_ad_id | VARCHAR(255) | Source TikTok |
| platform | VARCHAR(50) | Platforme source |
| creative_type | VARCHAR(50) | 'image' ou 'video' |
| original_url | TEXT | URL originale |
| local_path | TEXT | Chemin local |
| downloaded | BOOLEAN | Flag téléchargé |
| ad_first_seen | DATE | Première vue de la ad |
| ad_last_seen | DATE | Dernière vue de la ad |
| created_at | TIMESTAMP | Date création |

### Table: etsy_products

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| listing_id | VARCHAR(255) UNIQUE | ID listing Etsy |
| title | TEXT | Titre du produit |
| price | TEXT | Prix texte |
| currency | VARCHAR(10) | Devise |
| price_amount | DECIMAL(10,2) | Montant numérique |
| shop_name | TEXT | Nom de la boutique |
| shop_url | TEXT | URL boutique |
| rating | DECIMAL(2,1) | Note (ex: 4.8) |
| review_count | INTEGER | Nombre d'avis |
| url | TEXT UNIQUE | URL produit |
| search_keyword | TEXT | Mot-clé recherchée |
| first_seen_at | TIMESTAMP | Première détection |
| last_updated_at | TIMESTAMP | Dernière mise à jour |
| raw_json | JSONB | Données raw |

**Indexes:** `idx_etsy_shop`, `idx_etsy_rating`, `idx_etsy_reviews`

### Table: amazon_products

| Champ | Type | Description |
|-------|------|-------------|
| id | SERIAL PK | Auto-incrément |
| asin | VARCHAR(255) UNIQUE | ASIN Amazon |
| title | TEXT | Titre du produit |
| brand | TEXT | Marque |
| stars | DECIMAL(2,1) | Note (ex: 4.5) |
| reviews_count | INTEGER | Nombre d'avis |
| price | TEXT | Prix texte |
| price_amount | DECIMAL(10,2) | Montant numérique |
| thumbnail | TEXT | URL miniature |
| category | TEXT | Catégorie |
| url | TEXT UNIQUE | URL produit |
| search_keyword | TEXT | Mot-clé recherchée |
| first_seen_at | TIMESTAMP | Première détection |
| last_updated_at | TIMESTAMP | Dernière mise à jour |
| raw_json | JSONB | Données raw |

---

## Endpoints API suggérés pour le Front

### 1. Liste des ads (unifié)
```http
GET /api/ads?source=facebook&page=1&limit=20
```

### 2. Détail d'un advertiser
```http
GET /api/advertisers/{page_id}
```

### 3. Détail d'une ad Facebook
```http
GET /api/ads/{ad_archive_id}
```

### 4. Détail d'une ad TikTok
```http
GET /api/tiktok-ads/{ad_id}
```

### 5. Statistiques de collecte
```http
GET /api/crawl-jobs?source=facebook
```

---

## Types de données principaux

| Type PostgreSQL | Usage |
|-----------------|-------|
| SERIAL PRIMARY KEY | Auto-incrément ID |
| VARCHAR(255) | IDs, noms courts |
| TEXT | Contenus longs (body, description) |
| JSONB | Données raw/structurées |
| BOOLEAN | Flags (is_active, etc.) |
| TIMESTAMP | Dates de collecte |
| BIGINT | Tailles de fichiers |

---

## Relations clés

```
advertisers (1) ────── (N) ads
ads (1) ────── (N) ad_snapshots
ads (1) ────── (N) ad_cards
ads (1) ────── (N) eu_targeting ── (1:N) reach_breakdown
ads (1) ────── (N) ad_categories, violation_types, targeted_countries
tiktok_ads (1) ────── (N) tiktok_ad_media
tiktok_ads (1) ────── (N) tiktok_ad_targeting_*
```