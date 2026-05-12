# Launch Engine — R2 Storage Integration

## Contexte

Cloudflare R2 est notre stockage objet partagé pour tous les fichiers produits par le système :
- Créatives scrapées par Tony (vidéos, images depuis Meta/TikTok/Etsy/Google)
- Créatives générées par Idriss (vidéos, images, screenshots de LP)
- Screenshots uploadés par les humains lors des review requests

R2 est S3-compatible, donc n'importe quel SDK S3 fonctionne.

## Infos de base

- **Bucket name** : `launch-engine-creatives`
- **Endpoint S3** : `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` (Simon te file la valeur exacte)
- **Public URL** : `https://pub-<HASH>.r2.dev` (Simon te file la valeur exacte après activation du public URL)

## Credentials nécessaires

Tu reçois ces 3 valeurs **en privé** de Simon (jamais en clair dans Slack/groupe) :

- **Access Key ID** (commence par un identifiant alphanumérique)
- **Secret Access Key** (long, sensible)
- **Endpoint URL** (au format `https://...r2.cloudflarestorage.com`)

Mets-les dans ton `.env` sous :

```env
R2_ACCESS_KEY_ID=xxxx
R2_SECRET_ACCESS_KEY=xxxx
R2_ENDPOINT=https://xxxx.r2.cloudflarestorage.com
R2_BUCKET=launch-engine-creatives
R2_PUBLIC_URL=https://pub-xxxx.r2.dev
```

## Convention de nommage des fichiers

Structure générale :
```
{origin}/{identifier}/{filename}
```

### Tony (scraping)

```
scrape/meta/<ad_archive_id>/creative-<n>.<ext>
scrape/tiktok/<ad_id>/creative-<n>.<ext>
scrape/google/<ad_id>/creative-<n>.<ext>
scrape/etsy/<store_slug>/<product_id>/<image>.<ext>
scrape/instagram/<ad_id>/creative-<n>.<ext>
```

Exemples :
- `scrape/meta/123456789/creative-1.mp4`
- `scrape/etsy/cozy-home-store/abc123/img-1.jpg`

### Idriss (AI generation)

```
ai/<product_uuid>/lp-screenshot.png         # screenshot de la LP générée
ai/<product_uuid>/creative-<n>.<ext>        # créatives générées (1 à 10)
ai/<product_uuid>/lp-assets/<filename>      # autres assets de la LP si pertinent
```

Exemples :
- `ai/c8e9d2a4-1234-5678-9abc-def012345678/creative-1.mp4`
- `ai/c8e9d2a4-1234-5678-9abc-def012345678/lp-screenshot.png`

### Reviews humaines (uploadées depuis l'UI)

```
reviews/<product_uuid>/<timestamp>-<random>.<ext>
```

Exemple :
- `reviews/c8e9d2a4.../1715000000-abc12.png`

### Pourquoi cette structure ?

- **Cleanup facile** : si on archive un produit, `aws s3 rm --recursive ai/<product_uuid>/` supprime tout en une commande
- **Navigation manuelle** : dans le dashboard R2 Cloudflare, on retrouve facilement les fichiers d'un produit
- **Identification de l'origine** : préfix `scrape/` vs `ai/` permet de distinguer immédiatement source data vs AI-generated

## Code exemples

### Python (Tony — boto3)

```python
import os
import boto3
from botocore.config import Config

# Init client une fois au boot du scraper
s3 = boto3.client(
    's3',
    endpoint_url=os.environ['R2_ENDPOINT'],
    aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
    aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
    config=Config(signature_version='s3v4'),
    region_name='auto',  # R2 ignore la region mais boto3 en exige une
)

# Upload d'un fichier scrapé
def upload_creative(local_path, key, content_type):
    s3.upload_file(
        Filename=local_path,
        Bucket=os.environ['R2_BUCKET'],
        Key=key,
        ExtraArgs={
            'ContentType': content_type,
            'CacheControl': 'public, max-age=31536000',  # 1 an, créatives immutables
        },
    )
    return f"{os.environ['R2_PUBLIC_URL']}/{key}"

# Usage
public_url = upload_creative(
    local_path='/tmp/scraped/video.mp4',
    key='scrape/meta/123456789/creative-1.mp4',
    content_type='video/mp4',
)
# public_url = "https://pub-xxx.r2.dev/scrape/meta/123456789/creative-1.mp4"

# Tu stockes ensuite cette URL dans la table Postgres :
# UPDATE ad_creatives SET local_path = $1 WHERE id = $2  (selon ton schéma)
```

