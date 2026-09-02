# ☁️ Cloud Deploy Guide — News Hub AI Agent

## App ko cloud pe deploy karne ke 3 steps hain:

---

## STEP 1: GitHub account banao (2 minute)

1. Browser mein jao: **github.com**
2. **Sign Up** pe click karo
3. Email, password daalo, account banao
4. Email verify kar lo

**Agar pehle se GitHub account hai toh STEP 2 pe jao.**

---

## STEP 2: Code ko GitHub pe upload karo (5 minute)

### Option A: Web browser se (sabse aasaan — tablet se bhi ho jayega)

1. GitHub.com pe login karo
2. Upar right mein **+** icon → **New repository** pe click karo
3. Repository naam do: `news-hub-ai-agent`
4. **Public** select karo (free cloud deploy ke liye public chahiye)
5. **Create repository** pe click karo
6. Ab **uploading an existing file** link pe click karo (neche dikhega)
7. NewsHubAI_Agent.zip ke andar jo files hain — unhe drag-drop kar do:
   - `app.py`
   - `requirements.txt`
   - `SETUP_GUIDE.md`
   - `modules/` folder (config.py, database.py, aggregator.py, publisher.py, __init__.py)
   - `.streamlit/config.toml`
   - `.gitignore`
8. Upar **Commit changes** pe click karo

**Zip ke andar se sab files pehle extract kar lo, phir individual files upload karo.**

### Option B: Terminal se (agar computer available hai)

```bash
# Zip extract karo
unzip NewsHubAI_Agent.zip
cd newsagent

# Git init aur push
git init
git add .
git commit -m "News Hub AI Agent"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/news-hub-ai-agent.git
git push -u origin main
```

---

## STEP 3: Streamlit Cloud pe deploy karo (3 minute)

1. Browser mein jao: **share.streamlit.io**
2. **Sign in with GitHub** (same GitHub account se)
3. Authorize karne do
4. **New app** pe click karo
5. Ye details bharo:
   - **Repository**: Apna GitHub username select karo → `news-hub-ai-agent`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App name**: `news-hub-ai-agent` (ya jo bhi naam chaho)
6. **Deploy!** pe click karo

### Deploy hone ke baad:

- 2-3 minute mein app live ho jayegi
- URL milega jaise: `https://your-username-news-hub-ai-agent.streamlit.app`
- Ye URL bookmark kar lo
- Tablet/phone/computer — kahin se bhi khol sakte ho

### Deploy ke baad Settings pe jao aur platform credentials daalo:

- Facebook: Page ID + Page Access Token
- Instagram: IG User ID + Access Token
- Twitter: Bearer Token
- YouTube: API Key
- Gmail: Email + App Password

---

## ⚠️ Important Cloud Notes

### SQLite limitation:
Streamlit Cloud pe jab bhi app restart hogi (ya 7 din baad automatic restart hoga), toh SQLite database clear ho jayegi. Ye free cloud ka limitation hai.

### Iska solution:
- **Short term**: News regularly publish kar lo, data delete ho bhi toh posts already published hain
- **Long term**: Agar chahiye toh baad mein free PostgreSQL (Supabase.com) connect kar sakte hain — main ye bhi setup karwa dunga

### Streamlit Cloud free tier:
- 1 GB RAM
- App 7 din mein ek baar automatically restart hoti hai
- Sahi hai testing aur personal use ke liye

---

## 🔄 App Update Kaise Karo

Agar code mein kuch change karna ho:

1. GitHub pe file edit karo (web interface se)
2. Commit karo
3. Streamlit Cloud pe automatically update ho jayegi (3-5 minute)
4. Ya Streamlit Cloud dashboard mein jake **Reboot** pe click karo

---

## 📞 Troubleshooting Cloud Issues

**"Module not found" error?**
- GitHub pe `requirements.txt` upload hua hai na? Check karo

**App deploy nahi ho rahi?**
- Repository **public** hai na? Private repo ke liye Streamlit Pro chahiye
- `app.py` root folder mein hai na? `modules/` folder bhi same level pe?

**"Port already in use" error?**
- Streamlit Cloud dashboard → **Settings** → **Reboot**

**App slow hai?**
- Free tier mein 1 GB RAM hai, heavy data mein slow ho sakti hai
- News fetch karte time 50-100 articles tak limit rakho

---

## ✅ Checklist

- [ ] GitHub account bana
- [ ] Repository `news-hub-ai-agent` bana (public)
- [ ] Sab files upload kar
- [ ] share.streamlit.io pe jao
- [ ] Deploy kar
- [ ] URL save kar
- [ ] Settings mein platform credentials daalo
- [ ] "Fetch News Now" pe click kar
- [ ] News feed check karo
- [ ] Post editor mein post banao
- [ ] Publish karo!

---

**Dheeraj ji, koi step mein dikkat aaye toh batayein. Main step-by-step help karunga.**
