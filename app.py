"""
News Hub AI Agent - Final Version
Chhattisgarh news collection, filtering, poster creation, video generation,
and multi-platform publishing. Single file, no external modules folder.
"""
import os
import re
import io
import json
import sqlite3
import smtplib
import subprocess
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import requests
import feedparser
import streamlit as st

# --- PIL for image generation ---
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# --- gTTS for AI voice ---
try:
    from gtts import gTTS
    HAS_GTTS = True
except ImportError:
    HAS_GTTS = False

# --- imageio-ffmpeg: bundles ffmpeg binary in pip, NO apt needed ---
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    HAS_FFMPEG = True
except Exception:
    FFMPEG_PATH = None
    HAS_FFMPEG = False


# ===========================================================================
# CONFIG
# ===========================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "news_hub.db")
CONFIG_PATH = os.path.join(DATA_DIR, "config.json")
os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_RSS_SOURCES = [
    {"name": "Patrika Chhattisgarh", "url": "https://www.patrika.com/rss/chhattisgarh-news.xml", "lang": "hi", "region": "chhattisgarh"},
    {"name": "Bhaskar Chhattisgarh", "url": "https://www.bhaskar.com/rss-feed/1061/", "lang": "hi", "region": "chhattisgarh"},
    {"name": "Amar Ujala CG", "url": "https://www.amarujala.com/rss/chhattisgarh", "lang": "hi", "region": "chhattisgarh"},
    {"name": "NDTV India", "url": "https://www.ndtv.com/rss/india", "lang": "en", "region": "national"},
    {"name": "Aaj Tak", "url": "https://www.aajtak.in/rssfeeds/?id=home", "lang": "hi", "region": "national"},
    {"name": "BBC Hindi", "url": "https://feeds.bbci.co.uk/hindi/rss.xml", "lang": "hi", "region": "national"},
    {"name": "ANI News", "url": "https://www.aninews.in/rss/feed/category/national", "lang": "en", "region": "national"},
    {"name": "Moneycontrol", "url": "https://www.moneycontrol.com/rss/latestnews.xml", "lang": "en", "region": "business"},
]

CG_KEYWORDS = [
    "chhattisgarh","raipur","bilaspur","bhilai","durg","korba","raigarh",
    "jagdalpur","dhamtari","mahasamund","ambikapur","bastar","sukma",
    "dantewada","narayanpur","kanker","kondagaon","rajnandgaon",
    "chirmiri","baikunthpur","janjgir","champa","kawardha","cg news",
    "\u091b\u0924\u094d\u0924\u0940\u0938\u0917\u0922\u093c","\u0930\u093e\u092f\u092a\u0941\u0930",
    "\u092c\u093f\u0932\u093e\u0938\u092a\u0941\u0930","\u092d\u093f\u0932\u093e\u0908","\u0926\u0941\u0930\u094d\u0917",
    "\u0915\u094b\u0930\u092c\u093e","\u0930\u093e\u092f\u0917\u0922\u093c","\u091c\u0917\u0926\u0932\u092a\u0941\u0930",
    "\u092c\u0938\u094d\u0924\u0930","\u0938\u0942\u0915\u092e\u093e","\u0926\u0902\u0924\u0947\u0935\u093e\u0921\u093c\u093e",
    "\u092c\u0948\u0915\u0941\u0902\u0920\u092a\u0941\u0930","\u0905\u0902\u092c\u093f\u0915\u093e\u092a\u0941\u0930",
    "\u0927\u092e\u0924\u0930\u0940","\u092e\u0939\u093e\u0938\u092e\u0941\u0902\u0926",
]

CATEGORY_KEYWORDS = {
    "Politics": ["minister","mla","mp","election","bjp","congress","cm ","chief minister","\u092e\u0902\u0924\u094d\u0930\u0940","\u0935\u093f\u0927\u093e\u092f\u0915","\u091a\u0941\u0928\u093e\u0935","\u092e\u0941\u0916\u094d\u092f\u092e\u0902\u0924\u094d\u0930\u0940"],
    "Crime": ["murder","theft","robbery","accused","arrest","police","crime","\u091a\u094b\u0930\u0940","\u0932\u0942\u091f","\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930","\u092a\u0941\u0932\u093f\u0938","\u0939\u0924\u094d\u092f\u093e","\u0926\u0941\u0930\u094d\u0918\u091f\u0928\u093e"],
    "Business": ["business","market","economy","trade","industry","gst","budget","\u092c\u093e\u091c\u093e\u0930","\u0935\u094d\u092f\u093e\u092a\u093e\u0930","\u0909\u0926\u094d\u092f\u094b\u0917","\u092c\u091c\u091f"],
    "Education": ["school","college","university","exam","result","student","education","\u0938\u094d\u0915\u0942\u0932","\u0915\u0949\u0932\u0947\u091c","\u092a\u0930\u0940\u0915\u094d\u0937\u093e","\u0930\u093f\u091c\u0932\u094d\u091f","\u091b\u093e\u0924\u094d\u0930"],
    "Sports": ["cricket","match","tournament","player","team","goal","win","\u0915\u094d\u0930\u093f\u0915\u0947\u091f","\u092e\u0948\u091a","\u0916\u093f\u0932\u093e\u0921\u093c\u0940","\u091f\u0940\u092e"],
    "Health": ["health","hospital","disease","doctor","patient","medicine","\u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f","\u0905\u0938\u094d\u092a\u0924\u093e\u0932","\u092c\u0940\u092e\u093e\u0930\u0940","\u0921\u0949\u0915\u094d\u091f\u0930"],
    "Agriculture": ["farmer","crop","agriculture","irrigation","loan waiver","msp","\u0915\u093f\u0938\u093e\u0928","\u092b\u0938\u0932","\u0916\u0947\u0924\u0940","\u0938\u093f\u0902\u091a\u093e\u0908"],
}

