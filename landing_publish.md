# Landing Page Hosting — Architecture complète pour l'IA

## Contexte système

Le système scrape des ads (TikTok, Facebook, Etsy, Amazon), détecte des produits gagnants, télécharge les créas et landing pages, les modifie (logo, prix, paiement), puis les publie automatiquement sur `ignuva.shop` et pousse les ads sur Meta.

**VPS IP :** `178.105.100.232`  
**Domaine :** `ignuva.shop`  
**Stack :** Docker + Traefik + Nginx  
**Pattern URL :** `https://ignuva.shop/<product_slug>`

---

## Architecture globale

```
Internet
    │
    ▼
ignuva.shop (DNS A → 178.105.100.232)
    │
    ▼
VPS : 178.105.100.232
    │
    ├── :80  → Traefik → redirect HTTPS automatique
    └── :443 → Traefik → Container Nginx
                              │
                    /usr/share/nginx/html/
                              │
                    ┌─────────┴──────────┐
                    │                    │
               produit1/           produit2/
               index.html          index.html
               assets/             assets/
```

Le dossier `landings/` sur le VPS est monté en volume partagé entre :
- Le **container Nginx** (qui sert les fichiers)
- Le **container Bot** (qui écrit les fichiers)

Aucun redémarrage n'est nécessaire pour publier une nouvelle landing. Nginx sert les fichiers statiques à la volée.

---

## Structure des fichiers sur le VPS

```
/opt/launch-engine/
├── docker-compose.yml
├── traefik/
│   ├── traefik.yml
│   └── acme.json                  ← certificats Let's Encrypt (chmod 600 obligatoire)
└── landings/                      ← volume partagé Nginx + Bot
    ├── index.html                 ← page d'accueil optionnelle
    ├── produit1/
    │   ├── index.html
    │   └── assets/
    │       ├── style.css
    │       └── hero.jpg
    ├── produit2/
    │   ├── index.html
    │   └── assets/
    └── produit_N/
        └── index.html
```

---

## Fichiers de configuration

### `/opt/launch-engine/docker-compose.yml`

```yaml
version: "3.8"

services:

  traefik:
    image: traefik:v3.0
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/traefik.yml:ro
      - ./traefik/acme.json:/acme.json
    networks:
      - web

  landings:
    image: nginx:alpine
    restart: unless-stopped
    volumes:
      - ./landings:/usr/share/nginx/html:ro
    networks:
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.landings.rule=Host(`ignuva.shop`) || Host(`www.ignuva.shop`)"
      - "traefik.http.routers.landings.entrypoints=websecure"
      - "traefik.http.routers.landings.tls.certresolver=letsencrypt"
      - "traefik.http.services.landings.loadbalancer.server.port=80"
      - "traefik.http.middlewares.www-redirect.redirectregex.regex=^https://www\\.ignuva\\.shop/(.*)"
      - "traefik.http.middlewares.www-redirect.redirectregex.replacement=https://ignuva.shop/$${1}"
      - "traefik.http.routers.landings.middlewares=www-redirect"

  # ─── Ajouter ici le service bot si il tourne dans Docker ───
  # bot:
  #   image: ton-bot-image
  #   volumes:
  #     - ./landings:/app/landings   ← même dossier que Nginx
  #   networks:
  #     - web

networks:
  web:
    external: false
```

### `/opt/launch-engine/traefik/traefik.yml`

```yaml
api:
  dashboard: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false

certificatesResolvers:
  letsencrypt:
    acme:
      email: contact@ignuva.shop      # ← email pour Let's Encrypt
      storage: /acme.json
      httpChallenge:
        entryPoint: web
```

---

## DNS à configurer

Chez le registrar du domaine `ignuva.shop`, ajouter ces deux records :

| Type | Nom | Valeur | TTL |
|------|-----|--------|-----|
| `A` | `@` | `178.105.100.232` | 300 |
| `A` | `www` | `178.105.100.232` | 300 |

TTL à 300 pour la mise en place, remonter à 3600 ensuite.  
Pas de wildcard nécessaire : tout passe par des paths (`/produit1`), pas des sous-domaines.

---

## Commandes d'initialisation (une seule fois)

```bash
# Se connecter au VPS
ssh root@178.105.100.232

# Créer la structure
mkdir -p /opt/launch-engine/traefik
mkdir -p /opt/launch-engine/landings

# Créer le fichier acme.json avec les bonnes permissions (OBLIGATOIRE sinon Traefik refuse)
touch /opt/launch-engine/traefik/acme.json
chmod 600 /opt/launch-engine/traefik/acme.json

# Ouvrir les ports firewall
ufw allow 80
ufw allow 443

# Déployer
cd /opt/launch-engine
docker compose up -d

# Vérifier que Traefik obtient le certificat Let's Encrypt
docker compose logs -f traefik
```

