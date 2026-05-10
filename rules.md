# SCRAPER RULES v2 — AI-First Winner Detection

# Le scraper collecte. L'AI analyse. L'humain valide

---

## PRINCIPE FONDAMENTAL

Le scoring par points fixes ne marche pas. Les variables peuvent être trompeuses (catégorie mal classée, titre ambigu, faux positifs).

**Le bon système :**

1. Le scraper collecte la data brute (titre, reviews, prix, catégorie, description, images)
2. L'AI (Claude) analyse CHAQUE produit et produit un verdict structuré
3. L'humain valide le top 10-20

L'AI ne compte pas des points. Elle COMPREND le produit.

---

## SECTION 1 — CE QUE LE SCRAPER COLLECTE (par plateforme)

Le scraper ne filtre RIEN. Il collecte tout et passe à l'AI.

### Amazon

```
title, asin, brand, stars, reviewsCount, thumbnailImage, 
breadCrumbs, description, price.value, price.currency, url
```

### Etsy

```
title, price, currency, shopName, rating, reviewCount, url
```

### Facebook Ad Library

```
ad_archive_id, snapshot.page_name, snapshot.cards[].body,
snapshot.cards[].title, snapshot.cards[].link_url,
snapshot.cards[].cta_text, snapshot.cards[].original_image_url,
snapshot.cards[].video_hd_url, collation_count,
eu_total_reach (EU only), age_country_gender_reach_breakdown
```

### TikTok

```
AD ID, Advertiser Name, Ad Dates (FirstShown, LastShown),
Ad Audience, Ad Details (Estimated Audience, Impression, Spent),
Ad Targeting (regions, age, gender), Ad Media, Ad Target Audience Size
```

---

## SECTION 2 — CE QUE L'AI ANALYSE

Pour chaque produit scrapé, l'AI reçoit la data brute et doit répondre à ces questions :

### 2.1 Compréhension du produit

```
QUESTION 1: Qu'est-ce que ce produit RÉELLEMENT ?
- Analyser le titre + description + catégorie + image ensemble
- Ne PAS se fier à la catégorie seule (elle peut être fausse)
- Exemples : 
  → "Higher Learning" dans "Movies & TV > Drama" = c'est un FILM, pas de l'éducation
  → "Scholastic Flash Cards" dans "Reading & Phonics" = c'est des FLASHCARDS éducatives
  → "Preschool Prep DVD" dans "DVD" = c'est du CONTENU ÉDUCATIF en format vidéo

QUESTION 2: Ce produit prouve-t-il une DEMANDE pour quelque chose qu'on peut vendre en digital ?
- Le nombre de reviews = proxy du nombre de ventes. C'est LE signal le plus important.
- Un produit 3 étoiles avec 50K reviews = demande massive. La qualité on s'en fout, on fera mieux.
- Un produit 5 étoiles avec 12 reviews = pas de demande prouvée.
- La note (stars) N'EST PAS un facteur de scoring. Seul le volume compte.

QUESTION 3: Quel est le CONCEPT sous-jacent qu'on peut repackager en digital ?
- Ne pas copier le produit. Copier le BESOIN qu'il résout.
- Exemples :
  → Flash cards physiques → printable PDF + audio app
  → Cahier d'écriture → printable worksheets bundle
  → DVD éducatif → digital learning pack avec vidéos AI
  → Poster mural → printable high-res PDF poster set
  → Crème anti-cernes → protocol anti-cernes (tapping, massage, routine)
  → Knee brace → knee strengthening program PDF + videos
```

### 2.2 Verdict de l'AI

Pour chaque produit, l'AI produit ce JSON :

