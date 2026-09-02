"""
News Hub AI Agent - Single File Version
A unified tool to collect, filter, edit, schedule, and publish
Chhattisgarh & national news to Facebook, Instagram, Twitter, YouTube, Gmail.
No external modules needed - everything is in this one file.
"""
import os
import re
import json
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import requests
import feedparser
import streamlit as st

# ===========================================================================
# CONFIG SECTION
# ===========================================================================
# config.py
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


# ===========================================================================
# DATABASE SECTION  
# ===========================================================================
# database.py
import sqlite3
import json
from datetime import datetime
# DB_PATH defined in config section above


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            link TEXT UNIQUE,
            summary TEXT,
            source TEXT,
            lang TEXT,
            region TEXT,
            category TEXT,
            is_cg_related INTEGER DEFAULT 0,
            published TEXT,
            fetched_at TEXT,
            status TEXT DEFAULT 'new'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER,
            content TEXT,
            hashtags TEXT,
            image_url TEXT,
            platforms TEXT,
            status TEXT DEFAULT 'draft',
            scheduled_at TEXT,
            published_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (news_id) REFERENCES news(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS publish_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            platform TEXT,
            status TEXT,
            message TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def insert_news(item):
    """Insert a news item; skip if link already exists."""
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT OR IGNORE INTO news
            (title, link, summary, source, lang, region, category,
             is_cg_related, published, fetched_at, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            item.get("title", ""),
            item.get("link", ""),
            item.get("summary", ""),
            item.get("source", ""),
            item.get("lang", ""),
            item.get("region", ""),
            item.get("category", ""),
            1 if item.get("is_cg_related") else 0,
            item.get("published", ""),
            datetime.utcnow().isoformat(),
            "new"
        ))
        conn.commit()
    finally:
        conn.close()


def get_news(status=None, cg_only=False, limit=200):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM news WHERE 1=1"
    params = []
    if status:
        q += " AND status=?"
        params.append(status)
    if cg_only:
        q += " AND is_cg_related=1"
    q += " ORDER BY datetime(fetched_at) DESC LIMIT ?"
    params.append(limit)
    c.execute(q, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_news_status(news_id, status):
    conn = get_db()
    conn.execute("UPDATE news SET status=? WHERE id=?", (status, news_id))
    conn.commit()
    conn.close()


def update_news_category(news_id, category):
    conn = get_db()
    conn.execute("UPDATE news SET category=? WHERE id=?", (category, news_id))
    conn.commit()
    conn.close()


def delete_news(news_id):
    conn = get_db()
    conn.execute("DELETE FROM news WHERE id=?", (news_id,))
    conn.commit()
    conn.close()


# ---- Posts ----
def create_post(news_id, content, hashtags, image_url, platforms, scheduled_at=None):
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO posts (news_id, content, hashtags, image_url, platforms, status, scheduled_at)
        VALUES (?,?,?,?,?,?,?)
    """, (news_id, content, hashtags, image_url, json.dumps(platforms),
          "scheduled" if scheduled_at else "draft", scheduled_at))
    post_id = c.lastrowid
    if news_id:
        conn.execute("UPDATE news SET status='used' WHERE id=?", (news_id,))
    conn.commit()
    conn.close()
    return post_id


def get_posts(status=None, limit=100):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM posts"
    params = []
    if status:
        q += " WHERE status=?"
        params.append(status)
    q += " ORDER BY datetime(created_at) DESC LIMIT ?"
    params.append(limit)
    c.execute(q, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def update_post(post_id, content=None, hashtags=None, platforms=None,
                status=None, scheduled_at=None):
    conn = get_db()
    c = conn.cursor()
    fields = []
    params = []
    if content is not None:
        fields.append("content=?"); params.append(content)
    if hashtags is not None:
        fields.append("hashtags=?"); params.append(hashtags)
    if platforms is not None:
        fields.append("platforms=?"); params.append(json.dumps(platforms))
    if status is not None:
        fields.append("status=?"); params.append(status)
    if scheduled_at is not None:
        fields.append("scheduled_at=?"); params.append(scheduled_at)
    if fields:
        params.append(post_id)
        c.execute(f"UPDATE posts SET {', '.join(fields)} WHERE id=?", params)
        conn.commit()
    conn.close()


def delete_post(post_id):
    conn = get_db()
    conn.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()


def log_publish(post_id, platform, status, message):
    conn = get_db()
    conn.execute("""
        INSERT INTO publish_log (post_id, platform, status, message)
        VALUES (?,?,?,?)
    """, (post_id, platform, status, message))
    conn.commit()
    conn.close()


def get_publish_log(limit=50):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM publish_log ORDER BY datetime(timestamp) DESC LIMIT ?",
              (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_pending_scheduled():
    """Return scheduled posts whose time has come."""
    now = datetime.utcnow().isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM posts WHERE status='scheduled'
        AND scheduled_at IS NOT NULL
        AND scheduled_at <= ?
    """, (now,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def stats():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM news"); total = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM news WHERE is_cg_related=1"); cg = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM posts WHERE status='draft'"); drafts = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM posts WHERE status='scheduled'"); sched = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM posts WHERE status='published'"); pub = c.fetchone()["n"]
    conn.close()
    return {"total_news": total, "cg_news": cg, "drafts": drafts,
            "scheduled": sched, "published": pub}