---

## Fonction de publication — implémentation Bot

Quand le bot a modifié une landing page et veut la publier, il appelle cette fonction.

### Python

```python
import os
import shutil
import re

LANDINGS_DIR = "/app/landings"       # chemin dans le container bot
BASE_URL = "https://ignuva.shop"

def slugify(name: str) -> str:
    """Convertit un nom de produit en slug URL-safe."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\-_]', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug

def publish_landing(
    product_name: str,
    html_content: str,
    assets_dir: str = None
) -> str:
    """
    Publie une landing page et retourne son URL publique.
    
    Args:
        product_name: ex "Nike Air Force Blue" → slug: "nike-air-force-blue"
        html_content: contenu HTML de la landing modifiée (logo, prix, paiement injectés)
        assets_dir: chemin local vers les assets (images, css, js) à copier
    
    Returns:
        URL publique: "https://ignuva.shop/nike-air-force-blue"
    """
    slug = slugify(product_name)
    output_dir = os.path.join(LANDINGS_DIR, slug)
    
    # Créer le dossier
    os.makedirs(output_dir, exist_ok=True)
    
    # Écrire le HTML
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Copier les assets si fournis
    if assets_dir and os.path.exists(assets_dir):
        assets_output = os.path.join(output_dir, "assets")
        if os.path.exists(assets_output):
            shutil.rmtree(assets_output)
        shutil.copytree(assets_dir, assets_output)
    
    public_url = f"{BASE_URL}/{slug}"
    print(f"✅ Landing publiée : {public_url}")
    return public_url

def unpublish_landing(product_slug: str) -> bool:
    """Supprime une landing page."""
    target = os.path.join(LANDINGS_DIR, product_slug)
    if os.path.exists(target):
        shutil.rmtree(target)
        print(f"🗑️  Landing supprimée : {product_slug}")
        return True
    return False

def list_published_landings() -> list[dict]:
    """Retourne la liste des landings publiées avec leurs URLs."""
    if not os.path.exists(LANDINGS_DIR):
        return []
    
    results = []
    for slug in os.listdir(LANDINGS_DIR):
        path = os.path.join(LANDINGS_DIR, slug)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "index.html")):
            results.append({
                "slug": slug,
                "url": f"{BASE_URL}/{slug}",
                "path": path
            })
    return results
```

### Node.js / TypeScript

```typescript
import fs from "fs";
import path from "path";

const LANDINGS_DIR = "/app/landings";
const BASE_URL = "https://ignuva.shop";

function slugify(name: string): string {
  return name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\-_]/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

async function publishLanding(
  productName: string,
  htmlContent: string,
  assetsDir?: string
): Promise<string> {
  const slug = slugify(productName);
  const outputDir = path.join(LANDINGS_DIR, slug);

  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, "index.html"), htmlContent, "utf-8");

  if (assetsDir && fs.existsSync(assetsDir)) {
    fs.cpSync(assetsDir, path.join(outputDir, "assets"), { recursive: true });
  }

  const publicUrl = `${BASE_URL}/${slug}`;
  console.log(`✅ Landing publiée : ${publicUrl}`);
  return publicUrl;
}
```

---

## Workflow complet — du scraping à l'ad Meta

```
1. SCRAPING
   └── Détection produit gagnant sur TikTok/Facebook/Etsy/Amazon

2. TÉLÉCHARGEMENT
   ├── creative.jpg/mp4     → Cloudflare R2 (bucket: launch-engine-creatives)
   └── landing.html + assets → local /tmp/product_raw/

3. MODIFICATION LANDING
   ├── Remplacer logo       → <img src="/assets/logo.png">
   ├── Injecter prix        → ex: <span class="price">29.99€</span>
   ├── Injecter paiement    → snippet Stripe / PayPal / autre
   └── Corriger les liens   → tous les hrefs → relatifs ou ignuva.shop

4. PUBLICATION LANDING
   ├── publish_landing("nom-produit", html_modifié, assets_dir)
   └── → URL retournée : "https://ignuva.shop/nom-produit"

5. PUSH META ADS CLI
   ├── meta ads campaign create ...
   ├── meta ads adset create ... --pixel-id $META_PIXEL_ID
   ├── meta ads creative create ... --page-id $META_PAGE_ID --image-url <R2_URL>
   │     body/title/link-url → utiliser l'URL de la landing (étape 4)
   └── meta ads ad create ...

6. ACTIVATION
   └── meta ads campaign/adset/ad update ... --status ACTIVE
```

---

## Modification HTML — patterns à implémenter

