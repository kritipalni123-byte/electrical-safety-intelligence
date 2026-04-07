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
    .badge-ma   { background:#2d1b4e; color:#bf91f3; border:1px solid #6e40c9; }
    .badge-cap  { background:#1b3a4e; color:#79c0ff; border:1px solid #1f6feb; }
    .badge-tech { background:#1b4e2a; color:#56d364; border:1px solid #238636; }
    .badge-prod { background:#4e3a1b; color:#ffa657; border:1px solid #9e6a03; }
    .badge-reg  { background:#4e1b1b; color:#ff7b72; border:1px solid #b62324; }
    .badge-mkt  { background:#1b4e4e; color:#39d3c3; border:1px solid #0e7490; }
    .badge-fin  { background:#3a4e1b; color:#d2ff52; border:1px solid #4d7c0f; }
    .badge-oth  { background:#2d2d2d; color:#8b949e; border:1px solid #484f58; }
    .header-bar { background: linear-gradient(90deg,#f7b731,#f39c12); height:3px; border-radius:2px; margin-bottom:24px; }
    .section-head { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; text-transform:uppercase; letter-spacing:1.5px; color:#f7b731; margin:16px 0 6px 0; border-bottom:1px solid #30363d; padding-bottom:4px; }
    .stButton > button { background:#f7b731; color:#0d1117; border:none; font-weight:700; border-radius:6px; width:100%; }
    .stButton > button:hover { background:#f39c12; }
    div[data-testid="stSidebarContent"] { background:#0d1117; border-right:1px solid #30363d; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MASTER DATA
# ══════════════════════════════════════════════════════════════════

COMPETITORS = [
    "Honeywell Safety", "Honeywell Salisbury", "Salisbury",
    "CATU", "Novax", "Ansell", "DPL", "MN Rubber", "Jayco", "Morning Pride",
]

KEYWORDS_GLOVES = {
    "Core": [
        "electrical safety gloves","electrical insulating gloves",
        "rubber insulating gloves","electrician gloves",
        "high voltage gloves","low voltage gloves",
        "insulated gloves electrical","safety gloves for electrical work",
        "shock proof gloves","dielectric gloves",
    ],
    "Technical": [
        "voltage rated gloves","dielectric rubber gloves",
        "insulating hand protection","electrical PPE gloves",
        "electrical protective gloves","live line gloves",
        "energized work gloves","electrical hazard gloves",
        "arc flash gloves","arc rated gloves",
    ],
    "Standards": [
        "IEC 60903 gloves","EN 60903 gloves","ASTM D120 gloves",
        "ASTM F2675 gloves","IS 4770 electrical gloves",
        "OSHA electrical gloves","NFPA 70E gloves",
    ],
    "Class": [
        "Class 00 gloves","Class 0 gloves","Class 1 gloves",
        "Class 2 gloves","Class 3 gloves","Class 4 gloves",
    ],
    "Voltage": [
        "500V gloves","1kV gloves","11kV gloves","33kV gloves","36kV gloves",
        "high voltage insulating gloves","medium voltage gloves",
        "extra high voltage gloves",
    ],
    "Material": [
        "latex insulating gloves","rubber electrical gloves",
        "synthetic rubber gloves","composite electrical gloves",
        "leather protector gloves","dual layer electrical glove",
    ],
    "Use Case": [
        "lineman gloves","utility worker gloves","substation gloves",
        "switchgear gloves","maintenance electrician gloves",
        "transmission line gloves","telecom electrical gloves",
        "EV maintenance gloves",
    ],
    "Feature": [
        "arc flash rated gloves","flame resistant gloves",
        "cut resistant electrical gloves","oil resistant electrical gloves",
        "ozone resistant gloves","waterproof insulating gloves",
        "ergonomic electrical gloves",
    ],
}

KEYWORDS_MATS = {
    "Core": [
        "electrical safety mat","insulating rubber mat",
        "electrical insulating mat","dielectric mat",
        "safety mat for electrical panel","switchboard mat",
    ],
    "Technical": [
        "rubber insulating matting","electrical insulation mat",
        "anti shock mat","electrical protection mat",
        "electrical floor mat","panel room mat",
    ],
    "Standards": [
        "IEC 61111 mat","ASTM insulating mat","IS 15652 mat","OSHA electrical mat",
    ],
    "Class": [
        "Class A electrical mat","Class B electrical mat","Class C electrical mat",
    ],
    "Voltage": [
        "low voltage safety mat","medium voltage mat",
        "high voltage insulating mat","11kV mat","33kV mat",
    ],
    "Use Case": [
        "switchgear mat","transformer room mat","control panel mat",
        "substation mat","electrical room flooring","HT panel mat","LT panel mat",
    ],
    "Feature": [
        "anti skid electrical mat","flame retardant mat",
        "fire resistant rubber mat","oil resistant mat",
        "heat resistant electrical mat","corrugated rubber mat","non conductive mat",
    ],
}

KEYWORDS_ARC = {
    "Core": [
        "arc flash suit","arc flash PPE","arc flash protection suit",
        "electrical arc suit","arc rated suit",
    ],
    "Technical": [
        "arc flash clothing","arc flash protective clothing",
        "arc flash kit","arc flash coverall","arc flash uniform",
    ],
    "Standards": [
        "NFPA 70E arc flash suit","IEC 61482 arc flash suit",
        "ASTM F1506 arc flash","ATPV rating suit","cal/cm2 rating suit",
        "8 cal arc flash suit","25 cal arc flash suit",
    ],
    "Type": [
        "arc flash hood","arc flash face shield","arc flash helmet",
        "arc flash jacket","arc flash bib overall",
        "arc flash gloves","arc flash balaclava",
    ],
    "Use Case": [
        "substation arc flash suit","switchgear arc flash PPE",
        "electrical maintenance PPE","high voltage PPE suit","live panel work PPE",
    ],
    "Feature": [
        "flame resistant suit","fire retardant suit","heat resistant PPE",
        "arc rated clothing","multi layer arc suit",
    ],
    "Common": [
        "electrical blast suit","arc protection clothing",
        "flash fire suit","electrical hazard suit","FR arc flash clothing",
    ],
}

KEYWORDS_COMMON = [
    "electrical PPE","electrical safety equipment",
    "electrical protective equipment","live line PPE",
    "high voltage safety equipment","industrial safety PPE electrical",
    "power sector safety gear","electrical PPE India","electrical safety India",
]

COMPETITOR_KEYWORDS = [
    "Salisbury insulating gloves","Salisbury Class 2 gloves",
    "Salisbury electrical gloves","Honeywell electrical gloves",
    "Honeywell insulating gloves","Honeywell insulating mats",
    "Salisbury insulating mats","Honeywell arc flash PPE",
    "Morning Pride arc flash suit","CATU insulating gloves",
    "CATU electrical gloves","CATU IEC 60903 gloves",
    "CATU Class 1 gloves","CATU insulating mats","CATU arc flash suit",
    "Novax electrical gloves","Novax rubber insulating gloves",
    "Novax insulating gloves","Novax Class 0 gloves","Novax ASTM D120 gloves",
    "Ansell electrical gloves","Ansell arc flash PPE",
    "DPL electrical gloves","DPL insulating gloves",
    "DPL rubber mats","DPL arc flash suit",
    "MN Rubber electrical gloves","MN Rubber insulating mats",
    "Jayco electrical gloves","Jayco insulating mats","Jayco arc flash PPE",
]

ALL_KEYWORD_GROUPS = {
    "🧤 Gloves — Core":        KEYWORDS_GLOVES["Core"],
    "🧤 Gloves — Technical":   KEYWORDS_GLOVES["Technical"],
    "🧤 Gloves — Standards":   KEYWORDS_GLOVES["Standards"],
    "🧤 Gloves — Class":       KEYWORDS_GLOVES["Class"],
    "🧤 Gloves — Voltage":     KEYWORDS_GLOVES["Voltage"],
    "🧤 Gloves — Material":    KEYWORDS_GLOVES["Material"],
    "🧤 Gloves — Use Case":    KEYWORDS_GLOVES["Use Case"],
    "🧤 Gloves — Feature":     KEYWORDS_GLOVES["Feature"],
    "🟫 Mats — Core":          KEYWORDS_MATS["Core"],
    "🟫 Mats — Technical":     KEYWORDS_MATS["Technical"],
    "🟫 Mats — Standards":     KEYWORDS_MATS["Standards"],
    "🟫 Mats — Class":         KEYWORDS_MATS["Class"],
    "🟫 Mats — Voltage":       KEYWORDS_MATS["Voltage"],
    "🟫 Mats — Use Case":      KEYWORDS_MATS["Use Case"],
    "🟫 Mats — Feature":       KEYWORDS_MATS["Feature"],
    "🦺 Arc Suits — Core":     KEYWORDS_ARC["Core"],
    "🦺 Arc Suits — Technical":KEYWORDS_ARC["Technical"],
    "🦺 Arc Suits — Standards":KEYWORDS_ARC["Standards"],
    "🦺 Arc Suits — Type":     KEYWORDS_ARC["Type"],
    "🦺 Arc Suits — Use Case": KEYWORDS_ARC["Use Case"],
    "🦺 Arc Suits — Feature":  KEYWORDS_ARC["Feature"],
    "🦺 Arc Suits — Common":   KEYWORDS_ARC["Common"],
    "🌐 Common / Cross-Product": KEYWORDS_COMMON,
}

CATEGORIES = [
    "M&A / Partnerships","Capacity Development","Technology Update",
    "New Product Launch","Regulatory Change","Market Expansion",
    "Financial Results","Other",
]
BADGE_CLASS = {
    "M&A / Partnerships":"badge-ma","Capacity Development":"badge-cap",
    "Technology Update":"badge-tech","New Product Launch":"badge-prod",
    "Regulatory Change":"badge-reg","Market Expansion":"badge-mkt",
    "Financial Results":"badge-fin","Other":"badge-oth",
}
CATEGORY_COLORS = {
    "M&A / Partnerships":"#bf91f3","Capacity Development":"#79c0ff",
    "Technology Update":"#56d364","New Product Launch":"#ffa657",
    "Regulatory Change":"#ff7b72","Market Expansion":"#39d3c3",
    "Financial Results":"#d2ff52","Other":"#8b949e",
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
    if any(k in t for k in ["acqui","merger","partner","joint venture","stake","takeover","collaboration","alliance"]):
        return "M&A / Partnerships"
    if any(k in t for k in ["plant","capacity","expansion","facility","manufactur","greenfield","brownfield","production"]):
        return "Capacity Development"
    if any(k in t for k in ["technology","innovation","patent","r&d","research","digital","new material","composite"]):
        return "Technology Update"
    if any(k in t for k in ["launch","new product","introduce","unveil","new model","new range","new line"]):
        return "New Product Launch"
    if any(k in t for k in ["regulat","standard","compliance","bis","iec","astm","nfpa","osha","is 4770","is 15652","iec 60903","iec 61111","iec 61482","policy","law","cea","dgfasli","mandatory"]):
        return "Regulatory Change"
    if any(k in t for k in ["market","export","global","international","expand","distributor","new territory","india","apac"]):
        return "Market Expansion"
    if any(k in t for k in ["revenue","profit","earnings","results","quarter","turnover","growth","sales"]):
        return "Financial Results"
    return "Other"

def classify_with_llm(articles, api_key):
    if not api_key:
        for a in articles:
            a["category"]    = keyword_classify(a["title"] + " " + a["summary"])
            a["relevance"]   = 6
            a["key_insight"] = "Add Groq API key for AI-powered insights"
        return articles
    client = Groq(api_key=api_key)
    for a in articles:
        prompt = f"""You are a market intelligence analyst for an electrical safety PPE manufacturer in India.
Products: electrical insulating gloves, rubber insulating mats, arc flash suits.
Competitors: Honeywell Salisbury, CATU, Novax, Ansell, DPL, MN Rubber, Jayco, Morning Pride.

Classify this article into EXACTLY ONE category:
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
                max_tokens=120, temperature=0.1,
            )
            result = json.loads(resp.choices[0].message.content.strip())
            a["category"]    = result.get("category","Other")
            a["relevance"]   = int(result.get("relevance",5))
            a["key_insight"] = result.get("key_insight","—")
        except Exception:
            a["category"]    = keyword_classify(a["title"]+" "+a["summary"])
            a["relevance"]   = 5
            a["key_insight"] = "Classification unavailable"
        time.sleep(0.3)
    return articles

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_news(queries_tuple, days_back, api_key):
    all_articles = []
    for q in queries_tuple:
        all_articles.extend(fetch_google_news(q, days_back))
        time.sleep(0.2)
    seen, unique = set(), []
    for a in all_articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return classify_with_llm(unique, api_key)

def build_queries(sel_competitors, sel_groups, include_comp_kw):
    queries = list(sel_competitors)
    for g in sel_groups:
        queries.extend(ALL_KEYWORD_GROUPS.get(g, []))
    if include_comp_kw:
        queries.extend(COMPETITOR_KEYWORDS)
    seen, unique = set(), []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
    return unique

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Intel Platform")
    st.markdown("**Electrical Safety PPE · India**")
    st.markdown('<div class="header-bar"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">🔑 API Key</div>', unsafe_allow_html=True)
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    st.markdown('<div class="section-head">🏭 Competitors</div>', unsafe_allow_html=True)
    selected_competitors = st.multiselect("Select competitors", COMPETITORS, default=COMPETITORS)
    new_co = st.text_input("➕ Add competitor", placeholder="e.g. Karam Industries")
    if new_co:
        selected_competitors.append(new_co)

    st.markdown('<div class="section-head">📦 Product Lines</div>', unsafe_allow_html=True)
    product_lines = st.multiselect(
        "Select product lines",
        ["🧤 Gloves","🟫 Mats","🦺 Arc Suits","🌐 Common"],
        default=["🧤 Gloves","🟫 Mats","🦺 Arc Suits","🌐 Common"],
    )

    st.markdown('<div class="section-head">🔍 Keyword Groups</div>', unsafe_allow_html=True)
    available_groups = [
        g for g in ALL_KEYWORD_GROUPS.keys()
        if any(pl.split(" ")[0] in g for pl in product_lines) or "Common" in g
    ]
    selected_groups = st.multiselect("Keyword groups", available_groups, default=available_groups)
    include_comp_kw = st.checkbox("Include competitor-specific keywords", value=True)

    st.markdown('<div class="section-head">📅 Filters</div>', unsafe_allow_html=True)
    days_back     = st.slider("Days of news", 7, 90, 30)
    selected_cats = st.multiselect("Categories", CATEGORIES, default=CATEGORIES)
    min_rel       = st.slider("Min relevance score", 1, 10, 5)

    fetch_btn = st.button("⚡ Fetch & Analyse News")

# ── MAIN ──────────────────────────────────────────────────────────
st.markdown("# ⚡ Electrical Safety Market Intelligence")
st.markdown("*Tracking M&A · Capacity · Technology · Products · Regulatory — Gloves · Mats · Arc Suits*")
st.markdown('<div class="header-bar"></div>', unsafe_allow_html=True)

if fetch_btn or "intel_data" in st.session_state:
    if fetch_btn:
        queries = build_queries(selected_competitors, selected_groups, include_comp_kw)
        st.info(f"🔍 Searching **{len(queries)} queries** across competitors + all keyword groups…")
        with st.spinner("Fetching news & running AI analysis… this may take 1–2 minutes"):
            data = fetch_all_news(tuple(queries), days_back, api_key or "")
            st.session_state["intel_data"] = data

    data = st.session_state.get("intel_data", [])
    df   = pd.DataFrame(data)

    if df.empty:
        st.warning("No articles found. Try a longer time range or broader keywords.")
    else:
        df_f = df[df["category"].isin(selected_cats) & (df["relevance"] >= min_rel)].copy()
        df_f = df_f.sort_values("published", ascending=False)

        # Metrics
        c1,c2,c3,c4,c5 = st.columns(5)
        for col, val, lbl in [
            (c1, len(df_f),                                              "Total Articles"),
            (c2, df_f["category"].nunique(),                             "Categories Active"),
            (c3, len(df_f[df_f["category"]=="M&A / Partnerships"]),     "M&A Signals"),
            (c4, len(df_f[df_f["category"]=="Regulatory Change"]),       "Regulatory Alerts"),
            (c5, round(df_f["relevance"].mean(),1) if len(df_f) else 0, "Avg Relevance"),
        ]:
            col.markdown(
                f'<div class="metric-card"><div class="metric-number">{val}</div>'
                f'<div class="metric-label">{lbl}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Charts
        ch1, ch2 = st.columns(2)
        with ch1:
            cat_df = df_f["category"].value_counts().reset_index()
            cat_df.columns = ["Category","Count"]
            fig = px.bar(cat_df, x="Count", y="Category", orientation="h",
                         color="Category", color_discrete_map=CATEGORY_COLORS,
                         title="📊 Articles by Intelligence Category")
            fig.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                font_color="#e6edf3", showlegend=False,
                margin=dict(l=10,r=10,t=40,b=10),
                xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"),
            )
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            df_f["week"] = df_f["published"].dt.to_period("W").astype(str)
            trend = df_f.groupby(["week","category"]).size().reset_index(name="count")
            fig2 = px.line(trend, x="week", y="count", color="category",
                           color_discrete_map=CATEGORY_COLORS,
                           title="📈 Intelligence Trend by Week", markers=True)
            fig2.update_layout(
                plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                font_color="#e6edf3", title_font_size=13,
                legend=dict(bgcolor="#0d1117", font_size=10),
                margin=dict(l=10,r=10,t=40,b=10),
                xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"),
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Product line breakdown
        st.markdown("### 📦 Coverage by Product Line")
        p1, p2, p3 = st.columns(3)
        all_glove_kw = [k for v in KEYWORDS_GLOVES.values() for k in v]
        all_mat_kw   = [k for v in KEYWORDS_MATS.values()   for k in v]
        all_arc_kw   = [k for v in KEYWORDS_ARC.values()    for k in v]
        for col, label, kws in [
            (p1,"🧤 Gloves", all_glove_kw),
            (p2,"🟫 Mats",   all_mat_kw),
            (p3,"🦺 Arc Suits", all_arc_kw),
        ]:
            count = len(df_f[df_f["query"].isin(kws)]) if "query" in df_f.columns else 0
            col.markdown(
                f'<div class="metric-card"><div class="metric-number">{count}</div>'
                f'<div class="metric-label">{label}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # News feed
        st.markdown("### 📰 Intelligence Feed")
        fc1, fc2, fc3 = st.columns([2,1,1])
        with fc1:
            search = st.text_input("🔎 Search", placeholder="e.g. Honeywell, IEC 60903, arc flash…")
        with fc2:
            filter_product = st.selectbox("Product line", ["All","Gloves","Mats","Arc Suits"])
        with fc3:
            sort_by = st.selectbox("Sort by", ["Latest first","Highest relevance"])

        if search:
            df_f = df_f[df_f["title"].str.contains(search, case=False, na=False)]
        if filter_product != "All":
            pm = {"Gloves": all_glove_kw, "Mats": all_mat_kw, "Arc Suits": all_arc_kw}
            df_f = df_f[df_f["query"].isin(pm[filter_product])]
        if sort_by == "Highest relevance":
            df_f = df_f.sort_values("relevance", ascending=False)

        st.markdown(f"**{len(df_f)} articles** found")

        for _, row in df_f.iterrows():
            bc = BADGE_CLASS.get(row["category"], "badge-oth")
            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">
                    <a href="{row['link']}" target="_blank"
                       style="color:#e6edf3;text-decoration:none;">{row['title']}</a>
                </div>
                <div style="margin:8px 0;">
                    <span class="badge {bc}">{row['category']}</span>
                    <span class="badge" style="background:#1c2128;color:#8b949e;border:1px solid #30363d;">★ {row.get('relevance','—')}/10</span>
                    <span class="badge" style="background:#1c2128;color:#79c0ff;border:1px solid #30363d;">🔍 {row.get('query','—')}</span>
                </div>
                <div class="news-meta">
                    🗞️ {row['source']} &nbsp;|&nbsp;
                    📅 {row['published'].strftime('%d %b %Y')} &nbsp;|&nbsp;
                    💡 {row.get('key_insight','—')}
                </div>
            </div>""", unsafe_allow_html=True)

        # Export
        st.markdown("### 📥 Export Intelligence")
        ec1, ec2 = st.columns(2)
        out = df_f[["title","category","relevance","key_insight","query","source","published","link"]].copy()
        out["published"] = out["published"].dt.strftime("%Y-%m-%d")
        full_out = df[["title","category","relevance","key_insight","query","source","published","link"]].copy()
        full_out["published"] = full_out["published"].dt.strftime("%Y-%m-%d")
        with ec1:
            st.download_button("⬇️ Download filtered CSV", out.to_csv(index=False),
                f"intel_filtered_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
        with ec2:
            st.download_button("⬇️ Download full CSV", full_out.to_csv(index=False),
                f"intel_full_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")

else:
    st.info("👈 Configure your settings in the sidebar, then click **⚡ Fetch & Analyse News**")
    st.markdown("### 📦 Product Lines Being Tracked")
    cols = st.columns(3)
    cards = [
        ("🧤","Electrical Insulating Gloves","Classes 00–4 · IEC 60903 · ASTM D120 · IS 4770\n8 keyword groups · 60+ search terms"),
        ("🟫","Electrical Insulating Mats","Classes A–C · IEC 61111 · IS 15652 · ASTM\n7 keyword groups · 40+ search terms"),
        ("🦺","Arc Flash Suits","8–25 cal · NFPA 70E · IEC 61482 · ASTM F1506\n7 keyword groups · 45+ search terms"),
    ]
    for i,(icon,title,desc) in enumerate(cards):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card" style="text-align:left;padding:20px;min-height:140px;">
                <div style="font-size:2rem;margin-bottom:10px;">{icon}</div>
                <div style="font-weight:700;color:#f7b731;font-size:0.9rem;margin-bottom:6px;">{title}</div>
                <div style="font-size:0.78rem;color:#8b949e;line-height:1.6;white-space:pre-line;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("### 🏭 Competitors Being Tracked")
    comp_cols = st.columns(5)
    for i,co in enumerate(COMPETITORS):
        with comp_cols[i%5]:
            st.markdown(
                f'<div class="metric-card" style="padding:10px;margin-bottom:8px;">'
                f'<div style="font-size:0.8rem;color:#e6edf3;font-weight:600;">{co}</div></div>',
                unsafe_allow_html=True
            )
