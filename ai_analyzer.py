import os
import json
import time
import requests
from dotenv import load_dotenv
import db

load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
MODEL_NAME = os.getenv("MODEL_OPENROUTER", "anthropic/claude-3.5-sonnet")

SYSTEM_PROMPT = """
Tu es un expert en détection de produits winners pour une machine qui :
1. Détecte des produits qui se vendent bien (sur Amazon, Etsy, TikTok, Facebook)
2. Les repackage en produits DIGITAUX vendus $10-40 (Guides, Templates, Cours, Checklists, Outils)
3. Detection de produits digitaux.

RÈGLES D'ANALYSE :

1. COMPRENDS LE PRODUIT/OFFRE :
   - Sur Amazon/Etsy : Utilise le titre + description. Les REVIEWS sont le signal #1 ( proxy des ventes). et surtout determine si le produit vendu est un produit digitaux.
   - Sur TikTok/Facebook : Utilise le texte de l'Ad et le nom de l'annonceur. Si l'ad est récente ou a peu de reach, analyse le POTENTIEL du concept créatif. et surtout determine si le produit vendu est un produit digitaux.

2. SOIS ANALYTIQUE, PAS DISMISSIF : Même si certaines données manquent, utilise ce que tu as (Nom de la marque, Titre, Image) pour inférer le potentiel. Un annonceur qui dépense sur TikTok/Facebook a souvent un produit validé ailleurs.

3. RECONNAISSANCE DE MARQUE : Si l'annonceur est une marque connue ou une niche spécifique, utilise tes connaissances internes pour enrichir l'analyse.

4. LE PRIX SOURCE N'EST PAS UN FILTRE. Peu importe le prix du produit physique, notre prix de vente digital sera toujours $10-40.

5. PROPOSE L'IDÉE DE REPACKAGE DIGITAL : Sois spécifique et créatif. Ne te contente pas de dire "un guide", dis "Un plan d'action de 21 jours pour...".

6. ÉVALUE L'EFFORT DE PRODUCTION :
   - LOW = 1-2 jours (templates, printables, PDF)
   - MEDIUM = 3-5 jours (contenu original, vidéos AI, audio)
   - HIGH = 1-2 semaines (app web, contenu complexe)

7. POUR TIKTOK/FACEBOOK : Analyse l'angle marketing (ex: "Problem-Solution", "User Generated Content", "Fear of Missing Out"). Suggère comment cet angle peut être utilisé pour vendre le produit digital.

Pour chaque produit, réponds EXCLUSIVEMENT en JSON structuré respectant ce format :
{
  "product_name": "titre original",
  "source_platform": "amazon|etsy|facebook|tiktok",
  "source_url": "url",
  "source_price": 0.0,
  "reviews_count": 0,
  "digital_product": "true|false",

  "ai_analysis": {
    "what_is_it": "Description courte",
    "is_relevant": true,
    "relevance_reason": "Pourquoi c'est un bon signal",
    "skip_reason": null,

    "digital_repackage_idea": "Description de l'idée digitale précise",
    "our_suggested_price": "$19-$39",
    "estimated_margin": "95%+",
    "production_effort": "LOW|MEDIUM|HIGH",

    "demand_level": "LOW|MEDIUM|HIGH|MASSIVE",
    "demand_evidence": "Preuves (ex: 'Marque établie', '1500 reviews', 'Angle marketing fort')",

    "priority": "LOW|MEDIUM|HIGH",
    "priority_reason": "Pourquoi cette priorité",

    "suggested_concepts": ["Concept 1", "Concept 2"],
    "warnings": []
  }
}
"""

# Cache for system prompt (5 min TTL)
_prompt_cache = {"text": None, "fetched_at": 0}
CACHE_TTL_SECONDS = 300

def get_active_system_prompt(prompt_key="product_analyzer"):
    """Get active system prompt from DB, with 5-min cache"""
    global _prompt_cache

    now = time.time()
    if _prompt_cache["text"] and (now - _prompt_cache["fetched_at"]) < CACHE_TTL_SECONDS:
        return _prompt_cache["text"]

    # Try to fetch from DB
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT prompt_text FROM system_prompts WHERE prompt_key = %s AND is_active = TRUE",
            (prompt_key,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and row[0]:
            _prompt_cache = {"text": row[0], "fetched_at": now}
            return row[0]
    except Exception as e:
        print(f"[ai_analyzer] Error fetching prompt from DB: {e}")

    # Fallback to hardcoded
    return SYSTEM_PROMPT

def clear_prompt_cache():
    """Clear the prompt cache (call after updating prompt)"""
    global _prompt_cache
    _prompt_cache = {"text": None, "fetched_at": 0}

def analyze_product(product_data, platform):
    """
    Analyze a product using Claude via OpenRouter
    """
    if not OPENROUTER_KEY:
        return {"error": "OPENROUTER_KEY not found in .env"}

    # Format the product data for the prompt
    prompt_input = {
        "platform": platform,
        "data": product_data
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "HTTP-Referer": "https://github.com/OpenRouterTeam/openrouter-python",
                "X-Title": "Ad Intel Analyzer",
            },
            data=json.dumps({
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": get_active_system_prompt()},
                    {"role": "user", "content": f"Analyze this product from {platform}: {json.dumps(product_data, indent=2)}"}
                ],
                "response_format": {"type": "json_object"}
            }),
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error from OpenRouter: {response.status_code} - {response.text}")
            return {"error": f"API Error: {response.status_code}"}

        try:
            result = response.json()
            if 'choices' not in result or not result['choices']:
                return {"error": "Empty response from AI model"}
            content = result['choices'][0]['message']['content']
            if not content:
                return {"error": "AI model returned empty content"}
            
            # Clean up content: handle markdown code blocks and whitespace
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(f"Failed to parse AI response: {content}")
            return {"error": f"Invalid AI response format: {str(e)}"}

    except requests.exceptions.Timeout:
        return {"error": "AI analysis timed out after 30 seconds"}
    except Exception as e:
        print(f"Exception during AI analysis: {e}")
        return {"error": str(e)}

def batch_analyze(products, platform):
    """
    Analyze a batch of products. In a real scenario, we might want to 
    send them all at once to Claude if the context window allows, 
    but for reliability we'll do them one by one or in smaller chunks.
    """
    results = []
    for p in products:
        verdict = analyze_product(p, platform)
        results.append(verdict)
    return results