```json
{
  "product_name": "titre original",
  "source_platform": "amazon",
  "source_url": "url",
  "source_price": 3.07,
  "reviews_count": 33527,
  
  "ai_analysis": {
    "what_is_it": "Physical flashcards for teaching sight words to children aged 3-7. Used by parents and teachers for early reading skills.",
    "is_relevant": true,
    "relevance_reason": "Proves massive demand for sight words learning material. 33K reviews = estimated 500K-1M+ sales. The concept (learn sight words) is easily digitizable.",
    "skip_reason": null,
    
    "digital_repackage_idea": "Ultimate Sight Words Digital Pack — 220 printable flashcards in PDF, audio pronunciation MP3 for each word (AI text-to-speech), interactive progress tracker, parent guide with teaching tips.",
    "our_suggested_price": "$19",
    "estimated_margin": "95%+",
    "production_effort": "LOW — Canva for flashcards, ElevenLabs/TTS for audio, PDF for tracker. 1-2 days max.",
    
    "demand_level": "MASSIVE",
    "demand_evidence": "33,527 reviews at 4.8 stars. Multiple competing products in same niche also with thousands of reviews. Category 'Reading & Phonics' is evergreen.",
    
    "competition_on_meta": null,
    "virgin_seed": null,
    
    "priority": "HIGH",
    "priority_reason": "Massive proven demand + easy to digitize + low production effort + evergreen niche",
    
    "suggested_concepts": [
      "Parents of toddlers 2-5 — 'Screen-free learning in 10 minutes/day' — unaware",
      "Homeschool parents — 'The sight words system that actually sticks' — problem_aware",
      "Gift for teacher — 'The printable pack every kindergarten teacher needs' — solution_aware"
    ],
    
    "warnings": [
      "Scholastic is a known brand — don't use their name or design style",
      "The physical product is $3 — our digital version at $19 needs to clearly justify the premium (audio, interactive, convenience)"
    ]
  }
}
```

### 2.3 Quand l'AI doit marquer SKIP

L'AI skip un produit quand :

```
- C'est un film, une série, de la musique, un jeu vidéo, de la fiction
  (même si le titre contient des mots-clés éducatifs)
- C'est un produit de marque protégée qu'on ne peut pas repackager
  (ex: un jouet Disney spécifique)
- Le concept n'est PAS convertible en digital
  (ex: un vrai outil physique sans dimension informationnelle)
- Le produit est dans une niche médicale/pharmaceutique sensible
  (risque compliance Meta)
- Il n'y a aucune evidence de demande
  (< 20 reviews, produit inconnu)
```

L'AI explique TOUJOURS pourquoi elle skip dans `skip_reason`.

---

## SECTION 3 — PROMPT SYSTÈME POUR L'AI ANALYZER

Ce prompt est donné à Claude pour analyser chaque batch de produits scrapés :

```
Tu es un expert en détection de produits winners pour une machine qui :
1. Détecte des produits qui se vendent bien (sur Amazon, Etsy, TikTok, Facebook)
2. Les repackage en produits DIGITAUX vendus $10-40
3. Crée des landing pages et des créatives Meta ads
4. Lance sur Meta et plante des "graines" — l'humain scale celles qui prennent

RÈGLES D'ANALYSE :

1. COMPRENDS LE PRODUIT avant de scorer. Ne te fie pas à la catégorie — elle peut être fausse. Lis le titre + description + catégorie ensemble pour comprendre ce que c'est RÉELLEMENT.

2. LE NOMBRE DE REVIEWS EST LE SEUL VRAI SIGNAL. C'est le proxy du nombre de ventes. Plus il y a de reviews, plus la demande est prouvée. La note (étoiles) n'est PAS un facteur — un produit 3 étoiles avec 50K reviews prouve une demande massive. On fera mieux.

3. DEMANDE-TOI : "quel BESOIN ce produit résout-il ?" Puis : "ce besoin peut-il être résolu par un produit digital ?" Si oui → c'est un winner potentiel. Si non → skip.

4. LE PRIX SOURCE N'EST PAS UN FILTRE. Un produit à $3 avec 33K reviews = demande massive. On le repackage en digital à $19-29. Un produit à $200 avec 33K reviews = même chose. Notre prix de vente sera toujours $10-40.

5. PROPOSE L'IDÉE DE REPACKAGE DIGITAL. Sois spécifique : quel format (PDF, app, audio, vidéo), quel contenu, quel prix, quel effort de production.

6. ÉVALUE L'EFFORT DE PRODUCTION :
   - LOW = 1-2 jours (templates, printables, PDF)
   - MEDIUM = 3-5 jours (contenu original, vidéos AI, audio)
   - HIGH = 1-2 semaines (app web, contenu complexe, multiple formats)

7. PROPOSE 2-3 CONCEPTS D'ADS. Pour chaque : persona + angle + awareness level. C'est l'input pour le concept builder.

8. SIGNALE LES WARNINGS : marques protégées, niches sensibles, compétition probable, justification de prix nécessaire.

9. SKIP les faux positifs : films, musique, jeux vidéo, fiction, produits non-convertibles. Explique pourquoi dans skip_reason.

Pour chaque produit, réponds en JSON structuré (voir format ci-dessus).
```

---

## SECTION 4 — RÈGLES SPÉCIFIQUES PAR PLATEFORME