DEFAULT_PLATFORMS = {
    "facebook": {"name":"Facebook","connected":False,
                 "credentials":{"page_access_token":"","page_id":""},
                 "notes":"Needs Page Access Token + Page ID from Facebook Graph API."},
    "instagram": {"name":"Instagram","connected":False,
                  "credentials":{"access_token":"","ig_user_id":""},
                  "notes":"Needs Business IG account linked to FB Page. See Instagram Setup Guide tab."},
    "twitter": {"name":"Twitter/X","connected":False,
                "credentials":{"bearer_token":""},
                "notes":"X API v2 free tier. 1500 posts/month."},
    "gmail": {"name":"Gmail","connected":False,
              "credentials":{"app_email":"","app_password":""},
              "notes":"Use Gmail App Password (not regular password)."},
}

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    cfg = {"rss_sources":DEFAULT_RSS_SOURCES,"platforms":DEFAULT_PLATFORMS,
           "settings":{"default_hashtags":"#ChhattisgarhNews #CGNews #News"}}
    save_config(cfg)
    return cfg

def save_config(cfg):
    with open(CONFIG_PATH,"w",encoding="utf-8") as f:
        json.dump(cfg,f,ensure_ascii=False,indent=2)


# ===========================================================================
# DATABASE
# ===========================================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS news(
        id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,link TEXT UNIQUE,
        summary TEXT,source TEXT,lang TEXT,region TEXT,category TEXT,
        is_cg_related INTEGER DEFAULT 0,published TEXT,fetched_at TEXT,status TEXT DEFAULT 'new');
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,news_id INTEGER,content TEXT,
        hashtags TEXT,image_url TEXT,platforms TEXT,status TEXT DEFAULT 'draft',
        scheduled_at TEXT,published_at TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS publish_log(
        id INTEGER PRIMARY KEY AUTOINCREMENT,post_id INTEGER,platform TEXT,
        status TEXT,message TEXT,timestamp TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit(); conn.close()

def insert_news(item):
    conn = get_db()
    conn.execute("""INSERT OR IGNORE INTO news
        (title,link,summary,source,lang,region,category,is_cg_related,published,fetched_at,status)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (item.get("title",""),item.get("link",""),item.get("summary",""),item.get("source",""),
         item.get("lang",""),item.get("region",""),item.get("category",""),
         1 if item.get("is_cg_related") else 0,item.get("published",""),
         datetime.utcnow().isoformat(),"new"))
    conn.commit(); conn.close()

def get_news(status=None,cg_only=False,limit=200):
    conn = get_db()
    q="SELECT * FROM news WHERE 1=1"; params=[]
    if status: q+=" AND status=?"; params.append(status)
    if cg_only: q+=" AND is_cg_related=1"
    q+=" ORDER BY datetime(fetched_at) DESC LIMIT ?"; params.append(limit)
    rows=[dict(r) for r in conn.execute(q,params).fetchall()]
    conn.close(); return rows

def delete_news(nid):
    conn=get_db(); conn.execute("DELETE FROM news WHERE id=?",(nid,)); conn.commit(); conn.close()

def create_post(nid,content,hashtags,image_url,platforms,scheduled_at=None):
    conn=get_db(); c=conn.cursor()
    c.execute("""INSERT INTO posts(news_id,content,hashtags,image_url,platforms,status,scheduled_at)
        VALUES(?,?,?,?,?,?,?)""",(nid,content,hashtags,image_url,json.dumps(platforms),
        "scheduled" if scheduled_at else "draft",scheduled_at))
    pid=c.lastrowid
    if nid: conn.execute("UPDATE news SET status='used' WHERE id=?",(nid,))
    conn.commit(); conn.close(); return pid

def get_posts(status=None,limit=100):
    conn=get_db()
    q="SELECT * FROM posts"; params=[]
    if status: q+=" WHERE status=?"; params.append(status)
    q+=" ORDER BY datetime(created_at) DESC LIMIT ?"; params.append(limit)
    rows=[dict(r) for r in conn.execute(q,params).fetchall()]
    conn.close(); return rows

def update_post(pid,status=None,content=None,hashtags=None,platforms=None,scheduled_at=None):
    conn=get_db(); f=[]; p=[]
    if content is not None: f.append("content=?");p.append(content)
    if hashtags is not None: f.append("hashtags=?");p.append(hashtags)
    if platforms is not None: f.append("platforms=?");p.append(json.dumps(platforms))
    if status is not None: f.append("status=?");p.append(status)
    if scheduled_at is not None: f.append("scheduled_at=?");p.append(scheduled_at)
    if f: p.append(pid); conn.execute(f"UPDATE posts SET {','.join(f)} WHERE id=?",p); conn.commit()
    conn.close()

def delete_post(pid):
    conn=get_db(); conn.execute("DELETE FROM posts WHERE id=?",(pid,)); conn.commit(); conn.close()

def log_publish(pid,plat,status,msg):
    conn=get_db(); conn.execute("INSERT INTO publish_log(post_id,platform,status,message) VALUES(?,?,?,?)",(pid,plat,status,msg)); conn.commit(); conn.close()

def get_publish_log(limit=50):
    conn=get_db()
    rows=[dict(r) for r in conn.execute("SELECT * FROM publish_log ORDER BY datetime(timestamp) DESC LIMIT ?",(limit,)).fetchall()]
    conn.close(); return rows

def get_pending_scheduled():
    now=datetime.utcnow().isoformat()
    conn=get_db()
    rows=[dict(r) for r in conn.execute("SELECT * FROM posts WHERE status='scheduled' AND scheduled_at IS NOT NULL AND scheduled_at<=?",(now,)).fetchall()]
    conn.close(); return rows

def stats():
    conn=get_db(); c=conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM news"); t=c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM news WHERE is_cg_related=1"); cg=c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM posts WHERE status='draft'"); d=c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM posts WHERE status='scheduled'"); sc=c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM posts WHERE status='published'"); pu=c.fetchone()["n"]
    conn.close()
    return {"total_news":t,"cg_news":cg,"drafts":d,"scheduled":sc,"published":pu}


# ===========================================================================
# AGGREGATOR
# ===========================================================================
_html=re.compile(r'<[^>]+>')
def clean_html(t): return _html.sub('',t or "").strip()

def is_cg_related(title,summary):
    text=f"{title} {summary}".lower()
    return any(kw.lower() in text for kw in CG_KEYWORDS)

def auto_categorise(title,summary):
    text=f"{title} {summary}".lower()
    best,bs="General",0
    for cat,kws in CATEGORY_KEYWORDS.items():
        sc=sum(1 for k in kws if k.lower() in text)
        if sc>bs: best,bs=cat,sc
    return best

def fetch_feed(source):
    items=[]
    try:
        feed=feedparser.parse(source["url"])
        for e in feed.entries[:50]:
            title=clean_html(e.get("title",""))
            summary=clean_html(e.get("summary",e.get("description","")))
            link=e.get("link",""); pub=e.get("published",e.get("updated",""))
            if not title: continue
            cg=is_cg_related(title,summary)
            items.append({"title":title,"link":link,"summary":summary[:500],
                "source":source["name"],"lang":source.get("lang","en"),
                "region":"chhattisgarh" if cg else source.get("region","national"),
                "category":auto_categorise(title,summary),"is_cg_related":cg,"published":pub})
    except Exception as ex:
        print(f"[RSS] {source['name']}: {ex}")
    return items

def fetch_all(sources):
    total=0; cg=0
    for src in sources:
        for item in fetch_feed(src):
            insert_news(item); total+=1
            if item["is_cg_related"]: cg+=1
    return {"total_fetched":total,"cg_related":cg,"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}


# ===========================================================================
# PUBLISHER
# ===========================================================================
def _creds(key):
    cfg=load_config()
    p=cfg["platforms"].get(key,{})
    return p.get("credentials",{}),p.get("connected",False)

def _post_facebook(content,image_url=None):
    cr,cn=_creds("facebook")
    if not cn or not cr.get("page_access_token") or not cr.get("page_id"):
        return {"ok":False,"msg":"Facebook not configured. Go to Settings."}
    try:
        if image_url:
            r=requests.post(f"https://graph.facebook.com/v19.0/{cr['page_id']}/photos",
                data={"message":content,"url":image_url,"access_token":cr["page_access_token"]},timeout=30)
        else:
            r=requests.post(f"https://graph.facebook.com/v19.0/{cr['page_id']}/feed",
                data={"message":content,"access_token":cr["page_access_token"]},timeout=30)
        return {"ok":r.status_code==200,"msg":"Posted!" if r.status_code==200 else f"Error: {r.text[:150]}"}
    except Exception as e:
        return {"ok":False,"msg":f"Error: {e}"}

def _post_instagram(content,image_url=None):
    cr,cn=_creds("instagram")
    if not cn or not cr.get("access_token") or not cr.get("ig_user_id"):
        return {"ok":False,"msg":"Instagram not configured. See Setup Guide in Settings."}
    if not image_url:
        return {"ok":False,"msg":"Instagram needs an image. Create a Poster or Video first, upload it, and paste URL here."}
    try:
        r=requests.post(f"https://graph.facebook.com/v19.0/{cr['ig_user_id']}/media",
            data={"image_url":image_url,"caption":content,"access_token":cr["access_token"]},timeout=30)
        cid=r.json()
        if "id" not in cid: return {"ok":False,"msg":f"IG error: {r.text[:150]}"}
        r2=requests.post(f"https://graph.facebook.com/v19.0/{cr['ig_user_id']}/media_publish",
            data={"creation_id":cid["id"],"access_token":cr["access_token"]},timeout=30)
        return {"ok":r2.status_code==200,"msg":"Posted!" if r2.status_code==200 else f"IG error: {r2.text[:150]}"}
    except Exception as e:
        return {"ok":False,"msg":f"Error: {e}"}

def _post_twitter(content,image_url=None):
    cr,cn=_creds("twitter")
    if not cn or not cr.get("bearer_token"):
        return {"ok":False,"msg":"Twitter not configured. Go to Settings."}
    try:
        r=requests.post("https://api.twitter.com/2/tweets",
            headers={"Authorization":f"Bearer {cr['bearer_token']}","Content-Type":"application/json"},
            json={"text":content[:280]},timeout=30)
        return {"ok":r.status_code in (200,201),"msg":"Tweeted!" if r.status_code in (200,201) else f"Error: {r.text[:150]}"}
    except Exception as e:
        return {"ok":False,"msg":f"Error: {e}"}

def _post_gmail(content,subject="News Update",recipients=None,image_url=None):
    cr,cn=_creds("gmail")
    if not cn or not cr.get("app_email") or not cr.get("app_password"):
        return {"ok":False,"msg":"Gmail not configured. Go to Settings."}
    if not recipients:
        return {"ok":False,"msg":"No email recipients."}
    try:
        msg=MIMEMultipart("alternative")
        msg["From"]=cr["app_email"]
        msg["To"]=", ".join(recipients) if isinstance(recipients,list) else recipients
        msg["Subject"]=subject
        html=f"<html><body><div style='font-family:Arial;max-width:600px;margin:0 auto;padding:20px;'><h2 style='color:#1a73e8;'>{subject}</h2><hr><p>{content}</p>"
        if image_url: html+=f'<br><img src="{image_url}" style="max-width:100%;border-radius:8px;">'
        html+="<hr><p style='font-size:12px;color:#666;'>News Hub AI Agent</p></div></body></html>"
        msg.attach(MIMEText(content,"plain")); msg.attach(MIMEText(html,"html"))
        with smtplib.SMTP_SSL("smtp.gmail.com",465,timeout=30) as s:
            s.login(cr["app_email"],cr["app_password"])
            s.sendmail(cr["app_email"],recipients if isinstance(recipients,list) else [recipients],msg.as_string())
        return {"ok":True,"msg":"Email sent!"}
    except Exception as e:
        return {"ok":False,"msg":f"Error: {e}"}

_PUB={"facebook":_post_facebook,"instagram":_post_instagram,"twitter":_post_twitter,"gmail":_post_gmail}

def publish_post(post,gmail_recipients=None):
    content=post.get("content","")
    hashtags=post.get("hashtags","")
    full=f"{content}\n\n{hashtags}".strip()
    img=post.get("image_url") or None
    plats=post.get("platforms",[])
    if isinstance(plats,str): plats=json.loads(plats)
    results={}
    for p in plats:
        if p=="gmail":
            res=_post_gmail(full,subject=post.get("title","News Update")[:100],recipients=gmail_recipients or [],image_url=img)
        else:
            fn=_PUB.get(p)
            res=fn(full,img) if fn else {"ok":False,"msg":f"Unknown: {p}"}
        results[p]=res
        log_publish(post.get("id",0),p,"success" if res["ok"] else "failed",res["msg"])
    return results


# ===========================================================================
# POSTER + VIDEO GENERATOR
# ===========================================================================
THEMES = {
    "Breaking Red": {"bg":(180,20,20),"text":(255,255,255),"accent":(255,220,50),"label":"BREAKING NEWS"},
    "Dark Blue": {"bg":(15,25,50),"text":(240,245,255),"accent":(80,180,255),"label":"NEWS"},
    "Clean White": {"bg":(248,248,252),"text":(25,25,35),"accent":(200,40,40),"label":"NEWS"},
    "CG Saffron": {"bg":(255,153,51),"text":(20,20,20),"accent":(0,0,128),"label":"CHHATTISGARH NEWS"},
    "Forest Green": {"bg":(20,70,35),"text":(240,255,240),"accent":(180,255,100),"label":"NEWS"},
}

def _font(size,bold=False):
    if not HAS_PIL: return None
    for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
               "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        try: return ImageFont.truetype(fp,size)
        except: pass
    return ImageFont.load_default()

def _wrap(text,font,max_w,draw):
    words=text.split(); lines=[]; cur=[]
    for w in words:
        test=" ".join(cur+[w])
        bb=draw.textbbox((0,0),test,font=font)
        if bb[2]-bb[0]<=max_w: cur.append(w)
        else:
            if cur: lines.append(" ".join(cur))
            cur=[w]
    if cur: lines.append(" ".join(cur))
    return lines

def create_poster(headline,content,theme_name="Breaking Red",source_text=""):
    """Create 1080x1920 news poster image. Returns PIL Image."""
    if not HAS_PIL: return None
    th=THEMES.get(theme_name,THEMES["Breaking Red"])
    W,H=1080,1920
    img=Image.new("RGB",(W,H),color=th["bg"])
    draw=ImageDraw.Draw(img)
    draw.rectangle([0,0,W,130],fill=th["accent"])
    draw.text((40,35),th["label"],fill=th["bg"],font=_font(52,True))
    hf=_font(60,True); mw=W-80
    y=210
    for line in _wrap(headline,hf,mw,draw)[:8]:
        draw.text((40,y),line,fill=th["text"],font=hf); y+=75
    y+=20; draw.line([(40,y),(W-40,y)],fill=th["accent"],width=3); y+=40
    bf=_font(42)
    for line in _wrap(content[:300],bf,mw,draw)[:12]:
        draw.text((40,y),line,fill=th["text"],font=bf); y+=55
    if source_text:
        y+=20; draw.text((40,y),f"Source: {source_text}",fill=th["accent"],font=_font(34))
    draw.rectangle([0,H-90,W,H],fill=th["accent"])
    draw.text((40,H-68),"Chhattisgarh News Hub",fill=th["bg"],font=_font(36,True))
    return img

def poster_bytes(img):
    buf=io.BytesIO(); img.save(buf,format="PNG"); return buf.getvalue()

def generate_video(headline, content, theme_name="Breaking Red",
                   use_voice=True, lang="hi", duration_sec=30):
    """Generate news video (MP4) using FFmpeg directly.
    Returns path to video file, or error dict.
    """
    if not HAS_PIL:
        return {"ok":False,"msg":"Pillow not installed"}
    if not HAS_FFMPEG:
        return {"ok":False,"msg":"FFmpeg not available. Check requirements.txt has imageio-ffmpeg."}

    tmpdir = tempfile.mkdtemp()
    th = THEMES.get(theme_name, THEMES["Breaking Red"])

    try:
        # 1. Create poster frames
        head_img = create_poster(headline, "", theme_name)
        head_path = os.path.join(tmpdir, "frame1.png")
        head_img.save(head_path)

        body_img = create_poster("", content[:200], theme_name)
        body_path = os.path.join(tmpdir, "frame2.png")
        body_img.save(body_path)

        end_img = create_poster("Follow Us", "@ChhattisgarhNewsHub", theme_name)
        end_path = os.path.join(tmpdir, "frame3.png")
        end_img.save(end_path)

        # 2. Generate AI voice if requested
        audio_args = []
        if use_voice and HAS_GTTS:
            voice_text = f"{headline}. {content}"
            tts = gTTS(text=voice_text, lang=lang, slow=False)
            audio_path = os.path.join(tmpdir, "voice.mp3")
            tts.save(audio_path)
            audio_args = ["-i", audio_path]

        # 3. Determine segment durations
        if use_voice and HAS_GTTS:
            # Use ffprobe to get audio duration
            try:
                probe = subprocess.run(
                    [FFMPEG_PATH.replace("ffmpeg","ffprobe") if os.path.exists(FFMPEG_PATH.replace("ffmpeg","ffprobe")) 
                     else FFMPEG_PATH, "-i", audio_path, "-show_entries","format=duration",
                     "-v","quiet","-of","csv=p=0"],
                    capture_output=True, text=True, timeout=10)
                audio_dur = float(probe.stdout.strip())
                total_dur = max(audio_dur + 2, 10)
            except:
                total_dur = duration_sec
        else:
            total_dur = max(duration_sec, 10)

        d1 = total_dur * 0.4  # headline
        d2 = total_dur * 0.4  # content
        d3 = total_dur * 0.2  # end card

        # 4. Build video with FFmpeg
        output_path = os.path.join(tmpdir, "news_video.mp4")

        # Concatenate frames into video using FFmpeg
        # Create a concat file listing frames with durations
        concat_path = os.path.join(tmpdir, "concat.txt")
        with open(concat_path, "w") as f:
            f.write(f"file '{head_path}'\nduration {d1}\n")
            f.write(f"file '{body_path}'\nduration {d2}\n")
            f.write(f"file '{end_path}'\nduration {d3}\n")
            f.write(f"file '{end_path}'\n")  # last frame needs repeat

        cmd = [FFMPEG_PATH, "-y",
               "-f", "concat", "-safe", "0", "-i", concat_path,
               "-vf", "fps=24,scale=1080:1920",
               "-c:v", "libx264", "-pix_fmt", "yuv420p"]

        if audio_args:
            cmd += audio_args
            cmd += ["-c:a", "aac", "-shortest"]
            cmd += ["-map", "0:v:0", "-map", "1:a:0"]

        cmd += [output_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            # Try simpler command without audio mapping
            cmd2 = [FFMPEG_PATH, "-y", "-f", "concat", "-safe", "0", "-i", concat_path,
                    "-vf", "fps=24,scale=1080:1920", "-c:v", "libx264", "-pix_fmt", "yuv420p"]
            if audio_args:
                cmd2 += audio_args + ["-c:a", "aac", "-shortest"]
            cmd2 += [output_path]
            result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
            if result2.returncode != 0:
                return {"ok":False,"msg":f"FFmpeg error: {result2.stderr[:200]}"}

        if not os.path.exists(output_path):
            return {"ok":False,"msg":"Video file not created"}

        return {"ok":True,"path":output_path,"duration":total_dur}

    except Exception as e:
        return {"ok":False,"msg":f"Video error: {e}"}


# ===========================================================================
# STREAMLIT APP
# ===========================================================================
st.set_page_config(page_title="News Hub AI Agent", page_icon="📰", layout="wide",
                   initial_sidebar_state="expanded")

init_db()
cfg = load_config()

# --- DB namespace ---
class _DB:
    init_db=staticmethod(init_db)
    stats=staticmethod(stats)
    get_news=staticmethod(get_news)
    insert_news=staticmethod(insert_news)
    delete_news=staticmethod(delete_news)
    create_post=staticmethod(create_post)
    get_posts=staticmethod(get_posts)
    update_post=staticmethod(update_post)
    delete_post=staticmethod(delete_post)
    log_publish=staticmethod(log_publish)
    get_publish_log=staticmethod(get_publish_log)
    get_pending_scheduled=staticmethod(get_pending_scheduled)
    get_db=staticmethod(get_db)
db=_DB()
db.init_db()
cfg=load_config()

# --- Sidebar ---
st.sidebar.markdown("## 📰 News Hub AI Agent")
st.sidebar.caption("Chhattisgarh → Social Media")
st.sidebar.markdown("---")

page = st.sidebar.radio("Menu", [
    "Dashboard","News Feed","Post Editor",
    "Poster Studio","Video Studio",
    "Scheduled Posts","History","Settings"],
    label_visibility="collapsed")


# ===========================================================================
# DASHBOARD - Simple & Clean
# ===========================================================================
if page == "Dashboard":
    st.markdown("# 📊 Dashboard")
    st.markdown("---")

    s = db.stats()
    c1, c2, c3 = st.columns(3)
    c1.metric("📰 Total News", s["total_news"])
    c2.metric("🏷️ CG-Related", s["cg_news"])
    c3.metric("📤 Published", s["published"])

    st.markdown("---")
    st.markdown("### 🚀 Quick Start")
    st.markdown("1️⃣ Click **Fetch News** below to collect latest Chhattisgarh news")
    st.markdown("2️⃣ Go to **News Feed** to browse and select news")
    st.markdown("3️⃣ Go to **Poster Studio** or **Video Studio** to create content")
    st.markdown("4️⃣ Go to **Post Editor** to publish to social media")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📡 Fetch Latest News", use_container_width=True, type="primary"):
            with st.spinner("Fetching from all RSS sources..."):
                result = fetch_all(cfg["rss_sources"])
            st.success(f"✅ Fetched {result['total_fetched']} articles ({result['cg_related']} CG-related)")
            st.rerun()
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.markdown("### 📌 Platform Status")
    for key, p in cfg["platforms"].items():
        cn = p.get("connected", False)
        status = "🟢 Connected" if cn else "🔴 Not Connected"
        st.markdown(f"**{p['name']}** — {status}  |  _{p.get('notes','')}_")


# ===========================================================================
# NEWS FEED
# ===========================================================================
elif page == "News Feed":
    st.markdown("# 📡 News Feed")
    st.markdown("---")

    tb1, tb2, tb3 = st.columns([1, 1, 2])
    with tb1:
        if st.button("📡 Fetch News", use_container_width=True):
            with st.spinner("Fetching..."):
                result = fetch_all(cfg["rss_sources"])
            st.success(f"Fetched {result['total_fetched']} articles ({result['cg_related']} CG-related)")
            st.rerun()
    with tb2:
        cg_filter = st.checkbox("CG only", value=False)
    with tb3:
        search = st.text_input("🔍 Search", placeholder="Keyword...")

    st.markdown("---")
    news = db.get_news(limit=200)
    if cg_filter:
        news = [n for n in news if n["is_cg_related"]]
    if search:
        sl = search.lower()
        news = [n for n in news if sl in n["title"].lower() or sl in n["summary"].lower()]

    if not news:
        st.info("No news found. Click 'Fetch News' to pull latest articles.")
    else:
        st.caption(f"Showing {len(news)} articles")
        for item in news:
            cg_tag = "🏷️ CG" if item["is_cg_related"] else "🌐"
            with st.expander(f"{cg_tag}  {item['title'][:80]} — _{item['source']}_"):
                st.markdown(f"**Category:** {item['category']}  |  **Status:** {item['status']}")
                st.markdown(f"**Summary:** {item['summary']}")
                st.markdown(f"[🔗 Read Full Article]({item['link']})")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    if st.button("✍️ Post", key=f"cr_{item['id']}"):
                        st.session_state["edit_news_id"] = item["id"]
                        st.session_state["edit_title"] = item["title"]
                        st.session_state["edit_summary"] = item["summary"]
                        st.info("👆 Go to 'Post Editor'")
                with c2:
                    if st.button("🎨 Poster", key=f"po_{item['id']}"):
                        st.session_state["poster_headline"] = item["title"]
                        st.session_state["poster_content"] = item["summary"]
                        st.session_state["poster_source"] = item["source"]
                        st.info("👆 Go to 'Poster Studio'")
                with c3:
                    if st.button("🎬 Video", key=f"vi_{item['id']}"):
                        st.session_state["video_headline"] = item["title"]
                        st.session_state["video_content"] = item["summary"]
                        st.session_state["video_source"] = item["source"]
                        st.info("👆 Go to 'Video Studio'")
                with c4:
                    if st.button("🗑️", key=f"dl_{item['id']}"):
                        db.delete_news(item["id"])
                        st.rerun()


# ===========================================================================
# POST EDITOR
# ===========================================================================
elif page == "Post Editor":
    st.markdown("# ✍️ Post Editor")
    st.markdown("---")

    if "edit_news_id" not in st.session_state:
        st.session_state["edit_news_id"] = None
        st.session_state["edit_title"] = ""
        st.session_state["edit_summary"] = ""

    title = st.text_input("Title", value=st.session_state.get("edit_title", ""))
    content = st.text_area("Content", value=st.session_state.get("edit_summary", ""), height=150)

    ca, cb = st.columns(2)
    with ca:
        hashtags = st.text_input("Hashtags", value=cfg["settings"].get("default_hashtags", "#ChhattisgarhNews #CGNews #News"))
    with cb:
        image_url = st.text_input("Image URL (optional)", placeholder="https://...")

    st.markdown("### Select Platforms")
    selected = []
    pc = st.columns(len(cfg["platforms"]))
    for i, (key, p) in enumerate(cfg["platforms"].items()):
        with pc[i]:
            cn = p.get("connected", False)
            label = p["name"]
            if not cn: label += " ⚠️"
            if st.checkbox(label, key=f"pl_{key}", help=p.get("notes", "")):
                selected.append(key)

    st.markdown("### Schedule")
    schedule_now = st.checkbox("Publish immediately", value=True)
    scheduled_at = None
    if not schedule_now:
        sd, stt = st.columns(2)
        with sd: schedule_date = st.date_input("Date", min_value=datetime.now().date())
        with stt: schedule_time = st.time_input("Time", value=datetime.now().time())
        scheduled_at = datetime.combine(schedule_date, schedule_time).isoformat()

    st.markdown("---")
    a1, a2, a3 = st.columns(3)
    with a1:
        if st.button("💾 Save Draft", use_container_width=True):
            if content:
                pid = db.create_post(st.session_state.get("edit_news_id"), content, hashtags, image_url, selected, scheduled_at if scheduled_at else None)
                st.success(f"Saved (ID: {pid})")
                st.rerun()
            else: st.warning("Empty!")
    with a2:
        if st.button("📅 Schedule", use_container_width=True):
            if content and selected and scheduled_at:
                pid = db.create_post(st.session_state.get("edit_news_id"), content, hashtags, image_url, selected, scheduled_at)
                st.success(f"Scheduled for {scheduled_at}")
                st.rerun()
            else: st.warning("Need content, platforms & date/time.")
    with a3:
        if st.button("🚀 Publish Now", use_container_width=True, type="primary"):
            if not content: st.warning("Empty!")
            elif not selected: st.warning("Select platform.")
            else:
                post = {"id":0,"title":title,"content":content,"hashtags":hashtags,"image_url":image_url,"platforms":selected}
                with st.spinner("Publishing..."):
                    results = publish_post(post)
                for plat, res in results.items():
                    if res["ok"]: st.success(f"✅ {plat.title()}: {res['msg']}")
                    else: st.error(f"❌ {plat.title()}: {res['msg']}")


# ===========================================================================
# POSTER STUDIO
# ===========================================================================
elif page == "Poster Studio":
    st.markdown("# 🎨 Poster Studio")
    st.markdown("Create news poster images (1080x1920) for Instagram, Facebook, WhatsApp.")
    st.markdown("---")

    if not HAS_PIL:
        st.error("Pillow not installed. Add 'Pillow' to requirements.txt")
    else:
        ph = st.text_input("Headline", value=st.session_state.get("poster_headline", ""), placeholder="News headline...")
        pc = st.text_area("Content", value=st.session_state.get("poster_content", ""), height=100, placeholder="News content...")
        ps = st.text_input("Source", value=st.session_state.get("poster_source", ""), placeholder="e.g. Patrika")
        pt = st.selectbox("Theme", list(THEMES.keys()))

        if ph:
            st.markdown("---")
            st.markdown("### 👀 Preview")
            img = create_poster(ph, pc, pt, ps)
            if img:
                bts = poster_bytes(img)
                st.image(bts, caption="News Poster (1080x1920)", use_column_width=True)
                st.download_button("📥 Download PNG", data=bts,
                    file_name=f"poster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    mime="image/png", use_container_width=True)
        else:
            st.info("Enter a headline to see preview.")


# ===========================================================================
# VIDEO STUDIO
# ===========================================================================
elif page == "Video Studio":
    st.markdown("# 🎬 Video Studio")
    st.markdown("Create 30-60 second news videos for Instagram Reels, YouTube Shorts, Facebook.")
    st.markdown("---")

    # Dependency status
    dc1, dc2, dc3 = st.columns(3)
    dc1.metric("Pillow", "✅" if HAS_PIL else "❌")
    dc2.metric("FFmpeg", "✅" if HAS_FFMPEG else "❌")
    dc3.metric("gTTS Voice", "✅" if HAS_GTTS else "❌")

    if not HAS_FFMPEG:
        st.warning("FFmpeg not found. Make sure 'imageio-ffmpeg' is in requirements.txt")
        st.markdown("---")

    st.markdown("### 📝 News Content")
    vh = st.text_input("Headline", value=st.session_state.get("video_headline", ""), placeholder="News headline...")
    vc = st.text_area("Content (will be spoken in video)", value=st.session_state.get("video_content", ""), height=100, placeholder="Full news content...")

    st.markdown("### 🎨 Style")
    vs1, vs2, vs3 = st.columns(3)
    with vs1:
        vt = st.selectbox("Theme", list(THEMES.keys()))
    with vs2:
        use_voice = st.checkbox("AI Hindi Voice", value=True)
    with vs3:
        vl = st.selectbox("Language", ["hi","en"], index=0) if use_voice else st.selectbox("Language", ["hi","en"], index=0, disabled=True)

    st.markdown("### ⏱️ Duration")
    vdur = st.slider("Video length (seconds)", min_value=15, max_value=90, value=30, step=5)

    if vh and HAS_PIL:
        st.markdown("---")
        st.markdown("### 👀 Frame Preview")
        preview = create_poster(vh, vc[:80], vt, st.session_state.get("video_source", ""))
        if preview:
            st.image(poster_bytes(preview), caption="Preview frame", use_column_width=True)

    st.markdown("---")
    if st.button("🎬 Generate Video", type="primary", use_container_width=True, disabled=not vh):
        if not vh:
            st.warning("Enter headline!")
        elif not HAS_PFMPEG and not HAS_FFMPEG:
            st.error("FFmpeg not available.")
        else:
            with st.spinner("Generating video... (1-2 minutes)"):
                result = generate_video(vh, vc or vh, vt, use_voice, vl if use_voice else "hi", vdur)
            if result.get("ok"):
                st.success(f"✅ Video created! Duration: {result.get('duration',0):.0f}s")
                with open(result["path"], "rb") as f:
                    vbytes = f.read()
                st.video(vbytes)
                st.download_button("📥 Download MP4", data=vbytes,
                    file_name=f"news_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                    mime="video/mp4", use_container_width=True)
            else:
                st.error(f"❌ {result.get('msg','Unknown error')}")


# ===========================================================================
# SCHEDULED POSTS
# ===========================================================================
elif page == "Scheduled Posts":
    st.markdown("# 📅 Scheduled Posts")
    st.markdown("---")

    tab1, tab2 = st.tabs(["📋 Drafts", "📅 Scheduled"])

    with tab1:
        drafts = db.get_posts("draft")
        if not drafts:
            st.info("No drafts. Create from Post Editor.")
        for post in drafts:
            plats = json.loads(post["platforms"]) if post["platforms"] else []
            with st.expander(f"📝 {post['content'][:60]}..."):
                st.markdown(f"**Content:** {post['content']}")
                st.markdown(f"**Platforms:** {', '.join(plats)}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🚀 Publish", key=f"pd_{post['id']}"):
                        pd = {"id":post["id"],"title":"News","content":post["content"],
                              "hashtags":post["hashtags"],"image_url":post["image_url"],"platforms":plats}
                        with st.spinner("Publishing..."):
                            results = publish_post(pd)
                        for plat, res in results.items():
                            if res["ok"]: st.success(f"✅ {plat.title()}: {res['msg']}")
                            else: st.error(f"❌ {plat.title()}: {res['msg']}")
                        db.update_post(post["id"], status="published")
                        st.rerun()
                with c2:
                    if st.button("🗑️ Delete", key=f"dd_{post['id']}"):
                        db.delete_post(post["id"])
                        st.rerun()

    with tab2:
        scheduled = db.get_posts("scheduled")
        if not scheduled:
            st.info("No scheduled posts.")
        for post in scheduled:
            plats = json.loads(post["platforms"]) if post["platforms"] else []
            try:
                dt = datetime.fromisoformat(post["scheduled_at"])
                rem = dt - datetime.now()
                rstr = f"⏳ {rem}" if rem.total_seconds() > 0 else "⏰ Due"
            except: rstr = ""
            with st.expander(f"📅 {post['content'][:60]}... {rstr}"):
                st.markdown(f"**Content:** {post['content']}")
                st.markdown(f"**Scheduled:** {post['scheduled_at']}")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("🚀 Publish", key=f"ps_{post['id']}"):
                        pd = {"id":post["id"],"title":"News","content":post["content"],
                              "hashtags":post["hashtags"],"image_url":post["image_url"],"platforms":plats}
                        with st.spinner("Publishing..."):
                            results = publish_post(pd)
                        for plat, res in results.items():
                            if res["ok"]: st.success(f"✅ {plat.title()}: {res['msg']}")
                            else: st.error(f"❌ {plat.title()}: {res['msg']}")
                        db.update_post(post["id"], status="published")
                        st.rerun()
                with c2:
                    if st.button("✏️ Draft", key=f"es_{post['id']}"):
                        db.update_post(post["id"], status="draft")
                        st.rerun()

        st.markdown("---")
        pending = db.get_pending_scheduled()
        if pending:
            st.warning(f"{len(pending)} post(s) due!")
            if st.button("🚀 Publish All Due", type="primary"):
                for post in pending:
                    plats = json.loads(post["platforms"]) if post["platforms"] else []
                    pd = {"id":post["id"],"title":"News","content":post["content"],
                          "hashtags":post["hashtags"],"image_url":post["image_url"],"platforms":plats}
                    results = publish_post(pd)
                    for plat, res in results.items():
                        if res["ok"]: st.success(f"✅ Post {post['id']} → {plat}")
                        else: st.error(f"❌ Post {post['id']} → {plat}: {res['msg']}")
                    db.update_post(post["id"], status="published")
                st.rerun()
        else:
            st.success("No posts due.")


# ===========================================================================
# HISTORY
# ===========================================================================
elif page == "History":
    st.markdown("# 📤 Publish History")
    st.markdown("---")
    logs = db.get_publish_log(100)
    if not logs:
        st.info("No history yet.")
    else:
        for log in logs:
            icon = "✅" if log["status"] == "success" else "❌"
            st.markdown(f"{icon} **{log['platform'].title()}** (Post #{log['post_id']}) — {log['message'][:80]}")


# ===========================================================================
# SETTINGS
# ===========================================================================
elif page == "Settings":
    st.markdown("# ⚙️ Settings")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["🔑 Credentials", "📷 Instagram Guide", "📡 RSS Sources"])

    with tab1:
        st.markdown("### Platform Credentials")
        for key, p in cfg["platforms"].items():
            st.markdown(f"#### {p['name']}")
            st.caption(p.get("notes", ""))
            cn = st.checkbox("Connected", value=p.get("connected", False), key=f"c_{key}")
            p["connected"] = cn
            for ck, cv in p["credentials"].items():
                if "password" in ck or "secret" in ck or "token" in ck:
                    p["credentials"][ck] = st.text_input(ck, value=cv, type="password", key=f"k_{key}_{ck}")
                else:
                    p["credentials"][ck] = st.text_input(ck, value=cv, key=f"k_{key}_{ck}")
            st.markdown("---")
        if st.button("💾 Save All", type="primary"):
            save_config(cfg)
            st.success("Saved!")

    with tab2:
        st.markdown("# 📷 Instagram Setup Guide")
        st.markdown("Instagram ko link karne ke liye ye steps follow karein:")
        st.markdown("---")

        st.markdown("### Step 1: Instagram Business Account")
        st.markdown("1. Instagram app → Settings → Account type")
        st.markdown("2. **Switch to Professional Account** → select **Business**")
        st.markdown("---")

        st.markdown("### Step 2: Link Instagram to Facebook Page")
        st.markdown("1. Facebook app → apna Page kholo")
        st.markdown("2. Settings → Linked Accounts → Instagram")
        st.markdown("3. Apna Instagram Business account link karo")
        st.markdown("---")

        st.markdown("### Step 3: Facebook Developer App")
        st.markdown("1. **developers.facebook.com** pe jao")
        st.markdown("2. **My Apps** → **Create App** → type: **Business**")
        st.markdown("3. App naam do (e.g. News Hub)")
        st.markdown("4. **Pages** product add karo")
        st.markdown("---")

        st.markdown("### Step 4: Access Token")
        st.markdown("1. Graph API Explorer mein jao")
        st.markdown("2. Apna Facebook Page select karo")
        st.markdown("3. Permissions: `pages_manage_posts`, `instagram_basic`, `instagram_content_publish`")
        st.markdown("4. **Generate Access Token** → copy karo")
        st.markdown("---")

        st.markdown("### Step 5: Instagram User ID")
        st.markdown("Graph API Explorer mein ye query run karo:")
        st.code("GET /me/accounts?fields=instagram_business_account")
        st.markdown("IG User ID milega → copy karo")
        st.markdown("---")

        st.markdown("### Step 6: App mein daalo")
        st.markdown("1. **Credentials** tab mein jao")
        st.markdown("2. Instagram section:")
        st.markdown("   - **access_token** = Step 4 ka token")
        st.markdown("   - **ig_user_id** = Step 5 ka ID")
        st.markdown("3. **Connected** checkbox tick karo")
        st.markdown("4. **Save All** button dabao")
        st.markdown("---")

        st.markdown("### ⚠️ Important")
        st.markdown("- Instagram ke liye **image zaroori hai**")
        st.markdown("- Poster Studio se poster banao, ya Video Studio se video banao")
        st.markdown("- Poster/Video download karke kisi image host (imgur) pe upload karo")
        st.markdown("- Uska URL Post Editor mein daalo, Instagram select karke publish karo")
        st.markdown("---")

        st.markdown("### ✅ Checklist")
        st.markdown("- [ ] Instagram Business account")
        st.markdown("- [ ] FB Page linked to Instagram")
        st.markdown("- [ ] Facebook Developer App created")
        st.markdown("- [ ] Access Token generated")
        st.markdown("- [ ] IG User ID obtained")
        st.markdown("- [ ] Credentials saved in app")
        st.markdown("- [ ] Connected checkbox ticked")

    with tab3:
        st.markdown("### RSS Sources")
        sources = cfg.get("rss_sources", [])
        for i, src in enumerate(sources):
            c1, c2, c3, c4 = st.columns([3, 3, 1, 1])
            with c1: src["name"] = st.text_input("Name", value=src["name"], key=f"n_{i}")
            with c2: src["url"] = st.text_input("URL", value=src["url"], key=f"u_{i}")
            with c3: src["lang"] = st.selectbox("Lang", ["hi","en"], index=0 if src["lang"]=="hi" else 1, key=f"l_{i}")
            with c4:
                if st.button("🗑️", key=f"d_{i}"):
                    sources.pop(i)
                    cfg["rss_sources"] = sources
                    save_config(cfg)
                    st.rerun()

        st.markdown("---")
        nc1, nc2, nc3 = st.columns([3, 3, 2])
        with nc1: nn = st.text_input("New Name", key="nn")
        with nc2: nu = st.text_input("New URL", key="nu")
        with nc3: nl = st.selectbox("Lang", ["hi","en"], key="nl")
        if st.button("➕ Add Source"):
            if nn and nu:
                sources.append({"name":nn,"url":nu,"lang":nl,"region":"national"})
                cfg["rss_sources"] = sources
                save_config(cfg)
                st.success(f"Added: {nn}")
                st.rerun()

        st.markdown("---")
        if st.button("💾 Save All Sources"):
            cfg["rss_sources"] = sources
            save_config(cfg)
            st.success("Saved!")

        st.markdown("---")
        st.markdown("### 🗄️ Database")
        dc1, dc2 = st.columns(2)
        with dc1:
            if st.button("🗑️ Clear News"):
                conn = db.get_db()
                conn.execute("DELETE FROM news"); conn.commit(); conn.close()
                st.success("Cleared!"); st.rerun()
        with dc2:
            if st.button("🗑️ Clear Posts"):
                conn = db.get_db()
                conn.execute("DELETE FROM posts"); conn.execute("DELETE FROM publish_log")
                conn.commit(); conn.close()
                st.success("Cleared!"); st.rerun()
