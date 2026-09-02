"""
config.py - Central configuration for the News Hub AI Agent.
Holds RSS sources, keywords, and platform credential placeholders.
"""
import os
import json

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "news_hub.db")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# Default RSS sources  (Chhattisgarh + national Hindi/English news)
# ---------------------------------------------------------------------------
DEFAULT_RSS_SOURCES = [
    # --- Chhattisgarh local ---
    {"name": "Patrika Chhattisgarh", "url": "https://www.patrika.com/rss/chhattisgarh-news.xml", "lang": "hi", "region": "chhattisgarh"},
    {"name": "Bhaskar Chhattisgarh", "url": "https://www.bhaskar.com/rss-feed/1061/", "lang": "hi", "region": "chhattisgarh"},
    {"name": "Amar Ujala CG", "url": "https://www.amarujala.com/rss/chhattisgarh", "lang": "hi", "region": "chhattisgarh"},
    {"name": "Navbharat CG", "url": "https://www.navbharattimes.com/feeds/rssfeedsdefault.cms", "lang": "hi", "region": "national"},
    # --- National ---
    {"name": "NDTV India", "url": "https://www.ndtv.com/rss/india", "lang": "en", "region": "national"},
    {"name": "Aaj Tak", "url": "https://www.aajtak.in/rssfeeds/?id=home", "lang": "hi", "region": "national"},
    {"name": "BBC Hindi", "url": "https://feeds.bbci.co.uk/hindi/rss.xml", "lang": "hi", "region": "national"},
    {"name": "ANI News", "url": "https://www.aninews.in/rss/feed/category/national", "lang": "en", "region": "national"},
    # --- Business / Tech (optional extras) ---
    {"name": "Moneycontrol", "url": "https://www.moneycontrol.com/rss/latestnews.xml", "lang": "en", "region": "business"},
    {"name": "Gadgets Now", "url": "https://www.gadgetsnow.com/rssfeeds/2147478067.cms", "lang": "en", "region": "tech"},
]

# Keywords that tag a story as Chhattisgarh-relevant
CG_KEYWORDS = [
    "chhattisgarh", "raipur", "bilaspur", "bhilai", "durg", "korba", "raigarh",
    "jagdalpur", "dhamtari", "mahasamund", "ambikapur", "bastar", "sukma",
    "dantewada", "narayanpur", "kanker", "kondagaon", "rajnandgaon",
    "chirmiri", "baikunthpur", "janjgir", "champa", "kawardha", "kanker",
    "cg news", "छत्तीसगढ़", "रायपुर", "बिलासपुर", "भिलाई", "दुर्ग",
    "कोरबा", "रायगढ़", "जगदलपुर", "बस्तर", "सूकमा", "दंतेवाड़ा",
    "बैकुंठपुर", "अंबिकापुर", "धमतरी", "महासमुंद",
]

# Category keywords for auto-tagging
CATEGORY_KEYWORDS = {
    "राजनीति / Politics": [
        "minister", "mla", "mp", "election", "bjp", "congress", "cm ", "chief minister",
        "मंत्री", "विधायक", "सांसद", "चुनाव", "मुख्यमंत्री",
    ],
    "अपराध / Crime": [
        "murder", "theft", "robbery", "accused", "arrest", "police", "crime",
        "मर्डर", "चोरी", "लूट", "गिरफ्तार", "पुलिस", "हत्या", "दुर्घटना",
    ],
    "व्यापार / Business": [
        "business", "market", "economy", "trade", "industry", "gst", "budget",
        "बाजार", "व्यापार", "उद्योग", "बजट", "कंपनी",
    ],
    "शिक्षा / Education": [
        "school", "college", "university", "exam", "result", "student", "education",
        "स्कूल", "कॉलेज", "विश्वविद्यालय", "परीक्षा", "रिजल्ट", "छात्र",
    ],
    "खेल / Sports": [
        "cricket", "match", "tournament", "player", "team", "goal", "win",
        "क्रिकेट", "मैच", "खिलाड़ी", "टीम", "जीत",
    ],
    "स्वास्थ्य / Health": [
        "health", "hospital", "disease", "doctor", "patient", "medicine", "corona",
        "स्वास्थ्य", "अस्पताल", "बीमारी", "डॉक्टर", "मरीज",
    ],
    "कृषि / Agriculture": [
        "farmer", "crop", "agriculture", "irrigation", "loan waiver", "msp",
        "किसान", "फसल", "खेती", "सिंचाई", "कर्ज माफी",
    ],
}


# ---------------------------------------------------------------------------
# Social-media platform config  (credentials filled by user at runtime)
# ---------------------------------------------------------------------------
DEFAULT_PLATFORMS = {
    "facebook": {
        "name": "Facebook",
        "icon": "📘",
        "connected": False,
        "credentials": {
            "page_access_token": "",
            "page_id": "",
        },
        "notes": "Facebook Graph API v19 — needs a Page access token & Page ID.",
    },
    "instagram": {
        "name": "Instagram",
        "icon": "📸",
        "connected": False,
        "credentials": {
            "access_token": "",
            "ig_user_id": "",
        },
        "notes": "Instagram Graph API — requires a Business account linked to a FB Page.",
    },
    "twitter": {
        "name": "Twitter / X",
        "icon": "🐦",
        "connected": False,
        "credentials": {
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "access_token_secret": "",
            "bearer_token": "",
        },
        "notes": "X API v2 — free tier allows 1 post / 24 hrs (1,500 / month).",
    },
    "youtube": {
        "name": "YouTube",
        "icon": "▶️",
        "connected": False,
        "credentials": {
            "api_key": "",
            "client_id": "",
            "client_secret": "",
        },
        "notes": "YouTube Data API v3 — for community posts & video uploads.",
    },
    "gmail": {
        "name": "Gmail (Newsletter)",
        "icon": "✉️",
        "connected": False,
        "credentials": {
            "app_email": "",
            "app_password": "",
        },
        "notes": "For sending news as email newsletter. Use a Gmail App Password.",
    },
}


# ---------------------------------------------------------------------------
# Config load / save
# ---------------------------------------------------------------------------
def load_config():
    """Load user config from disk, or return defaults."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    cfg = {
        "rss_sources": DEFAULT_RSS_SOURCES,
        "platforms": DEFAULT_PLATFORMS,
        "settings": {
            "auto_fetch_interval_minutes": 30,
            "max_news_items": 100,
            "default_hashtags": "#ChhattisgarhNews #CGNews #News",
        },
    }
    save_config(cfg)
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
