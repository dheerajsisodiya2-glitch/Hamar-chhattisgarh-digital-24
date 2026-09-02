"""
aggregator.py - RSS news fetcher, filterer, and auto-categoriser.
Pulls from configured RSS feeds, detects Chhattisgarh relevance,
tags a category, and stores into the database.
"""
import re
import feedparser
from datetime import datetime
from modules import database as db
from modules.config import CG_KEYWORDS, CATEGORY_KEYWORDS


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
