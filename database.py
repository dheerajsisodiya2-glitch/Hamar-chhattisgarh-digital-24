"""
database.py - SQLite layer for news, posts, and schedules.
"""
import sqlite3
import json
from datetime import datetime
from modules.config import DB_PATH


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
