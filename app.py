import streamlit as st
import feedparser
import pandas as pd
import plotly.express as px
from groq import Groq
from datetime import datetime, timedelta
import urllib.parse
import time
import json

# ── PAGE CONFIG ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Electrical Safety Intel",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── CUSTOM CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .metric-card {
        background: linear-gradient(135deg, #161b22, #1c2128);
        border: 1px solid #30363d; border-radius: 10px;
        padding: 20px; text-align: center;
    }
    .metric-number { font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 600; color: #f7b731; }
    .metric-label { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1.5px; color: #8b949e; margin-top: 4px; }
    .news-card {
        background: #161b22; border: 1px solid #30363d;
        border-left: 3px solid #f7b731; border-radius: 8px;
        padding: 16px 20px; margin-bottom: 12px;
    }
    .news-title { font-size: 0.95rem; font-weight: 600; color: #e6edf3; margin-bottom: 6px; }
    .news-meta { font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #8b949e; }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; margin-right: 6px; }
    .badge-ma  { background:#2d1b4e; color:#bf91f3; border:1px solid #6e40c9; }
    .badge-cap { background:#1b3a4e; color:#79c0ff; border:1px solid #1f6feb; }
    .badge-tech{ background:#1b4e2a; color:#56d364; border:1px solid #238636; }
    .badge-prod{ background:#4e3a1b; color:#ffa657; border:1px solid #9e6a03; }
    .badge-reg { background:#4e1b1b; color:#ff7b72; border:1px solid #b62324; }
    .badge-mkt { background:#1b4e4e; color:#39d3c3; border:1px solid #0e7490; }
    .badge-fin { background:#3a4e1b; color:#d2ff52; border:1px solid #4d7c0f; }
    .badge-oth { background:#2d2d2d; color:#8b949e; border:1px solid #484f58; }
    .header-bar { background: linear-gradient(90deg,#f7b731,#f39c12); height:3px; border-radius:2px; margin-bottom:24px; }
    .stButton > button { background:#f7b731; color:#0d1117; border:none; font-weight:700; border-radius:6px; width:100%; }
    .stButton > button:hover { background:#f39c12; }
    div[data-testid="stSidebarContent"] { background:#0d1117; border-right:1px solid #30363d; }
</style>
""", unsafe_allow_html=True)

# ── CONSTANTS ─────────────────────────────────────────────────────
DEFAULT_COMPANIES = [
    "Honeywell Safety",
    "Ansell",
    "Dräger",
    "Cementex",
    "Oberon Company",
    "Salisbury by Honeywell",
    "Rubber Insulating Products",
]
INDUSTRY_KEYWORDS = [
    "electrical safety gloves India",
    "electrical insulating gloves",
    "arc flash suit India",
    "arc protection PPE",
    "electrical safety mat",
    "rubber insulating mat",
    "electrical PPE India",
    "IS 4770 standard",
    "IEC 60903",
    "high voltage gloves manufacturer",
]
CATEGORIES = [
    "M&A / Partnerships",
    "Capacity Development",
    "Technology Update",
    "New Product Launch",
    "Regulatory Change",
    "Market Expansion",
    "Financial Results",
    "Other",
]
BADGE_CLASS = {
    "M&A / Partnerships":  "badge-ma",
    "Capacity Development":"badge-cap",
    "Technology Update":   "badge-tech",
    "New Product Launch":  "badge-prod",
    "Regulatory Change":   "badge-reg",
    "Market Expansion":    "badge-mkt",
    "Financial Results":   "badge-fin",
    "Other":               "badge-oth",
}
CATEGORY_COLORS = {
    "M&A / Partnerships":  "#bf91f3",
    "Capacity Development":"#79c0ff",
    "Technology Update":   "#56d364",
    "New Product Launch":  "#ffa657",
    "Regulatory Change":   "#ff7b72",
    "Market Expansion":    "#39d3c3",
    "Financial Results":   "#d2ff52",
    "Other":               "#8b949e",
}

# ── HELPERS ───────────────────────────────────────────────────────
def fetch_google_news(query, days_back=30):
    encoded = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    cutoff = datetime.now() - timedelta(days=days_back)
    articles = []
    for entry in feed.entries:
        try:
            pub = datetime(*entry.published_parsed[:6])
        except Exception:
            pub = datetime.now()
        if pub >= cutoff:
            articles.append({
                "title":     entry.title,
                "link":      entry.link,
                "published": pub,
                "source":    entry.get("source", {}).get("title", "Unknown"),
                "summary":   entry.get("summary", "")[:300],
                "query":     query,
            })
    return articles

def keyword_classify(text):
    t = text.lower()
    if any(k in t for k in ["acqui","merger","partner","joint venture","stake","takeover"]):
        return "M&A / Partnerships"
    if any(k in t for k in ["plant","capacity","expansion","facility","manufactur","greenfield"]):
        return "Capacity Development"
    if any(k in t for k in ["technology","innovation","patent","r&d","research","digital"]):
        return "Technology Update"
    if any(k in t for k in ["launch","new product","introduce","unveil","new model"]):
        return "New Product Launch"
    if any(k in t for k in ["regulat","standard","compliance","bis","iec","policy","law","cea","dgfasli"]):
        return "Regulatory Change"
    if any(k in t for k in ["market","export","global","international","expand","distributor"]):
        return "Market Expansion"
    if any(k in t for k in ["revenue","profit","earnings","results","quarter","turnover"]):
        return "Financial Results"
    return "Other"

def classify_with_llm(articles, api_key):
    if not api_key:
        for a in articles:
            a["category"]    = keyword_classify(a["title"] + " " + a["summary"])
            a["relevance"]   = 6
            a["key_insight"] = "Add Groq API key in sidebar for AI-powered insights"
        return articles

    client = Groq(api_key=api_key)
    for a in articles:
        prompt = f"""You are a market intelligence analyst for the electrical safety PPE industry
(insulating gloves, rubber mats, arc flash suits) focused on India.

Classify this article into EXACTLY ONE category from:
{json.dumps(CATEGORIES)}

Rate relevance 1-10 for a manufacturer in this space.
Give ONE key insight in max 15 words.

Title: {a['title']}
Summary: {a['summary']}

Reply ONLY in JSON (no markdown):
{{"category":"...","relevance":7,"key_insight":"..."}}"""
        try:
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role":"user","content":prompt}],
                max_tokens=100,
                temperature=0.1,
            )
            result = json.loads(resp.choices[0].message.content.strip())
            a["category"]    = result.get("category","Other")
            a["relevance"]   = int(result.get("relevance", 5))
            a["key_insight"] = result.get("key_insight","—")
        except Exception:
            a["category"]    = keyword_classify(a["title"] + " " + a["summary"])
            a["relevance"]   = 5
            a["key_insight"] = "Classification unavailable"
        time.sleep(0.3)
    return articles

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_news(companies_tuple, keywords_tuple, days_back, api_key):
    all_articles = []
    for q in list(companies_tuple) + list(keywords_tuple):
        all_articles.extend(fetch_google_news(q, days_back))
    seen, unique = set(), []
    for a in all_articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return classify_with_llm(unique, api_key)

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Intel Platform")
    st.markdown("**Electrical Safety Industry · India**")
    st.markdown('<div class="header-bar"></div>', unsafe_allow_html=True)

    st.markdown("#### 🔑 Groq API Key")
    api_key = st.text_input("Paste your key", type="password", placeholder="gsk_...")

    st.markdown("#### 🏭 Companies to Track")
    selected_companies = st.multiselect("Select competitors", DEFAULT_COMPANIES, default=DEFAULT_COMPANIES[:4])
    new_co = st.text_input("➕ Add a company", placeholder="e.g. Karam Industries")
    if new_co and new_co not in selected_companies:
        selected_companies.append(new_co)

    st.markdown("#### 🔍 Industry Keywords")
    selected_kw = st.multiselect("Select keywords", INDUSTRY_KEYWORDS, default=INDUSTRY_KEYWORDS[:4])

    st.markdown("#### 📅 Time Range")
    days_back = st.slider("Days of news", 7, 90, 30)

    st.markdown("#### 🎯 Filter by Category")
    selected_cats = st.multiselect("Show categories", CATEGORIES, default=CATEGORIES)

    st.markdown("#### 📊 Minimum Relevance")
    min_rel = st.slider("Score (1–10)", 1, 10, 5)

    fetch_btn = st.button("⚡ Fetch & Analyse News")

# ── MAIN ──────────────────────────────────────────────────────────
st.markdown("# ⚡ Electrical Safety Market Intelligence")
st.markdown("*Tracking M&A · Capacity · Technology · Products · Regulatory · India & Global*")
st.markdown('<div class="header-bar"></div>', unsafe_allow_html=True)

if fetch_btn or "intel_data" in st.session_state:
    if fetch_btn:
        with st.spinner("Fetching news & running AI analysis…"):
            data = fetch_all_news(
                tuple(selected_companies),
                tuple(selected_kw),
                days_back,
                api_key or "",
            )
            st.session_state["intel_data"] = data

    data = st.session_state.get("intel_data", [])
    df   = pd.DataFrame(data)

    if df.empty:
        st.warning("No articles found. Try broader keywords or a longer time range.")
    else:
        df_f = df[df["category"].isin(selected_cats) & (df["relevance"] >= min_rel)].copy()
        df_f = df_f.sort_values("published", ascending=False)

        # Metrics
        c1,c2,c3,c4,c5 = st.columns(5)
        for col, val, lbl in [
            (c1, len(df_f), "Total Articles"),
            (c2, df_f["category"].nunique(), "Categories"),
            (c3, len(df_f[df_f["category"]=="M&A / Partnerships"]), "M&A Signals"),
            (c4, len(df_f[df_f["category"]=="Regulatory Change"]), "Regulatory"),
            (c5, round(df_f["relevance"].mean(),1) if len(df_f) else 0, "Avg Relevance"),
        ]:
            col.markdown(f'<div class="metric-card"><div class="metric-number">{val}</div><div class="metric-label">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts
        ch1, ch2 = st.columns(2)
        with ch1:
            cat_df = df_f["category"].value_counts().reset_index()
            cat_df.columns = ["Category","Count"]
            fig = px.bar(cat_df, x="Count", y="Category", orientation="h",
                         color="Category", color_discrete_map=CATEGORY_COLORS,
                         title="📊 News by Category")
            fig.update_layout(plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                              font_color="#e6edf3", showlegend=False,
                              margin=dict(l=10,r=10,t=40,b=10),
                              xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            df_f["week"] = df_f["published"].dt.to_period("W").astype(str)
            trend = df_f.groupby(["week","category"]).size().reset_index(name="count")
            fig2 = px.line(trend, x="week", y="count", color="category",
                           color_discrete_map=CATEGORY_COLORS,
                           title="📈 Intelligence Trend Over Time", markers=True)
            fig2.update_layout(plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                               font_color="#e6edf3", title_font_size=13,
                               legend=dict(bgcolor="#0d1117", font_size=10),
                               margin=dict(l=10,r=10,t=40,b=10),
                               xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
            st.plotly_chart(fig2, use_container_width=True)

        # News feed
        st.markdown("### 📰 Intelligence Feed")
        search = st.text_input("🔎 Search articles", placeholder="Filter by keyword…")
        if search:
            df_f = df_f[df_f["title"].str.contains(search, case=False, na=False)]

        for _, row in df_f.iterrows():
            bc = BADGE_CLASS.get(row["category"], "badge-oth")
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">
                    <a href="{row['link']}" target="_blank" style="color:#e6edf3;text-decoration:none;">{row['title']}</a>
                </div>
                <div style="margin:8px 0;">
                    <span class="badge {bc}">{row['category']}</span>
                    <span class="badge" style="background:#1c2128;color:#8b949e;border:1px solid #30363d;">★ {row.get('relevance','—')}/10</span>
                </div>
                <div class="news-meta">🗞️ {row['source']} &nbsp;|&nbsp; 📅 {row['published'].strftime('%d %b %Y')} &nbsp;|&nbsp; 💡 {row.get('key_insight','—')}</div>
            </div>""", unsafe_allow_html=True)

        # Export
        st.markdown("### 📥 Export")
        out = df_f[["title","category","relevance","key_insight","source","published","link"]].copy()
        out["published"] = out["published"].dt.strftime("%Y-%m-%d")
        st.download_button("⬇️ Download as CSV", out.to_csv(index=False),
                           f"intel_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
else:
    st.info("👈 Configure your settings in the sidebar, then click **⚡ Fetch & Analyse News**")
    cols = st.columns(3)
    cards = [
        ("🤝","M&A / Partnerships","Acquisitions, JVs, distribution deals"),
        ("🏭","Capacity Development","New plants, expansions, production scale-up"),
        ("💡","Technology Updates","R&D, patents, material innovations"),
        ("🆕","New Product Launches","New SKUs, certifications earned"),
        ("📋","Regulatory Changes","BIS, IEC, IS 4770, CEA, DGFASLI updates"),
        ("🌏","Market Expansion","Export news, new geographies, distributors"),
    ]
    for i,(icon,title,desc) in enumerate(cards):
        with cols[i%3]:
            st.markdown(f"""<div class="metric-card" style="text-align:left;margin-bottom:12px;padding:16px;">
                <div style="font-size:1.5rem;margin-bottom:8px;">{icon}</div>
                <div style="font-weight:700;color:#f7b731;font-size:0.85rem;margin-bottom:4px;">{title}</div>
                <div style="font-size:0.78rem;color:#8b949e;line-height:1.4;">{desc}</div>
            </div>""", unsafe_allow_html=True)