Le bot doit transformer la landing scrapée avant publication. Voici les opérations à effectuer :

```python
from bs4 import BeautifulSoup

def modify_landing(
    raw_html: str,
    logo_path: str,
    price: str,
    payment_snippet: str,
    destination_url: str
) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remplacer le logo
    for img in soup.find_all("img", {"class": lambda c: c and "logo" in c}):
        img["src"] = "/assets/logo.png"

    # 2. Remplacer le prix
    for el in soup.find_all(class_=lambda c: c and "price" in c.lower()):
        el.string = price

    # 3. Injecter le système de paiement (avant </body>)
    payment_tag = soup.new_tag("div", id="payment-block")
    payment_tag.append(BeautifulSoup(payment_snippet, "html.parser"))
    soup.body.append(payment_tag)

    # 4. Rendre tous les liens absolus → relatifs au domaine
    for a in soup.find_all("a", href=True):
        if a["href"].startswith("http") and "ignuva.shop" not in a["href"]:
            a["href"] = destination_url

    # 5. Supprimer les scripts de tracking tiers
    for script in soup.find_all("script", src=True):
        src = script.get("src", "")
        if any(tracker in src for tracker in ["hotjar", "intercom", "crisp", "tawk"]):
            script.decompose()

    # 6. Injecter le Meta Pixel
    pixel_script = f"""
    <script>
      !function(f,b,e,v,n,t,s){{...}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');
      fbq('init', '{os.environ["META_PIXEL_ID"]}');
      fbq('track', 'PageView');
    </script>
    """
    soup.head.append(BeautifulSoup(pixel_script, "html.parser"))

    return str(soup)
```

---

## Vérification que tout fonctionne

```bash
# Vérifier la propagation DNS
dig ignuva.shop A
# Doit retourner : 178.105.100.232

# Vérifier le certificat HTTPS
curl -I https://ignuva.shop
# Doit retourner : HTTP/2 200 (ou 404 si pas de index.html à la racine)

# Tester une landing spécifique
curl -I https://ignuva.shop/produit1
# Doit retourner : HTTP/2 200

# Vérifier les containers
docker compose ps
# Doit afficher traefik et landings en "running"

# Logs Traefik (certificat Let's Encrypt)
docker compose logs traefik | grep -i "certificate\|acme\|error"
```

---

## Publication manuelle de test

```bash
# Créer une landing de test depuis le VPS
mkdir -p /opt/launch-engine/landings/test
cat > /opt/launch-engine/landings/test/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Test Landing</title></head>
<body><h1>✅ Ignuva Landing Engine fonctionne</h1></body>
</html>
EOF

# Accessible immédiatement sur :
# https://ignuva.shop/test
```

---

## Variables d'environnement du bot

Le bot doit avoir accès à ces variables pour les fonctions de publication et Meta Ads :

```dotenv
# Meta
META_AD_ACCOUNT_ID=1034387189758630
META_ACCESS_TOKEN=<token>
META_PIXEL_ID=1369571204982537
META_PAGE_ID=1110205078842924

# Cloudflare R2
R2_ACCESS_KEY_ID=be5a65bbb8f5936c629421e9d00d5e3d
R2_SECRET_ACCESS_KEY=e44b182d44ec140da2cfc0e6296682b99d3b420b07fb0c74b509993d893ef77f
R2_ENDPOINT=https://c299aec68b696628e4c7ec8b4a98dbd2.r2.cloudflarestorage.com
R2_BUCKET=launch-engine-creatives
R2_PUBLIC_URL=https://pub-a7e4dc4a348740188ab83fae76338f71.r2.dev

# Landing hosting
LANDINGS_DIR=/app/landings
LANDINGS_BASE_URL=https://ignuva.shop
```

---

## Règles importantes pour l'IA

1. **Ne jamais redémarrer Nginx** pour publier une landing — les fichiers sont servis à la volée.
2. **Le slug du produit = le path URL** — `slugify(product_name)` doit être déterministe et URL-safe.
3. **Toujours écrire `index.html`** dans le dossier du produit — Nginx sert `index.html` par défaut sur un path `/produit`.
4. **Les assets doivent être relatifs** dans le HTML — utiliser `/assets/...` ou `./assets/...`, jamais des URLs absolues vers le site d'origine.
5. **Injecter le Meta Pixel** dans chaque landing avant publication (voir section Modification HTML).
6. **L'URL de la landing = `link-url`** dans `meta ads creative create` — c'est la destination du clic dans l'ad.
7. **`acme.json` doit être chmod 600** — Traefik refuse de démarrer sinon.
8. **Attendre la propagation DNS** avant le premier `docker compose up` — sinon Let's Encrypt échoue et il faut attendre 1h (rate limit).