### 4.1 Amazon — ce que l'AI doit regarder en plus

- `reviewsCount` est le signal #1. Classement : < 100 = pas de demande, 100-1000 = niche, 1000-10000 = fort, 10000+ = massif
- `breadCrumbs` donne le contexte catégorie mais l'AI doit VÉRIFIER avec le titre/description
- `brand` non-null = produit de marque. Warning : ne pas copier leur design/nom
- `price.value` = info seulement. Utile pour calculer le gap de prix (si physique coûte $25 et notre digital est à $19, facile à justifier)
- `description` peut être null — dans ce cas l'AI se base sur titre + catégorie + image

### 4.2 Etsy — ce que l'AI doit regarder en plus

- `reviewCount` × 25-50 = ventes estimées (produits digitaux)
- `title` est souvent keyword-stuffé sur Etsy — l'AI doit extraire le VRAI produit
- Le fait que ce soit sur Etsy = déjà probablement du digital/printable. Bon signal.
- Cross-check Meta Ad Library : si personne ne fait de pub Meta dessus → VIRGIN SEED (meilleure graine)

### 4.3 Facebook Ad Library — ce que l'AI doit regarder en plus

- `snapshot.cards[].body` = le texte de l'ad. L'AI analyse le messaging et l'angle
- `snapshot.cards[].link_url` = la LP du concurrent. L'AI évalue si elle est battable
- `snapshot.cards[].video_hd_url === null` → c'est une image ad (notre priorité)
- `eu_total_reach` = impressions (EU only). Proxy de spend
- Compter les ads uniques par même domaine/LP = indicateur de scaling
- `cta_text` = "Shop Now" = commerce (bon signal)
- Nombre de jours entre `first_detection` et `today` = durée de vie de l'ad

### 4.4 TikTok — ce que l'AI doit regarder en plus

- `Ad Audience` string → parser en numérique pour estimer le reach
- `FirstShown` vs `LastShown` = jours actifs. Si encore actif + 14+ jours = fort signal
- `Ad Targeting.regions` = pays Tier 1 (US/UK/CA/AU) = prioritaire
- `Ad Target Audience Size` large = l'annonceur target broad (comme nous)
- Grouper par `Advertiser Name` pour compter les ads du même annonceur

---

## SECTION 5 — MOTS-CLÉS DE RECHERCHE

### 5.1 Mots-clés pour CHERCHER des produits (input du scraper)

**Produits AI personnalisés :**

```
AI baby face generator, AI baby predictor, future baby face,
personalized AI song, custom AI song, AI portrait, AI headshot generator,
AI pet portrait, AI family portrait, AI avatar pack, AI voice clone,
AI children's book, AI bedtime story personalized, restore old photo AI,
colorize old photo AI, AI cartoon portrait, AI superhero portrait,
AI action figure generator, turn photo into painting AI
```

**Templates / Printables / Presets :**

```
digital planner, budget spreadsheet template, Canva template pack,
social media template, Notion template, Lightroom preset pack,
resume template, content calendar template, wedding planner printable,
meal plan template, fitness planner digital, habit tracker printable,
self care journal, recipe book template, cleaning schedule printable,
homeschool planner, teacher printable
```

**Education / Learning :**

```
ABC learning, alphabet flashcards, phonics worksheets, sight words printable,
math worksheets kids, nursing flashcards, NCLEX study guide,
language learning flashcards, handwriting practice sheets,
toddler activity printable, preschool curriculum, homeschool worksheets,
anatomy flashcards, multiplication table printable
```

**Ebooks / Guides / Protocoles :**

```
ebook digital download, how to guide PDF, mini course,
protocol PDF, challenge 7 day, challenge 30 day,
weight loss guide, skincare routine guide, fitness program digital,
meditation guide audio, astrology reading personalized
```

**Audio / Sound :**

```
personalized song, custom lullaby, meditation audio, sleep sounds,
affirmation audio, guided visualization, hypnosis audio,
frequency healing, sound bath recording
```

**Produits physiques convertibles en digital :**

```
anti cerne, dark circles treatment, acne treatment, hair growth,
teeth whitening, posture corrector, back pain relief, knee brace,
sleep aid, detox tea, gut health, face yoga, jaw exerciser,
cellulite cream, stretch mark, snoring device, foot pain insole,
wrist brace carpal tunnel, neck pain pillow, migraine relief,
anxiety supplement, focus supplement, collagen supplement,
hormone balance, menopause supplement, weight loss supplement
```

