"""
app.py - News Hub AI Agent — Main Streamlit Dashboard
A unified tool to collect, filter, edit, schedule, and publish
Chhattisgarh & national news to Facebook, Instagram, Twitter, YouTube, Gmail.
"""
import json
import streamlit as st
from datetime import datetime, timedelta
from modules.config import load_config, save_config, DEFAULT_RSS_SOURCES, DEFAULT_PLATFORMS
from modules import database as db
from modules.aggregator import fetch_all, auto_categorise, is_cg_related
from modules.publisher import publish_post

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
