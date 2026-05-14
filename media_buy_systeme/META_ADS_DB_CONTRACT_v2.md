# META Ads Tool — DB Contract v2
*Launch Engine · Neon Postgres · Updated: 2026-05-12*

---

## Connection

```
Database: launch-engine (Neon Postgres)
Env var:  LAUNCH_ENGINE_DATABASE_URL
```

---

## Campaign Naming Convention

```
[sales_title] | [niche] | Test
Example: "The LuxeLoop Tote | Fashion | Test"
```

Use `products.sales_title` (human-validated name) + `products.niche`.

---

## Trigger — What to poll

```sql
SELECT * FROM products
WHERE status = 'approved'
ORDER BY updated_at ASC;
```

Poll every 60–120s. Set `status = 'testing'` immediately on pickup to avoid double-processing.

---

## Products Table — What you READ

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Product identifier |
| `name` | TEXT | Raw product name |
| `sales_title` | TEXT | ✅ Use as campaign/ad headline |
| `niche` | TEXT | Audience targeting context |
| `source` | TEXT | `'scraper'` or `'ai_freewill'` |
| `lp_url` | TEXT | Landing page destination URL |
| `stripe_url` | TEXT | Stripe payment link |
| `ref_image_url` | TEXT | Main visual (Cloudflare R2) |
| `brand_color_primary` | TEXT | Hex e.g. `#1a1a2e` |
| `brand_color_secondary` | TEXT | Hex |
| `brand_color_accent` | TEXT | Hex |

---

## Products Table — What you WRITE

```sql
-- On campaign launch
UPDATE products SET
  meta_campaign_id      = $1,
  meta_adset_id         = $2,
  meta_ad_account_id    = $3,
  meta_ad_account_name  = $4,
  meta_campaign_status  = 'active',
  testing_started_at    = NOW(),
  testing_daily_budget  = $5,
  status                = 'testing',
  updated_at            = NOW()
WHERE id = $6;

-- Daily metrics sync (campaign-level snapshot)
UPDATE products SET
  meta_amount_spent     = $1,
  meta_purchases        = $2,
  meta_conversion_value = $3,
  meta_cpm              = $4,
  meta_ctr              = $5,
  meta_cpc              = $6,
  meta_atc              = $7,
  meta_ic               = $8,
  meta_roas             = $9,
  updated_at            = NOW()
WHERE id = $10;
```

| Column | Type | Description |
|--------|------|-------------|
| `meta_campaign_id` | TEXT | META Campaign ID |
| `meta_adset_id` | TEXT | Main adset ID |
| `meta_ad_account_id` | TEXT | Ad account ID |
| `meta_ad_account_name` | TEXT | Ad account display name |
| `meta_campaign_status` | TEXT | `active` · `paused` · `completed` |
| `testing_started_at` | TIMESTAMPTZ | Campaign launch time |
| `testing_daily_budget` | NUMERIC | Daily budget in € |
| `meta_amount_spent` | NUMERIC | Total spend |
| `meta_purchases` | INTEGER | Purchase conversions |
| `meta_conversion_value` | NUMERIC | Total revenue from ads |
| `meta_cpm` | NUMERIC | Cost per 1000 impressions |
| `meta_ctr` | NUMERIC | Click-through rate % |
| `meta_cpc` | NUMERIC | Cost per click |
| `meta_atc` | INTEGER | Add to cart events |
| `meta_ic` | INTEGER | Initiate checkout events |
| `meta_roas` | NUMERIC | Return on ad spend |

---

## Creatives Table — What you READ

```sql
SELECT id, url, type, format, status
FROM creatives
WHERE product_id = $1
  AND status = 'approved'
ORDER BY created_at ASC;
```

| Column | Type | Values |
|--------|------|--------|
| `id` | UUID | Creative identifier |
| `url` | TEXT | Cloudflare R2 URL |
| `type` | TEXT | `'image'` · `'video'` |
| `format` | TEXT | `'1:1'` · `'4:5'` · `'9:16'` · `'16:9'` |