### Node.js (Idriss — @aws-sdk/client-s3 v3)

Install :
```bash
npm install @aws-sdk/client-s3
```

Code :
```javascript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import fs from 'fs';
import path from 'path';

const s3 = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  },
});

async function uploadCreative(localPath, key, contentType) {
  const body = fs.readFileSync(localPath);
  await s3.send(new PutObjectCommand({
    Bucket: process.env.R2_BUCKET,
    Key: key,
    Body: body,
    ContentType: contentType,
    CacheControl: 'public, max-age=31536000',
  }));
  return `${process.env.R2_PUBLIC_URL}/${key}`;
}

// Usage
const publicUrl = await uploadCreative(
  '/tmp/generated/video.mp4',
  `ai/${productUuid}/creative-1.mp4`,
  'video/mp4',
);

// Puis tu stockes dans la DB :
// INSERT INTO product_creatives (product_id, sequence_number, url, type, validation)
//   VALUES ($1, $2, $3, 'video', 'pending')
```

## Workflow complet (exemple Idriss)

```
1. Ton tool génère un produit (free will ou enhanced)
2. INSERT INTO products (...) RETURNING id
3. Ton tool génère la LP en HTML et un screenshot
4. Upload du screenshot → R2 → URL publique
5. UPDATE products SET lp_url = '<url_lp>' WHERE id = $1  (lp_url peut être ta page hostée, ou directement l'URL de la screenshot ou un lien R2)
6. Ton tool génère 10 créatives
7. Pour chaque créative :
   a. Upload sur R2 → URL publique
   b. INSERT INTO product_creatives (product_id, sequence_number, url, type, validation) VALUES (...)
8. UPDATE products SET status = 'creation_pending_review' WHERE id = $1
9. → Le produit apparaît dans Creation côté Simon, prêt à valider
```

## Tips et gotchas

### Permissions
- Le bucket est en accès public en lecture (pour que les URLs s'affichent dans l'UI)
- L'écriture passe par les credentials S3 que je t'ai filés
- Les credentials sont scoped uniquement à ce bucket

### Cache headers
- Mets `Cache-Control: public, max-age=31536000` pour les créatives qui ne changent pas (économise du transfer)
- Pour les screenshots de review qui peuvent être réuploadés, `Cache-Control: no-cache` plus prudent

### Erreurs courantes
- **403 Forbidden** : credentials mauvais, ou tu essaies un bucket différent
- **NoSuchBucket** : nom de bucket pas exact (sensible à la casse)
- **InvalidAccessKeyId** : copie incomplète de l'access key
- **SignatureDoesNotMatch** : signature_version='s3v4' obligatoire en Python boto3

### Test de validation
Avant de brancher en prod, fais un upload de test :

```python
# Python
s3.upload_file('/tmp/test.txt', 'launch-engine-creatives', 'test/hello.txt')
# Vérifie : https://pub-xxx.r2.dev/test/hello.txt
```

Si l'URL publique affiche bien le fichier dans le navigateur, tout marche.

### Cleanup test
```python
s3.delete_object(Bucket='launch-engine-creatives', Key='test/hello.txt')
```

## Limites du free tier

R2 free tier (large pour notre usage) :
- 10 GB stockage
- 1M Class A operations / mois (writes)
- 10M Class B operations / mois (reads)
- Egress gratuit (énorme avantage vs S3)

À 10 produits/jour avec 10 créatives chacun en moyenne (vidéo ~5MB, image ~500KB), on est largement sous la limite stockage les premiers mois. À monitorer si on scale.

## Contact

Pour les credentials, des questions ou un bug → ping Simon.
