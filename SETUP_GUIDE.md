# 📰 News Hub AI Agent — Chhattisgarh News → Social Media

A free, powerful, all-in-one tool to collect Chhattisgarh & national news from RSS feeds,
filter relevant stories, edit them, and publish to **Facebook, Instagram, Twitter/X, YouTube, and Gmail** —
all from one dashboard.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📡 **News Aggregation** | Fetches news from 10+ RSS sources (Patrika, Bhaskar, NDTV, Aaj Tak, BBC Hindi, etc.) |
| 🏷️ **CG Filter** | Auto-detects Chhattisgarh-related news using 40+ keywords (Hindi & English) |
| 📂 **Auto-Categorise** | Tags news as Politics, Crime, Business, Education, Sports, Health, Agriculture |
| ✍️ **Post Editor** | Full editing control — content, hashtags, image URL, platform selection |
| 📅 **Scheduling** | Schedule posts for specific date/time; auto-publisher runs due posts |
| 📤 **Multi-Platform Publishing** | Facebook, Instagram, Twitter/X, YouTube, Gmail — from one place |
| 📊 **Dashboard** | Stats, platform connection status, recent publish log |
| 📤 **Publish History** | Full log of every publish attempt with success/failure status |
| ⚙️ **Settings** | Add/remove RSS sources, configure API credentials, manage database |
| 💾 **Offline Storage** | SQLite database — no cloud dependency, your data stays on your machine |
| 🆓 **100% Free** | Uses only free APIs and open-source tools |

---

## 🚀 Installation (5 Minutes)

### Requirements
- Python 3.10 or higher
- Internet connection (for RSS fetching and publishing)

### Steps

```bash
# 1. Unzip the project
unzip newsagent.zip
cd newsagent

# 2. Create a virtual environment (recommended)
python -m venv venv

# 3. Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 🔑 Platform Setup Guide

Each platform needs API credentials. Here's how to get them (all free):

### 📘 Facebook
1. Go to https://developers.facebook.com/
2. Create a new App → type: "Business"
3. Add "Pages" product
4. Go to Graph API Explorer → generate a **Page Access Token**
5. Get your **Page ID** from your Facebook Page's "About" section
6. Enter both in Settings → Facebook

### 📸 Instagram
1. You need a **Business/Creator Instagram account** linked to a Facebook Page
2. Use the same Facebook App from above
3. Go to Graph API Explorer → get `instagram_basic` + `pages_show_list` permissions
4. Get your **IG User ID** from the API: `GET /me/accounts?fields=instagram_business_account`
5. Enter IG User ID + Access Token in Settings → Instagram

### 🐦 Twitter / X
1. Go to https://developer.x.com/
2. Sign up for a **Free account** (allows 1,500 posts/month)
3. Create a Project and App
4. Generate **Bearer Token** (and optionally API keys for OAuth 1.0a)
5. Enter Bearer Token in Settings → Twitter

### ▶️ YouTube
1. Go to https://console.cloud.google.com/
2. Create a project → enable **YouTube Data API v3**
3. Create an API key
4. Enter API Key in Settings → YouTube
5. Note: For posting community posts, you'll need OAuth2 setup (more advanced)

### ✉️ Gmail (Newsletter)
1. Go to your Google Account → Security
2. Enable 2-Step Verification
3. Go to "App Passwords" → generate a new app password
4. Use your Gmail address + the app password in Settings → Gmail
5. When publishing, specify recipient email addresses

---

## 📖 How to Use

### Step 1: Fetch News
- Go to **Dashboard** → click "Fetch Latest News"
- Or go to **News Feed** → click "Fetch News Now"
- News is automatically filtered and tagged

### Step 2: Review & Filter
- In **News Feed**, browse collected articles
- Filter by CG-related, category, or search by keyword
- Click on any article to expand and read summary

### Step 3: Create Post
- Click "Create Post" on any news item
- Go to **Post Editor** — edit content, add hashtags, select platforms
- Preview your post before publishing

### Step 4: Publish or Schedule
- **Publish Now**: Immediately posts to selected platforms
- **Schedule**: Pick a date/time, save as scheduled
- Go to **Scheduled Posts** tab to manage and auto-publish due posts

### Step 5: Monitor
- Check **Publish History** for success/failure logs
- Dashboard shows stats and platform status

---

## 🏗️ Project Structure

```
newsagent/
├── app.py                    # Main Streamlit dashboard
├── requirements.txt          # Python dependencies
├── SETUP_GUIDE.md           # This file
├── modules/
│   ├── __init__.py
│   ├── config.py             # RSS sources, platform config, keywords
│   ├── database.py           # SQLite database layer
│   ├── aggregator.py         # RSS fetcher, filterer, categoriser
│   └── publisher.py          # Multi-platform publishing
└── data/
    ├── news_hub.db           # SQLite database (auto-created)
    └── config.json           # User configuration (auto-created)
```

---

## 🔧 Adding More RSS Sources

Go to **Settings → RSS Sources** tab. You can:
- Add any RSS/Atom feed URL
- Set language (hi/en) and region (chhattisgarh/national/business/tech)
- Sources are saved permanently

**Good Chhattisgarh news sources to add:**
- Patrika CG: `https://www.patrika.com/rss/chhattisgarh-news.xml`
- Bhaskar CG: `https://www.bhaskar.com/rss-feed/1061/`
- Amar Ujala CG: `https://www.amarujala.com/rss/chhattisgarh`
- Naya India CG: search for "chhattisgarh rss feed"

---

## 💡 Tips for Better Results

1. **Fetch regularly**: Run "Fetch News" every 30-60 minutes during the day
2. **CG filter first**: Check "CG-related only" to focus on local news
3. **Add hashtags**: Use relevant hashtags like `#ChhattisgarhNews #CGNews #Raipur`
4. **Schedule strategically**: Post during peak hours (8-10 AM, 12-2 PM, 7-9 PM)
5. **Edit before publishing**: Always review and edit the auto-generated content
6. **Use images**: Instagram requires an image URL; add one for better engagement

---

## 🆓 Cost: ₹0

This tool uses:
- **Streamlit** (free, open-source) for the dashboard
- **SQLite** (free, built into Python) for storage
- **feedparser** (free, open-source) for RSS
- **Platform APIs** (all have free tiers):
  - Facebook Graph API: Free
  - Instagram Graph API: Free
  - Twitter/X API Free tier: 1,500 posts/month
  - YouTube Data API: Free (10,000 units/day)
  - Gmail SMTP: Free with App Password

---

## ❓ Troubleshooting

**App won't start?**
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again

**No news appearing?**
- Check your internet connection
- Some RSS feeds may be temporarily down — try fetching again
- Add alternative RSS sources in Settings

**Facebook publish fails?**
- Ensure you're using a **Page Access Token** (not a User Token)
- Tokens expire — regenerate if needed
- Check that your app has `pages_manage_posts` permission

**Instagram publish fails?**
- Instagram requires an image URL — make sure you added one
- Your Instagram account must be Business/Creator type
- Must be linked to a Facebook Page

**Twitter publish fails?**
- Free tier allows 1 post per 24 hours
- Make sure the Bearer Token is correct
- Content must be ≤280 characters

**Gmail fails?**
- Use App Password, not your regular password
- Enable 2-Step Verification first
- Check recipient email addresses are valid

---

## 📞 Need Help?

This is your personal News Hub AI Agent. Experiment with it, add your own RSS sources,
and customize it for your news channel's needs. The entire codebase is open and editable.

**Built for Chhattisgarh news creators. Free forever.**