# ===========================================================================
# AGGREGATOR SECTION
# ===========================================================================
# aggregator.py
import re
import feedparser
from datetime import datetime
# database functions defined above
# CG_KEYWORDS, CATEGORY_KEYWORDS defined above


_html_clean = re.compile(r'<[^>]+>')

def clean_html(text):
    return _html_clean.sub('', text or "").strip()


def is_cg_related(title, summary):
    text = f"{title} {summary}".lower()
    return any(kw.lower() in text for kw in CG_KEYWORDS)


def auto_categorise(title, summary):
    text = f"{title} {summary}".lower()
    best_cat, best_score = "सामान्य / General", 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw.lower() in text)
        if score > best_score:
            best_cat, best_score = cat, score
    return best_cat


def fetch_feed(source):
    """Fetch and parse a single RSS feed. Returns list of news dicts."""
    items = []
    try:
        feed = feedparser.parse(source["url"])
        for entry in feed.entries[:50]:
            title = clean_html(entry.get("title", ""))
            summary = clean_html(entry.get("summary", entry.get("description", "")))
            link = entry.get("link", "")
            published = entry.get("published", entry.get("updated", ""))
            if not title:
                continue
            cg = is_cg_related(title, summary)
            category = auto_categorise(title, summary)
            items.append({
                "title": title,
                "link": link,
                "summary": summary[:500],
                "source": source["name"],
                "lang": source.get("lang", "en"),
                "region": "chhattisgarh" if cg else source.get("region", "national"),
                "category": category,
                "is_cg_related": cg,
                "published": published,
            })
    except Exception as e:
        print(f"[aggregator] Error fetching {source['name']}: {e}")
    return items


