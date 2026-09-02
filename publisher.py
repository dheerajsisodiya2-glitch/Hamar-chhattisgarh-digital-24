"""
publisher.py - Social media publishing module.
Supports: Facebook, Instagram, Twitter/X, YouTube (community posts), Gmail (newsletter).
Each platform is independent — if credentials are missing, it gracefully reports
"not connected" instead of crashing.
"""
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from modules import database as db
from modules.config import load_config


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
