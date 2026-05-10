import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from db import add_automation_keyword

KEYWORDS_DATA = {
    "Produits AI personnalisés": [
        "AI baby face generator", "AI baby predictor", "future baby face",
        "personalized AI song", "custom AI song", "AI portrait", "AI headshot generator",
        "AI pet portrait", "AI family portrait", "AI avatar pack", "AI voice clone",
        "AI children's book", "AI bedtime story personalized", "restore old photo AI",
        "colorize old photo AI", "AI cartoon portrait", "AI superhero portrait",
        "AI action figure generator", "turn photo into painting AI"
    ],
    "Templates / Printables / Presets": [
        "digital planner", "budget spreadsheet template", "Canva template pack",
        "social media template", "Notion template", "Lightroom preset pack",
        "resume template", "content calendar template", "wedding planner printable",
        "meal plan template", "fitness planner digital", "habit tracker printable",
        "self care journal", "recipe book template", "cleaning schedule printable",
        "homeschool planner", "teacher printable"
    ],
    "Education / Learning": [
        "ABC learning", "alphabet flashcards", "phonics worksheets", "sight words printable",
        "math worksheets kids", "nursing flashcards", "NCLEX study guide",
        "language learning flashcards", "handwriting practice sheets",
        "toddler activity printable", "preschool curriculum", "homeschool worksheets",
        "anatomy flashcards", "multiplication table printable"
    ],
    "Ebooks / Guides / Protocoles": [
        "ebook digital download", "how to guide PDF", "mini course",
        "protocol PDF", "challenge 7 day", "challenge 30 day",
        "weight loss guide", "skincare routine guide", "fitness program digital",
        "meditation guide audio", "astrology reading personalized"
    ],
    "Audio / Sound": [
        "personalized song", "custom lullaby", "meditation audio", "sleep sounds",
        "affirmation audio", "guided visualization", "hypnosis audio",
        "frequency healing", "sound bath recording"
    ],
    "Produits physiques convertibles en digital": [
        "anti cerne", "dark circles treatment", "acne treatment", "hair growth",
        "teeth whitening", "posture corrector", "back pain relief", "knee brace",
        "sleep aid", "detox tea", "gut health", "face yoga", "jaw exerciser",
        "cellulite cream", "stretch mark", "snoring device", "foot pain insole",
        "wrist brace carpal tunnel", "neck pain pillow", "migraine relief",
        "anxiety supplement", "focus supplement", "collagen supplement",
        "hormone balance", "menopause supplement", "weight loss supplement"
    ]
}

def init_keywords():
    print("Initializing keywords...")
    for category, keywords in KEYWORDS_DATA.items():
        for kw in keywords:
            kw = kw.strip()
            if kw:
                add_automation_keyword(category, kw)
    print("Done!")

if __name__ == "__main__":
    init_keywords()