### 5.2 Mots-clés pour SCORER les résultats (analyse des descriptions/commentaires)

Ces mots-clés ne sont PAS pour chercher. Ils sont pour enrichir le scoring de résultats déjà scrapés :

**Signaux de produit digital dans le titre/description :**

```
generate yours, create yours, instant download, instant access,
digital download, instant delivery, personalized for you,
custom made, delivered to your email, download now, printable,
PDF, template, digital, interactive
```

**Signaux d'intention d'achat dans les commentaires (si scrapables) :**

```
I need this, take my money, where can I get this, link please,
this is amazing, best gift ever, game changer, obsessed with this
```

---

## SECTION 6 — FRÉQUENCE ET PIPELINE

### Fréquence de scraping

| Plateforme | Fréquence |
|-----------|-----------|
| TikTok | Toutes les 24h |
| Facebook Ad Library | Toutes les 48h |
| Etsy | Toutes les 72h |
| Amazon | Toutes les 72h |

### Pipeline

```
SCRAPER → collecte data brute par mots-clés (section 5.1)
    ↓
AI ANALYZER → Claude analyse chaque produit (prompt section 3)
    ↓
FILTRE → L'AI classe : SKIP / PASS / HIGH PRIORITY
    ↓
CROSS-CHECK → Pour les HIGH PRIORITY Etsy/Amazon : vérifier Meta Ad Library
    ↓
OUTPUT → Dashboard avec top 10-20 winners, triés par priorité
    ↓
HUMAIN → Valide, choisit, lance dans la machine
```

### Seuils à ajuster

- Si le scraper retourne < 5 résultats par run → élargir les mots-clés
- Si le scraper retourne > 100 résultats par run → l'AI filtre, pas le scraper
- L'objectif : 10-30 produits analysés par l'AI, 5-10 marqués PASS/HIGH PRIORITY pour le review humain

---

## SECTION 7 — NOTES POUR LE DEV

### MVP (phase 1)

1. Scraper les 4 plateformes avec les mots-clés de la section 5.1
2. Passer chaque batch à Claude avec le prompt de la section 3
3. Stocker les résultats JSON de l'AI
4. Afficher dans un dashboard simple : nom, plateforme, reviews, priorité AI, lien
5. L'humain review et marque "validated" ou "rejected"

### Phase 2

- Cross-check Meta Ad Library automatique pour les winners Etsy/Amazon
- Scraping des commentaires pour détecter les signaux d'intention d'achat
- Détection de niche (quand 3+ produits sont dans le même espace → flag "HOT NICHE")
- Historique de scraping (tracker les nouveaux produits vs déjà vus)
- Alerte automatique quand un nouveau HIGH PRIORITY apparaît

### Phase 3

- Le concept builder reçoit directement les winners validés
- Auto-génération des concepts, hooks, scripts, image prompts
- Pipeline complet : scrape → AI analyze → human validate → concept build → LP build → creative build → Meta launch

J'ai appelé bulk_search_interests avec les mots-clés des niches. Meta renvoie les intérêts disponibles avec leur ID et leur taille d'audience globale. Par exemple "homeschooling" → ID 6003241811213, audience globale 52-61M.
Étape 2 — Estimer l'audience filtrée
J'ai appelé estimate_audience_size avec :

Les IDs d'intérêts trouvés
Les pays ciblés : US, UK, CA, AU
Le filtre langue : anglais (locales: [6])
La tranche d'âge : 25-45 ou 25-50 selon la niche

Mot clef produit digitaux

generate yours, create yours, instant download, instant access,
digital download, instant delivery, personalized for you,
custom made, delivered to your email, download now, printable,
PDF, template, digital, interactive, personalize, custom, meditation, audio, sleep sounds,
affirmation audio, guided visualization, hypnosis audio,
frequency healing, ebook digital download, how to guide PDF, mini course,
protocol, challenge, guide, routine guide,program, digital,
audio, astrology, Flashcards, printable, learning, learn, practice, PDF, ebook, e-book, workbook, planner, template, prompt, preset, meal plan,  habit tracker, journal, recipe, generator, predictor, analyse, personalized.
checklist, cheatsheet, toolkit, blueprint, roadmap, convert, clone, predict, download, access, protocol, method, bootcamp, masterclass, training, certification, assessment, quiz, test, done for you, step by step, library, plug and play
AI generated, AI powered, ai made, made with AI
Photo to