---

## Creatives Table — What you WRITE

```sql
-- Link META ad ID back to creative
UPDATE creatives SET
  meta_ad_id = $1
WHERE id = $2;
```

---

## meta_adsets Table — What you WRITE

One row per adset. Upsert on `adset_id`.

```sql
INSERT INTO meta_adsets (
  product_id, campaign_id, adset_id, adset_name, status,
  daily_budget, amount_spent, purchases, conversion_value,
  cpm, ctr, cpc, atc, ic, roas, updated_at
)
VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,NOW())
ON CONFLICT (adset_id) DO UPDATE SET
  status            = EXCLUDED.status,
  daily_budget      = EXCLUDED.daily_budget,
  amount_spent      = EXCLUDED.amount_spent,
  purchases         = EXCLUDED.purchases,
  conversion_value  = EXCLUDED.conversion_value,
  cpm               = EXCLUDED.cpm,
  ctr               = EXCLUDED.ctr,
  cpc               = EXCLUDED.cpc,
  atc               = EXCLUDED.atc,
  ic                = EXCLUDED.ic,
  roas              = EXCLUDED.roas,
  updated_at        = NOW();
```

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | UUID | FK → products.id |
| `campaign_id` | TEXT | META Campaign ID |
| `adset_id` | TEXT | UNIQUE — META Adset ID |
| `adset_name` | TEXT | Adset display name |
| `status` | TEXT | `active` · `paused` · `completed` |
| `daily_budget` | NUMERIC | Adset daily budget |
| `amount_spent` | NUMERIC | Adset spend |
| `purchases` | INTEGER | Conversions |
| `conversion_value` | NUMERIC | Revenue |
| `cpm` | NUMERIC | CPM |
| `ctr` | NUMERIC | CTR % |
| `cpc` | NUMERIC | CPC |
| `atc` | INTEGER | Add to cart |
| `ic` | INTEGER | Initiate checkout |
| `roas` | NUMERIC | ROAS |

---

## Events Table — What you LOG

```sql
INSERT INTO events (product_id, event_type, payload)
VALUES ($1, $2, $3::jsonb);
```

> ⚠️ `product_id` is **UUID** type.

| event_type | payload keys |
|------------|-------------|
| `meta_campaign_created` | `campaign_id, adset_id, budget, ad_account_id, ad_account_name` |
| `meta_ads_launched` | `campaign_id, ad_count, product_name` |
| `meta_ad_created` | `ad_id, creative_id, creative_url, campaign_id` |
| `meta_campaign_paused` | `campaign_id, reason` |
| `meta_result_updated` | `spend, purchases, conversion_value, cpm, ctr, cpc, atc, ic, roas` |

---

## Status Flow

```
approved            ← poll here
    ↓ set status = 'testing' on pickup
testing             ← update metrics daily
    ↓
completed           ← meta_campaign_status = 'completed'
```

---

## Settings — Activation flag

```sql
SELECT value FROM settings WHERE key = 'meta_tool_active';
-- 'true' = go | 'false' = pause (controlled from dashboard)
```

---

## Quick Start Checklist

- [ ] Connect to `LAUNCH_ENGINE_DATABASE_URL`
- [ ] Poll `WHERE status = 'approved'` every 60–120s
- [ ] Set `status = 'testing'` immediately on pickup
- [ ] Name campaign: `[sales_title] | [niche] | Test`
- [ ] Fetch approved creatives from `creatives` table
- [ ] Write `meta_campaign_id`, `meta_ad_account_name`, `testing_daily_budget` to products
- [ ] Upsert adset metrics into `meta_adsets` table daily
- [ ] Update campaign-level metric columns on `products` daily
- [ ] Log events: `meta_campaign_created` → `meta_ads_launched` → `meta_result_updated` (daily)