def fetch_all(sources):
    """Fetch from all sources, store to DB, return summary dict."""
    total_new = 0
    total_cg = 0
    per_source = []
    for src in sources:
        items = fetch_feed(src)
        new_count = 0
        for item in items:
            before = db.get_news(limit=1)
            db.insert_news(item)
            after = db.get_news(limit=1)
            # insert_news uses INSERT OR IGNORE, so check if link existed
            # Simpler: just count items fetched
            new_count += 1
            if item["is_cg_related"]:
                total_cg += 1
        total_new += new_count
        per_source.append({"name": src["name"], "fetched": new_count})
    return {
        "total_fetched": total_new,
        "cg_related": total_cg,
        "per_source": per_source,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


# ===========================================================================
# PUBLISHER SECTION
# ===========================================================================
# publisher.py
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
# database functions defined above
# load_config defined above


def _creds(platform_key):
    cfg = load_config()
    p = cfg["platforms"].get(platform_key, {})
    return p.get("credentials", {}), p.get("connected", False)


# ---------------------------------------------------------------------------
# Facebook  (Graph API v19)
# ---------------------------------------------------------------------------
def publish_facebook(content, image_url=None):
    creds, connected = _creds("facebook")
    if not connected or not creds.get("page_access_token") or not creds.get("page_id"):
        return {"ok": False, "msg": "Facebook not configured. Add Page ID + Page Access Token in Settings."}
    try:
        if image_url:
            url = f"https://graph.facebook.com/v19.0/{creds['page_id']}/photos"
            data = {"message": content, "url": image_url,
                    "access_token": creds["page_access_token"]}
        else:
            url = f"https://graph.facebook.com/v19.0/{creds['page_id']}/feed"
            data = {"message": content, "access_token": creds["page_access_token"]}
        r = requests.post(url, data=data, timeout=30)
        if r.status_code == 200:
            return {"ok": True, "msg": "Facebook post published successfully."}
        return {"ok": False, "msg": f"FB error: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "msg": f"FB exception: {e}"}


# ---------------------------------------------------------------------------
# Instagram  (Graph API — requires image)
# ---------------------------------------------------------------------------
def publish_instagram(content, image_url=None):
    creds, connected = _creds("instagram")
    if not connected or not creds.get("access_token") or not creds.get("ig_user_id"):
        return {"ok": False, "msg": "Instagram not configured. Add IG User ID + Access Token in Settings."}
    if not image_url:
        return {"ok": False, "msg": "Instagram requires an image URL. Add one in the post editor."}
    try:
        # Step 1: create media container
        r = requests.post(
            f"https://graph.facebook.com/v19.0/{creds['ig_user_id']}/media",
            data={"image_url": image_url, "caption": content,
                  "access_token": creds["access_token"]},
            timeout=30)
        container = r.json()
        if "id" not in container:
            return {"ok": False, "msg": f"IG media creation failed: {r.text[:200]}"}
        # Step 2: publish
        r2 = requests.post(
            f"https://graph.facebook.com/v19.0/{creds['ig_user_id']}/media_publish",
            data={"creation_id": container["id"],
                  "access_token": creds["access_token"]},
            timeout=30)
        if r2.status_code == 200:
            return {"ok": True, "msg": "Instagram post published successfully."}
        return {"ok": False, "msg": f"IG publish error: {r2.text[:200]}"}
    except Exception as e:
        return {"ok": False, "msg": f"IG exception: {e}"}


# ---------------------------------------------------------------------------
# Twitter / X  (API v2 — free tier)
# ---------------------------------------------------------------------------
def publish_twitter(content, image_url=None):
    creds, connected = _creds("twitter")
    if not connected or not creds.get("bearer_token"):
        return {"ok": False, "msg": "Twitter/X not configured. Add Bearer Token in Settings."}
    try:
        # Using OAuth 1.0a for posting (free tier supports 1 post/24h)
        import requests as req
        auth_url = "https://api.twitter.com/2/tweets"
        # Simple bearer-based approach for v2 (may need OAuth1 for some accounts)
        headers = {"Authorization": f"Bearer {creds['bearer_token']}",
                   "Content-Type": "application/json"}
        payload = {"text": content[:280]}
        r = req.post(auth_url, headers=headers, json=payload, timeout=30)
        if r.status_code in (200, 201):
            return {"ok": True, "msg": "Tweet posted successfully."}
        return {"ok": False, "msg": f"Twitter error: {r.text[:200]}"}
    except Exception as e:
        return {"ok": False, "msg": f"Twitter exception: {e}"}


# ---------------------------------------------------------------------------
# YouTube  (Data API v3 — community posts)
# ---------------------------------------------------------------------------
def publish_youtube(content, image_url=None):
    creds, connected = _creds("youtube")
    if not connected or not creds.get("api_key"):
        return {"ok": False, "msg": "YouTube not configured. Add API Key in Settings."}
    # YouTube community posts via Data API v3 require OAuth2 — complex.
    # For now, return a helpful message.
    return {"ok": False, "msg": "YouTube posting requires OAuth2 setup. Use the API key for fetching video stats. See SETUP_GUIDE.md."}


# ---------------------------------------------------------------------------
# Gmail  (Newsletter via SMTP)
# ---------------------------------------------------------------------------
def publish_gmail(content, subject="News Update", recipients=None, image_url=None):
    creds, connected = _creds("gmail")
    if not connected or not creds.get("app_email") or not creds.get("app_password"):
        return {"ok": False, "msg": "Gmail not configured. Add App Email + App Password in Settings."}
    if not recipients:
        return {"ok": False, "msg": "No recipients specified for email."}
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = creds["app_email"]
        msg["To"] = ", ".join(recipients) if isinstance(recipients, list) else recipients
        msg["Subject"] = subject
        html = f"""\
<html><body>
<div style="font-family: Arial, sans-serif; max-width:600px; margin:0 auto; padding:20px;">
<h2 style="color:#1a73e8;">📰 {subject}</h2>
<hr>
<p>{content}</p>
"""
        if image_url:
            html += f'<br><img src="{image_url}" style="max-width:100%; border-radius:8px;">'
        html += """
<hr>
<p style="font-size:12px; color:#666;">Sent from News Hub AI Agent</p>
</div></body></html>"""
        msg.attach(MIMEText(content, "plain"))
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
            server.login(creds["app_email"], creds["app_password"])
            server.sendmail(creds["app_email"],
                            recipients if isinstance(recipients, list) else [recipients],
                            msg.as_string())
        return {"ok": True, "msg": "Email sent successfully."}
    except Exception as e:
        return {"ok": False, "msg": f"Gmail exception: {e}"}


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
PUBLISHERS = {
    "facebook": publish_facebook,
    "instagram": publish_instagram,
    "twitter": publish_twitter,
    "youtube": publish_youtube,
    "gmail": publish_gmail,
}


def publish_post(post, gmail_recipients=None):
    """Publish a post to all selected platforms.
    ``post`` is a dict with keys: content, hashtags, image_url, platforms (list).
    Returns a dict {platform: result}.
    """
    content = post.get("content", "")
    hashtags = post.get("hashtags", "")
    full_content = f"{content}\n\n{hashtags}".strip()
    image_url = post.get("image_url") or None
    platforms = post.get("platforms", [])
    if isinstance(platforms, str):
        platforms = json.loads(platforms)
    results = {}
    for p in platforms:
        if p == "gmail":
            res = publish_gmail(full_content,
                                subject=post.get("title", "News Update")[:100],
                                recipients=gmail_recipients or [],
                                image_url=image_url)
        else:
            fn = PUBLISHERS.get(p)
            if fn:
                res = fn(full_content, image_url)
            else:
                res = {"ok": False, "msg": f"Unknown platform: {p}"}
        results[p] = res
        db.log_publish(post.get("id", 0), p,
                       "success" if res["ok"] else "failed",
                       res["msg"])
    return results


# ===========================================================================
# STREAMLIT APP SECTION
# ===========================================================================
import json
import streamlit as st
from datetime import datetime, timedelta
# --- All module functions inlined above ---

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="News Hub AI Agent",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Init DB
db.init_db()

# Load config
cfg = load_config()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown("## 📰 News Hub AI Agent")
st.sidebar.caption("Chhattisgarh News → Social Media")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📡 News Feed", "✍️ Post Editor", "📅 Scheduled Posts",
     "📤 Publish History", "⚙️ Settings"],
    label_visibility="collapsed",
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def status_badge(status):
    colors = {"new": "🔵", "used": "🟢", "draft": "🟡", "scheduled": "🟠",
              "published": "✅", "failed": "🔴"}
    return f"{colors.get(status, '⚪')} {status}"


def platform_icon(p):
    icons = {"facebook": "📘", "instagram": "📸", "twitter": "🐦",
             "youtube": "▶️", "gmail": "✉️"}
    return icons.get(p, "📡")


# ===========================================================================
# DASHBOARD
# ===========================================================================
if page == "📊 Dashboard":
    st.markdown("# 📊 Dashboard")
    st.markdown("Unified control center for news collection and publishing.")
    st.markdown("---")

    s = db.stats()
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total News", s["total_news"])
    col2.metric("CG-Related", s["cg_news"])
    col3.metric("Drafts", s["drafts"])
    col4.metric("Scheduled", s["scheduled"])
    col5.metric("Published", s["published"])

    st.markdown("---")
    st.markdown("### 🚀 Quick Actions")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        if st.button("📡 Fetch Latest News", use_container_width=True):
            with st.spinner("Fetching from all RSS sources..."):
                result = fetch_all(cfg["rss_sources"])
            st.success(f"Fetched {result['total_fetched']} articles "
                       f"({result['cg_related']} CG-related) at {result['timestamp']}")
            st.rerun()
    with qa2:
        if st.button("🔄 Refresh Stats", use_container_width=True):
            st.rerun()
    with qa3:
        if st.button("📤 View Scheduled Posts", use_container_width=True):
            st.info("Go to 'Scheduled Posts' in the left sidebar.")

    st.markdown("---")
    st.markdown("### 📋 Platform Connection Status")
    for key, p in cfg["platforms"].items():
        connected = p.get("connected", False)
        status = "🟢 Connected" if connected else "🔴 Not Connected"
        st.markdown(f"{p['icon']} **{p['name']}** — {status}")

    st.markdown("---")
    st.markdown("### 📈 Recent Publish Log")
    logs = db.get_publish_log(10)
    if logs:
        for log in logs:
            icon = "✅" if log["status"] == "success" else "❌"
            st.markdown(f"{icon} **{log['platform'].title()}** — "
                        f"{log['message'][:80]}  \n"
                        f"<small>{log['timestamp']}</small>",
                        unsafe_allow_html=True)
    else:
        st.info("No publish history yet.")


# ===========================================================================
# NEWS FEED
# ===========================================================================
elif page == "📡 News Feed":
    st.markdown("# 📡 News Feed")
    st.markdown("Collected and filtered news from RSS sources.")
    st.markdown("---")

    # Top bar
    tb1, tb2, tb3, tb4 = st.columns([1, 1, 1, 1])
    with tb1:
        if st.button("📡 Fetch News Now", use_container_width=True):
            with st.spinner("Fetching..."):
                result = fetch_all(cfg["rss_sources"])
            st.success(f"Fetched {result['total_fetched']} articles "
                       f"({result['cg_related']} CG-related)")
            st.rerun()
    with tb2:
        cg_filter = st.checkbox("CG-related only", value=False)
    with tb3:
        cat_filter = st.selectbox("Category",
                                  ["All"] + list(dict.fromkeys(
                                      [n["category"] for n in db.get_news(limit=200)]
                                  )))
    with tb4:
        search = st.text_input("🔍 Search", placeholder="Keyword...")

    st.markdown("---")

    news = db.get_news(limit=200)
    if cg_filter:
        news = [n for n in news if n["is_cg_related"]]
    if cat_filter != "All":
        news = [n for n in news if n["category"] == cat_filter]
    if search:
        s_lower = search.lower()
        news = [n for n in news if s_lower in n["title"].lower()
                or s_lower in n["summary"].lower()]

    if not news:
        st.info("No news found. Click 'Fetch News Now' to pull latest articles.")
    else:
        st.caption(f"Showing {len(news)} articles")
        for item in news:
            cg_tag = "🏷️ **CG**" if item["is_cg_related"] else "🌐"
            with st.expander(
                f"{cg_tag}  {item['title'][:80]}  "
                f"— _{item['source']}_"
            ):
                st.markdown(f"**Category:** {item['category']}  |  "
                            f"**Lang:** {item['lang']}  |  "
                            f"**Status:** {status_badge(item['status'])}")
                st.markdown(f"**Summary:** {item['summary']}")
                st.markdown(f"**Source:** {item['source']}  |  "
                            f"**Published:** {item['published']}")
                st.markdown(f"[🔗 Read Full Article]({item['link']})")

                c1, c2, c3 = st.columns([1,1,4])
                with c1:
                    if st.button("✍️ Create Post", key=f"create_{item['id']}"):
                        st.session_state["edit_news_id"] = item["id"]
                        st.session_state["edit_title"] = item["title"]
                        st.session_state["edit_summary"] = item["summary"]
                        st.session_state["edit_category"] = item["category"]
                        st.session_state["edit_source"] = item["source"]
                        st.info("👆 Go to 'Post Editor' (left sidebar) to compose your post.")
                with c2:
                    if st.button("🗑️ Delete", key=f"del_{item['id']}"):
                        db.delete_news(item["id"])
                        st.rerun()


# ===========================================================================
# POST EDITOR
# ===========================================================================
elif page == "✍️ Post Editor":
    st.markdown("# ✍️ Post Editor")
    st.markdown("Create, edit, and prepare posts for publishing.")
    st.markdown("---")

    # If coming from news feed
    if "edit_news_id" not in st.session_state:
        st.session_state["edit_news_id"] = None
        st.session_state["edit_title"] = ""
        st.session_state["edit_summary"] = ""
        st.session_state["edit_category"] = ""

    # --- Post editor form ---
    st.markdown("### Compose Post")
    title = st.text_input("Post Title / Headline",
                          value=st.session_state.get("edit_title", ""))

    # Pre-fill content from summary
    default_content = ""
    if st.session_state.get("edit_summary"):
        default_content = st.session_state.get("edit_summary", "")

    content = st.text_area("Post Content",
                           value=default_content, height=150,
                           help="Write or edit your news post here.")

    col_a, col_b = st.columns(2)
    with col_a:
        hashtags = st.text_input("Hashtags",
                                value=cfg["settings"].get(
                                    "default_hashtags",
                                    "#ChhattisgarhNews #CGNews #News"))
    with col_b:
        image_url = st.text_input("Image URL (optional)",
                                  placeholder="https://example.com/image.jpg")

    st.markdown("### Select Platforms")
    platform_cols = st.columns(5)
    selected_platforms = []
    for i, (key, p) in enumerate(cfg["platforms"].items()):
        with platform_cols[i]:
            connected = p.get("connected", False)
            label = f"{p['icon']} {p['name']}"
            if not connected:
                label += " ⚠️"
            if st.checkbox(label, key=f"plat_{key}",
                           help=p.get("notes", "")):
                selected_platforms.append(key)

    st.markdown("### Schedule (optional)")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        schedule_date = st.date_input("Date",
                                      min_value=datetime.now().date())
    with col_s2:
        schedule_time = st.time_input("Time",
                                      value=datetime.now().time())

    scheduled_at = None
    schedule_now = st.checkbox("Publish immediately (skip scheduling)")
    if not schedule_now:
        scheduled_at = datetime.combine(schedule_date, schedule_time).isoformat()

    st.markdown("---")

    # Preview
    st.markdown("### 📋 Preview")
    preview_text = f"{content}\n\n{hashtags}".strip()
    st.text_area("Preview (read-only)", value=preview_text, height=100,
                 disabled=True, label_visibility="collapsed")

    # Actions
    ac1, ac2, ac3 = st.columns([2, 1, 1])
    with ac1:
        if st.button("💾 Save as Draft", use_container_width=True):
            if not content:
                st.warning("Content is empty!")
            else:
                post_id = db.create_post(
                    st.session_state.get("edit_news_id"),
                    content, hashtags, image_url,
                    selected_platforms, scheduled_at if scheduled_at else None
                )
                st.success(f"Post saved as draft (ID: {post_id}).")
                st.rerun()
    with ac2:
        if st.button("📅 Schedule", use_container_width=True):
            if not content:
                st.warning("Content is empty!")
            elif not selected_platforms:
                st.warning("Select at least one platform.")
            elif scheduled_at:
                post_id = db.create_post(
                    st.session_state.get("edit_news_id"),
                    content, hashtags, image_url,
                    selected_platforms, scheduled_at
                )
                st.success(f"Post scheduled for {scheduled_at} (ID: {post_id}).")
                st.rerun()
            else:
                st.warning("Enable scheduling or pick a date/time.")
    with ac3:
        if st.button("🚀 Publish Now", use_container_width=True, type="primary"):
            if not content:
                st.warning("Content is empty!")
            elif not selected_platforms:
                st.warning("Select at least one platform.")
            else:
                post = {
                    "id": 0,
                    "title": title,
                    "content": content,
                    "hashtags": hashtags,
                    "image_url": image_url,
                    "platforms": selected_platforms,
                }
                with st.spinner("Publishing..."):
                    results = publish_post(post)
                all_ok = all(r["ok"] for r in results.values()) if results else False
                if all_ok:
                    st.success("✅ Published to all selected platforms!")
                elif results:
                    for plat, res in results.items():
                        if res["ok"]:
                            st.success(f"{platform_icon(plat)} {plat.title()}: {res['msg']}")
                        else:
                            st.error(f"{platform_icon(plat)} {plat.title()}: {res['msg']}")
                else:
                    st.error("No platforms were processed.")


# ===========================================================================
# SCHEDULED POSTS
# ===========================================================================
elif page == "📅 Scheduled Posts":
    st.markdown("# 📅 Scheduled Posts")
    st.markdown("Manage draft and scheduled posts.")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Drafts", "📅 Scheduled"])

    with tab1:
        drafts = db.get_posts("draft")
        if not drafts:
            st.info("No drafts. Create one from the Post Editor.")
        for post in drafts:
            platforms = json.loads(post["platforms"]) if post["platforms"] else []
            plat_str = " ".join(platform_icon(p) for p in platforms)
            with st.expander(f"📝 {post['content'][:60]}... — {plat_str}"):
                st.markdown(f"**Content:** {post['content']}")
                st.markdown(f"**Hashtags:** {post['hashtags']}")
                st.markdown(f"**Image:** {post['image_url'] or 'None'}")
                st.markdown(f"**Platforms:** {', '.join(platforms)}")
                st.markdown(f"**Created:** {post['created_at']}")
                c1, c2 = st.columns([1,1])
                with c1:
                    if st.button("🚀 Publish Now", key=f"pub_d_{post['id']}"):
                        post_data = {
                            "id": post["id"],
                            "title": "News Update",
                            "content": post["content"],
                            "hashtags": post["hashtags"],
                            "image_url": post["image_url"],
                            "platforms": platforms,
                        }
                        with st.spinner("Publishing..."):
                            results = publish_post(post_data)
                        for plat, res in results.items():
                            if res["ok"]:
                                st.success(f"{platform_icon(plat)} {plat.title()}: {res['msg']}")
                            else:
                                st.error(f"{platform_icon(plat)} {plat.title()}: {res['msg']}")
                        db.update_post(post["id"], status="published")
                        st.rerun()
                with c2:
                    if st.button("🗑️ Delete", key=f"del_d_{post['id']}"):
                        db.delete_post(post["id"])
                        st.rerun()

    with tab2:
        scheduled = db.get_posts("scheduled")
        if not scheduled:
            st.info("No scheduled posts. Schedule one from the Post Editor.")
        for post in scheduled:
            platforms = json.loads(post["platforms"]) if post["platforms"] else []
            plat_str = " ".join(platform_icon(p) for p in platforms)
            try:
                dt = datetime.fromisoformat(post["scheduled_at"])
                time_remaining = dt - datetime.now()
                remaining_str = f"⏳ {time_remaining}" if time_remaining.total_seconds() > 0 else "⏰ Due now"
            except Exception:
                remaining_str = ""
            with st.expander(f"📅 {post['content'][:60]}... — {plat_str} — {remaining_str}"):
                st.markdown(f"**Content:** {post['content']}")
                st.markdown(f"**Hashtags:** {post['hashtags']}")
                st.markdown(f"**Image:** {post['image_url'] or 'None'}")
                st.markdown(f"**Platforms:** {', '.join(platforms)}")
                st.markdown(f"**Scheduled At:** {post['scheduled_at']}")
                c1, c2, c3 = st.columns([1,1,1])
                with c1:
                    if st.button("🚀 Publish Now", key=f"pub_s_{post['id']}"):
                        post_data = {
                            "id": post["id"],
                            "title": "News Update",
                            "content": post["content"],
                            "hashtags": post["hashtags"],
                            "image_url": post["image_url"],
                            "platforms": platforms,
                        }
                        with st.spinner("Publishing..."):
                            results = publish_post(post_data)
                        for plat, res in results.items():
                            if res["ok"]:
                                st.success(f"{platform_icon(plat)} {plat.title()}: {res['msg']}")
                            else:
                                st.error(f"{platform_icon(plat)} {plat.title()}: {res['msg']}")
                        db.update_post(post["id"], status="published")
                        st.rerun()
                with c2:
                    if st.button("✏️ Convert to Draft", key=f"edt_s_{post['id']}"):
                        db.update_post(post["id"], status="draft")
                        st.rerun()
                with c3:
                    if st.button("🗑️ Delete", key=f"del_s_{post['id']}"):
                        db.delete_post(post["id"])
                        st.rerun()

        # Auto-publish check
        st.markdown("---")
        st.markdown("### ⏰ Auto-Publisher")
        pending = db.get_pending_scheduled()
        if pending:
            st.warning(f"{len(pending)} post(s) are due for publishing!")
            if st.button("🚀 Publish All Due Posts", type="primary"):
                for post in pending:
                    platforms = json.loads(post["platforms"]) if post["platforms"] else []
                    post_data = {
                        "id": post["id"],
                        "title": "News Update",
                        "content": post["content"],
                        "hashtags": post["hashtags"],
                        "image_url": post["image_url"],
                        "platforms": platforms,
                    }
                    results = publish_post(post_data)
                    for plat, res in results.items():
                        if res["ok"]:
                            st.success(f"{platform_icon(plat)} Post {post['id']} → {plat}: OK")
                        else:
                            st.error(f"{platform_icon(plat)} Post {post['id']} → {plat}: {res['msg']}")
                    db.update_post(post["id"], status="published")
                st.rerun()
        else:
            st.success("No posts are due right now.")


# ===========================================================================
# PUBLISH HISTORY
# ===========================================================================
elif page == "📤 Publish History":
    st.markdown("# 📤 Publish History")
    st.markdown("Log of all publish attempts.")
    st.markdown("---")

    logs = db.get_publish_log(100)
    if not logs:
        st.info("No publish history yet. Publish a post to see logs here.")
    else:
        # Build a table
        st.markdown(f"**Total log entries:** {len(logs)}")
        st.markdown("---")
        for log in logs:
            icon = "✅" if log["status"] == "success" else "❌"
            st.markdown(f"{icon} **{log['platform'].title()}** "
                        f"(Post #{log['post_id']}) — {log['message']}  \n"
                        f"<small>{log['timestamp']}</small>",
                        unsafe_allow_html=True)


# ===========================================================================
# SETTINGS
# ===========================================================================
elif page == "⚙️ Settings":
    st.markdown("# ⚙️ Settings")
    st.markdown("Configure RSS sources, platform credentials, and preferences.")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📡 RSS Sources",
                                  "🔐 Platform Credentials",
                                  "⚙️ General"])

    # --- RSS Sources ---
    with tab1:
        st.markdown("### RSS Feed Sources")
        st.caption("Add or remove RSS feeds for news collection.")
        sources = cfg.get("rss_sources", [])
        for i, src in enumerate(sources):
            c1, c2, c3, c4, c5 = st.columns([3, 3, 1, 1, 1])
            with c1:
                src["name"] = st.text_input("Name", value=src["name"],
                                            key=f"src_name_{i}")
            with c2:
                src["url"] = st.text_input("URL", value=src["url"],
                                           key=f"src_url_{i}")
            with c3:
                src["lang"] = st.selectbox("Lang", ["hi", "en"],
                                           index=0 if src["lang"]=="hi" else 1,
                                           key=f"src_lang_{i}")
            with c4:
                src["region"] = st.text_input("Region", value=src["region"],
                                             key=f"src_region_{i}")
            with c5:
                if st.button("🗑️", key=f"src_del_{i}"):
                    sources.pop(i)
                    cfg["rss_sources"] = sources
                    save_config(cfg)
                    st.rerun()

        st.markdown("---")
        nc1, nc2, nc3, nc4 = st.columns([3, 3, 1, 1])
        with nc1:
            new_name = st.text_input("New Source Name", key="new_name")
        with nc2:
            new_url = st.text_input("New Source URL", key="new_url")
        with nc3:
            new_lang = st.selectbox("Lang", ["hi", "en"], key="new_lang")
        with nc4:
            new_region = st.text_input("Region", value="national", key="new_region")

        if st.button("➕ Add Source"):
            if new_name and new_url:
                sources.append({"name": new_name, "url": new_url,
                                "lang": new_lang, "region": new_region})
                cfg["rss_sources"] = sources
                save_config(cfg)
                st.success(f"Added: {new_name}")
                st.rerun()

        st.markdown("---")
        if st.button("💾 Save All Sources"):
            cfg["rss_sources"] = sources
            save_config(cfg)
            st.success("RSS sources saved!")

    # --- Platform Credentials ---
    with tab2:
        st.markdown("### Platform Credentials")
        st.caption("Enter API credentials for each platform. "
                   "See SETUP_GUIDE.md for how to obtain them.")

        for key, p in cfg["platforms"].items():
            st.markdown(f"#### {p['icon']} {p['name']}")
            st.caption(p.get("notes", ""))

            connected = st.checkbox(f"Connected", value=p.get("connected", False),
                                     key=f"conn_{key}")
            p["connected"] = connected

            for cred_key, cred_val in p["credentials"].items():
                if "password" in cred_key or "secret" in cred_key or "token" in cred_key:
                    p["credentials"][cred_key] = st.text_input(
                        cred_key, value=cred_val, type="password",
                        key=f"cred_{key}_{cred_key}")
                else:
                    p["credentials"][cred_key] = st.text_input(
                        cred_key, value=cred_val,
                        key=f"cred_{key}_{cred_key}")
            st.markdown("---")

        if st.button("💾 Save All Credentials", type="primary"):
            save_config(cfg)
            st.success("All platform credentials saved!")

    # --- General ---
    with tab3:
        st.markdown("### General Settings")
        settings = cfg.get("settings", {})
        settings["auto_fetch_interval_minutes"] = st.number_input(
            "Auto-fetch interval (minutes)",
            min_value=5, max_value=1440,
            value=settings.get("auto_fetch_interval_minutes", 30))
        settings["max_news_items"] = st.number_input(
            "Max news items to store",
            min_value=50, max_value=10000,
            value=settings.get("max_news_items", 100))
        settings["default_hashtags"] = st.text_input(
            "Default hashtags",
            value=settings.get("default_hashtags",
                               "#ChhattisgarhNews #CGNews #News"))

        if st.button("💾 Save Settings"):
            cfg["settings"] = settings
            save_config(cfg)
            st.success("Settings saved!")

        st.markdown("---")
        st.markdown("### 🗄️ Database Management")
        st.caption("Manage stored news and posts.")
        dc1, dc2, dc3 = st.columns(3)
        with dc1:
            if st.button("🗑️ Clear All News"):
                conn = db.get_db()
                conn.execute("DELETE FROM news")
                conn.commit()
                conn.close()
                st.success("All news cleared.")
                st.rerun()
        with dc2:
            if st.button("🗑️ Clear All Posts"):
                conn = db.get_db()
                conn.execute("DELETE FROM posts")
                conn.commit()
                conn.close()
                st.success("All posts cleared.")
                st.rerun()
        with dc3:
            if st.button("🔄 Reset Everything"):
                conn = db.get_db()
                conn.execute("DELETE FROM news")
                conn.execute("DELETE FROM posts")
                conn.execute("DELETE FROM publish_log")
                conn.commit()
                conn.close()
                st.success("Database reset.")
                st.rerun()

