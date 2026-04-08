import streamlit as st
import feedparser
import pandas as pd
import plotly.express as px
from groq import Groq
from datetime import datetime, timedelta
import urllib.parse
import time
import json
import re
from difflib import SequenceMatcher

# ── PAGE CONFIG ────────────────────────────────────────────────────
st.set_page_config(
    page_title="Electrical Safety Intel · India",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .metric-card {
        background: linear-gradient(135deg, #161b22, #1c2128);
        border: 1px solid #30363d; border-radius: 10px; padding: 20px; text-align: center;
    }
    .metric-number { font-family:'IBM Plex Mono',monospace; font-size:2.2rem; font-weight:600; color:#f7b731; }
    .metric-label  { font-size:0.75rem; text-transform:uppercase; letter-spacing:1.5px; color:#8b949e; margin-top:4px; }
    .news-card {
        background:#161b22; border:1px solid #30363d;
        border-radius:8px; padding:16px 20px; margin-bottom:12px;
    }
    .news-title { font-size:0.95rem; font-weight:600; color:#e6edf3; margin-bottom:6px; }
    .news-meta  { font-family:'IBM Plex Mono',monospace; font-size:0.7rem; color:#8b949e; margin-top:6px; line-height:1.6; }
    .score-bar-wrap { background:#21262d; border-radius:10px; height:7px; width:100%; margin:6px 0 4px 0; }
    .score-bar { height:7px; border-radius:10px; transition: width 0.4s ease; }
    .badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.7rem; font-weight:600; text-transform:uppercase; letter-spacing:0.8px; margin-right:6px; }
    .badge-ma   { background:#2d1b4e; color:#bf91f3; border:1px solid #6e40c9; }
    .badge-cap  { background:#1b3a4e; color:#79c0ff; border:1px solid #1f6feb; }
    .badge-tech { background:#1b4e2a; color:#56d364; border:1px solid #238636; }
    .badge-prod { background:#4e3a1b; color:#ffa657; border:1px solid #9e6a03; }
    .badge-reg  { background:#4e1b1b; color:#ff7b72; border:1px solid #b62324; }
    .badge-mkt  { background:#1b4e4e; color:#39d3c3; border:1px solid #0e7490; }
    .badge-fin  { background:#3a4e1b; color:#d2ff52; border:1px solid #4d7c0f; }
    .badge-oth  { background:#2d2d2d; color:#8b949e; border:1px solid #484f58; }
    .badge-high { background:#3d1a1a; color:#ff7b72; border:1px solid #b62324; font-size:0.75rem; }
    .badge-med  { background:#3d2e1a; color:#ffa657; border:1px solid #9e6a03; font-size:0.75rem; }
    .badge-low  { background:#3d3a1a; color:#f7b731; border:1px solid #7d6608; font-size:0.75rem; }
    .badge-ignore { background:#1a1a1a; color:#8b949e; border:1px solid #30363d; font-size:0.75rem; }
    .header-bar { background:linear-gradient(90deg,#f7b731,#f39c12); height:3px; border-radius:2px; margin-bottom:24px; }
    .section-head { font-family:'IBM Plex Mono',monospace; font-size:0.72rem; text-transform:uppercase; letter-spacing:1.5px; color:#f7b731; margin:16px 0 6px 0; border-bottom:1px solid #30363d; padding-bottom:4px; }
    .score-breakdown { background:#0d1117; border:1px solid #21262d; border-radius:6px; padding:8px 12px; font-size:0.72rem; color:#8b949e; margin-top:6px; font-family:'IBM Plex Mono',monospace; }
    .info-box { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:14px 18px; font-size:0.8rem; margin-bottom:16px; line-height:1.8; }
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

# ── KEYWORD SCORING MAP (Component 1) ─────────────────────────────
# Each entry: (pattern_to_match, base_score, keyword_type_label)
KEYWORD_SCORE_MAP = [
    # Brand + Product combos → 100
    ("salisbury arc flash",         100, "Brand+Product"),
    ("salisbury insulating glove",  100, "Brand+Product"),
    ("salisbury insulating mat",    100, "Brand+Product"),
    ("honeywell arc flash",         100, "Brand+Product"),
    ("honeywell insulating glove",  100, "Brand+Product"),
    ("honeywell insulating mat",    100, "Brand+Product"),
    ("catu arc flash",              100, "Brand+Product"),
    ("catu insulating glove",       100, "Brand+Product"),
    ("catu insulating mat",         100, "Brand+Product"),
    ("novax insulating glove",      100, "Brand+Product"),
    ("novax rubber insulating",     100, "Brand+Product"),
    ("ansell arc flash",            100, "Brand+Product"),
    ("ansell electrical glove",     100, "Brand+Product"),
    ("dpl insulating glove",        100, "Brand+Product"),
    ("dpl rubber mat",              100, "Brand+Product"),
    ("mn rubber electrical",        100, "Brand+Product"),
    ("jayco insulating",            100, "Brand+Product"),
    ("morning pride arc",           100, "Brand+Product"),

    # Standards → 90
    ("iec 60903",   90, "Standard"),
    ("iec 61111",   90, "Standard"),
    ("iec 61482",   90, "Standard"),
    ("astm d120",   90, "Standard"),
    ("astm f1506",  90, "Standard"),
    ("astm f2675",  90, "Standard"),
    ("nfpa 70e",    90, "Standard"),
    ("is 4770",     90, "Standard"),
    ("is 15652",    90, "Standard"),
    ("en 60903",    90, "Standard"),
    ("osha 1910",   90, "Standard"),

    # Specs → 80
    ("class 00",    80, "Spec"),
    ("class 0 ",    80, "Spec"),
    ("class 1 ",    80, "Spec"),
    ("class 2 ",    80, "Spec"),
    ("class 3 ",    80, "Spec"),
    ("class 4 ",    80, "Spec"),
    ("class a mat", 80, "Spec"),
    ("class b mat", 80, "Spec"),
    ("class c mat", 80, "Spec"),
    ("11kv",        80, "Spec"),
    ("33kv",        80, "Spec"),
    ("36kv",        80, "Spec"),
    ("8 cal",       80, "Spec"),
    ("25 cal",      80, "Spec"),
    ("40 cal",      80, "Spec"),
    ("cal/cm2",     80, "Spec"),
    ("atpv",        80, "Spec"),

    # Core products → 70
    ("arc flash suit",          70, "Core Product"),
    ("arc flash ppe",           70, "Core Product"),
    ("arc flash protection",    70, "Core Product"),
    ("arc rated suit",          70, "Core Product"),
    ("arc flash coverall",      70, "Core Product"),
    ("insulating glove",        70, "Core Product"),
    ("electrical insulating glove", 70, "Core Product"),
    ("rubber insulating glove", 70, "Core Product"),
    ("dielectric glove",        70, "Core Product"),
    ("high voltage glove",      70, "Core Product"),
    ("electrical safety glove", 70, "Core Product"),
    ("insulating mat",          70, "Core Product"),
    ("dielectric mat",          70, "Core Product"),
    ("switchboard mat",         70, "Core Product"),
    ("electrical safety mat",   70, "Core Product"),
    ("rubber mat electrical",   70, "Core Product"),

    # Technical / Feature → 50
    ("fr fabric",           50, "Technical"),
    ("flame resistant",     50, "Technical"),
    ("fire retardant",      50, "Technical"),
    ("arc rated",           50, "Technical"),
    ("dielectric",          50, "Technical"),
    ("live line",           50, "Technical"),
    ("energized work",      50, "Technical"),
    ("electrical hazard",   50, "Technical"),
    ("ozone resistant",     50, "Technical"),
    ("anti shock",          50, "Technical"),
    ("anti skid mat",       50, "Technical"),
    ("voltage rated",       50, "Technical"),
    ("electrical ppe",      50, "Technical"),
    ("lineman glove",       50, "Technical"),
    ("substation safety",   50, "Technical"),
    ("switchgear safety",   50, "Technical"),

    # Generic → 20
    ("safety equipment",    20, "Generic"),
    ("industrial safety",   20, "Generic"),
    ("ppe",                 20, "Generic"),
    ("protective equipment",20, "Generic"),
    ("electrical safety",   20, "Generic"),
]

# ── COMPETITOR SCORING MAP (Component 2) ──────────────────────────
DIRECT_COMPETITORS = [
    "honeywell", "salisbury", "catu", "novax", "ansell",
    "dpl", "mn rubber", "jayco", "morning pride",
]
INDIRECT_COMPETITOR_SIGNALS = [
    "global ppe leader", "leading ppe manufacturer", "major safety brand",
    "international safety company", "global safety leader",
]

# ── INTENT / CATEGORY SCORING (Component 3) ───────────────────────
INTENT_SCORES = {
    "Investment / Capacity Expansion": 100,
    "M&A / Partnership":               100,
    "New Product Launch":               90,
    "Technology / Innovation":          85,
    "Regulatory / Compliance":          80,
    "Large Order / Contract":           75,
    "General News / Mention":           40,
    "Irrelevant":                        0,
}

# Maps intent → display category for the dashboard
INTENT_TO_CATEGORY = {
    "Investment / Capacity Expansion": "Capacity Development",
    "M&A / Partnership":               "M&A / Partnerships",
    "New Product Launch":              "New Product Launch",
    "Technology / Innovation":         "Technology Update",
    "Regulatory / Compliance":         "Regulatory Change",
    "Large Order / Contract":          "Market Expansion",
    "General News / Mention":          "Other",
    "Irrelevant":                      "Other",
}

CATEGORIES = [
    "M&A / Partnerships", "Capacity Development", "Technology Update",
    "New Product Launch", "Regulatory Change", "Market Expansion",
    "Financial Results", "Other",
]
BADGE_CLASS = {
    "M&A / Partnerships": "badge-ma",   "Capacity Development": "badge-cap",
    "Technology Update":  "badge-tech", "New Product Launch":   "badge-prod",
    "Regulatory Change":  "badge-reg",  "Market Expansion":     "badge-mkt",
    "Financial Results":  "badge-fin",  "Other":                "badge-oth",
}
CATEGORY_COLORS = {
    "M&A / Partnerships": "#bf91f3", "Capacity Development": "#79c0ff",
    "Technology Update":  "#56d364", "New Product Launch":   "#ffa657",
    "Regulatory Change":  "#ff7b72", "Market Expansion":     "#39d3c3",
    "Financial Results":  "#d2ff52", "Other":                "#8b949e",
}

# ── HARD DISQUALIFIERS ────────────────────────────────────────────
# Articles containing ANY of these phrases are removed entirely
HARD_DISQUALIFIERS = [
    # Salisbury Journal / unrelated publications
    "salisbury journal", "the salisbury journal", "salisbury news",
    "salisbury post", "salisbury daily times", "salisbury university",
    "salisbury maryland", "salisbury uk", "salisbury cathedral",
    "salisbury plain", "salisbury poisoning", "salisbury novichok",
    # Unrelated safety categories
    "fire safety", "fall protection", "hard hat", "safety helmet",
    "safety footwear", "safety shoe", "safety boot",
    "hearing protection", "ear muff", "respirator mask",
    "gas mask", "safety goggle", "eye protection",
    # Consumer electronics
    "home appliance", "consumer electronic", "led bulb",
    "smartphone charger", "laptop battery", "television",
    "air conditioner", "washing machine", "refrigerator",
    "electric vehicle battery", "ev battery",
    # Academic journals
    "journal of", "scientific paper", "research paper",
    "abstract:", "doi:", "pubmed", "elsevier", "springer nature",
    "ieee xplore", "sciencedirect",
]

# Foreign-only signals — disqualify if present with NO India signal
FOREIGN_ONLY = [
    "u.s. market", "us market", "american market", "north american market",
    "european market", "uk market", "german market", "french market",
    "china market", "japanese market", "latin america market",
]
INDIA_SIGNALS = [
    "india", "indian", "bharat", "mumbai", "delhi", "bangalore",
    "chennai", "hyderabad", "pune", "kolkata", "gujarat", "maharashtra",
    "bis ", "is 4770", "is 15652", "cea ", "dgfasli", "pgiel",
    "make in india", "msme", "rupee", "₹", "inr",
    "ntpc", "bhel", "ongc", "powergrid", "tata power", "adani",
    "torrent power", "cesc", "bses",
]

# ── KEYWORD SETS FOR SIDEBAR ──────────────────────────────────────
KEYWORDS_GLOVES = {
    "Core":      ["electrical safety gloves","electrical insulating gloves","rubber insulating gloves","electrician gloves","high voltage gloves","low voltage gloves","insulated gloves electrical","shock proof gloves","dielectric gloves"],
    "Technical": ["voltage rated gloves","dielectric rubber gloves","electrical PPE gloves","electrical protective gloves","live line gloves","energized work gloves","arc flash gloves","arc rated gloves"],
    "Standards": ["IEC 60903 gloves","ASTM D120 gloves","IS 4770 electrical gloves","NFPA 70E gloves","EN 60903 gloves"],
    "Class":     ["Class 00 gloves","Class 0 gloves","Class 1 gloves","Class 2 gloves","Class 3 gloves","Class 4 gloves"],
    "Voltage":   ["11kV gloves","33kV gloves","500V gloves","high voltage insulating gloves","medium voltage gloves"],
    "Use Case":  ["lineman gloves","substation gloves","switchgear gloves","maintenance electrician gloves","transmission line gloves","EV maintenance gloves"],
    "Feature":   ["arc flash rated gloves","flame resistant gloves","ozone resistant gloves","oil resistant electrical gloves","waterproof insulating gloves"],
}
KEYWORDS_MATS = {
    "Core":      ["electrical safety mat","insulating rubber mat","electrical insulating mat","dielectric mat","switchboard mat"],
    "Technical": ["rubber insulating matting","anti shock mat","electrical protection mat","electrical floor mat","panel room mat"],
    "Standards": ["IEC 61111 mat","IS 15652 mat","ASTM insulating mat"],
    "Voltage":   ["11kV mat","33kV mat","high voltage insulating mat"],
    "Use Case":  ["switchgear mat","transformer room mat","control panel mat","substation mat","HT panel mat","LT panel mat"],
    "Feature":   ["anti skid electrical mat","flame retardant mat","corrugated rubber mat","non conductive mat"],
}
KEYWORDS_ARC = {
    "Core":      ["arc flash suit","arc flash PPE","arc flash protection suit","arc rated suit"],
    "Technical": ["arc flash clothing","arc flash protective clothing","arc flash coverall","arc flash uniform"],
    "Standards": ["NFPA 70E arc flash suit","IEC 61482 arc flash suit","ASTM F1506 arc flash","8 cal arc flash suit","25 cal arc flash suit"],
    "Type":      ["arc flash hood","arc flash face shield","arc flash helmet","arc flash jacket","arc flash balaclava"],
    "Use Case":  ["substation arc flash suit","switchgear arc flash PPE","electrical maintenance PPE","high voltage PPE suit"],
    "Feature":   ["flame resistant suit","fire retardant suit","arc rated clothing","multi layer arc suit"],
}
KEYWORDS_COMMON = [
    "electrical PPE India","electrical safety equipment India",
    "live line PPE India","high voltage safety equipment India",
    "electrical safety India","industrial safety PPE electrical India",
]
COMPETITOR_KEYWORDS = [
    "Salisbury arc flash suit","Salisbury insulating gloves","Salisbury insulating mats",
    "Honeywell electrical gloves India","Honeywell arc flash PPE India","Honeywell insulating mats India",
    "CATU insulating gloves","CATU arc flash suit","CATU IEC 60903 gloves","CATU insulating mats",
    "Novax electrical gloves","Novax rubber insulating gloves","Novax Class 0 gloves","Novax ASTM D120 gloves",
    "Ansell electrical gloves India","Ansell arc flash PPE India",
    "DPL electrical gloves","DPL insulating gloves","DPL rubber mats","DPL arc flash suit",
    "MN Rubber electrical gloves","MN Rubber insulating mats",
    "Jayco electrical gloves","Jayco insulating mats","Jayco arc flash PPE",
    "Morning Pride arc flash suit",
]
ALL_KEYWORD_GROUPS = {
    "🧤 Gloves — Core":         KEYWORDS_GLOVES["Core"],
    "🧤 Gloves — Technical":    KEYWORDS_GLOVES["Technical"],
    "🧤 Gloves — Standards":    KEYWORDS_GLOVES["Standards"],
    "🧤 Gloves — Class":        KEYWORDS_GLOVES["Class"],
    "🧤 Gloves — Voltage":      KEYWORDS_GLOVES["Voltage"],
    "🧤 Gloves — Use Case":     KEYWORDS_GLOVES["Use Case"],
    "🧤 Gloves — Feature":      KEYWORDS_GLOVES["Feature"],
    "🟫 Mats — Core":           KEYWORDS_MATS["Core"],
    "🟫 Mats — Technical":      KEYWORDS_MATS["Technical"],
    "🟫 Mats — Standards":      KEYWORDS_MATS["Standards"],
    "🟫 Mats — Voltage":        KEYWORDS_MATS["Voltage"],
    "🟫 Mats — Use Case":       KEYWORDS_MATS["Use Case"],
    "🟫 Mats — Feature":        KEYWORDS_MATS["Feature"],
    "🦺 Arc Suits — Core":      KEYWORDS_ARC["Core"],
    "🦺 Arc Suits — Technical": KEYWORDS_ARC["Technical"],
    "🦺 Arc Suits — Standards": KEYWORDS_ARC["Standards"],
    "🦺 Arc Suits — Type":      KEYWORDS_ARC["Type"],
    "🦺 Arc Suits — Use Case":  KEYWORDS_ARC["Use Case"],
    "🦺 Arc Suits — Feature":   KEYWORDS_ARC["Feature"],
    "🌐 Common / Cross-Product": KEYWORDS_COMMON,
}

# ══════════════════════════════════════════════════════════════════
# RELEVANCE SCORING ENGINE
# Formula: Score = (KS × 0.4) + (CS × 0.3) + (IS × 0.3)
# ══════════════════════════════════════════════════════════════════

def compute_keyword_score(title, summary):
    """Component 1: Keyword Score (0–100)"""
    text_full  = (title + " " + summary).lower()
    text_title = title.lower()

    best_score    = 0
    best_type     = "Generic"
    matched_kws   = []
    high_val_count = 0

    for pattern, base_score, ktype in KEYWORD_SCORE_MAP:
        if pattern in text_full:
            matched_kws.append((pattern, base_score, ktype))
            if base_score > best_score:
                best_score = base_score
                best_type  = ktype
            if base_score >= 70:
                high_val_count += 1

    if not matched_kws:
        return 0, "None", []

    score = best_score

    # +10 if keyword appears in title
    for pattern, base_score, _ in matched_kws:
        if pattern in text_title and base_score == best_score:
            score += 10
            break

    # +10 if multiple high-value keywords present
    if high_val_count >= 2:
        score += 10

    return min(score, 100), best_type, matched_kws


def compute_competitor_score(title, summary):
    """Component 2: Competitor Score (0–100)"""
    text = (title + " " + summary).lower()

    direct_hits = [c for c in DIRECT_COMPETITORS if c in text]
    indirect    = any(s in text for s in INDIRECT_COMPETITOR_SIGNALS)

    if not direct_hits and not indirect:
        return 20, [], False

    score = 20
    bonus = False

    if direct_hits:
        score = 100
        if len(direct_hits) >= 2:
            score += 10   # competitive intensity bonus
            bonus = True
    elif indirect:
        score = 60

    return min(score, 100), direct_hits, bonus


def compute_intent_score_keyword(title, summary):
    """Keyword-based fallback intent scoring."""
    text = (title + " " + summary).lower()
    if any(k in text for k in ["new plant","expansion","invest","greenfield","brownfield","capacity"]):
        return 100, "Investment / Capacity Expansion"
    if any(k in text for k in ["acqui","merger","joint venture","partnership","stake","buyout","takeover"]):
        return 100, "M&A / Partnership"
    if any(k in text for k in ["launch","new product","new model","introduces","unveil","new range"]):
        return 90, "New Product Launch"
    if any(k in text for k in ["innovation","patent","r&d","technology","new material","fr fabric","composite"]):
        return 85, "Technology / Innovation"
    if any(k in text for k in ["regulat","standard","compliance","bis","qco","mandatory","norms","dgfasli","pgiel"]):
        return 80, "Regulatory / Compliance"
    if any(k in text for k in ["contract","order","supply deal","tender","award","procurement"]):
        return 75, "Large Order / Contract"
    if any(k in text for k in ["revenue","profit","earnings","quarter","results","turnover"]):
        return 40, "General News / Mention"
    return 40, "General News / Mention"


def final_relevance_score(kw_score, comp_score, intent_score,
                           w_kw=0.4, w_comp=0.3, w_intent=0.3):
    """Weighted formula: Score = (KS×0.4) + (CS×0.3) + (IS×0.3)"""
    raw = (kw_score * w_kw) + (comp_score * w_comp) + (intent_score * w_intent)
    return round(raw)


def score_label(score):
    if score >= 80: return "🔥 High",  "badge-high"
    if score >= 60: return "⚡ Medium", "badge-med"
    if score >= 40: return "🟡 Low",   "badge-low"
    return "❌ Ignore", "badge-ignore"


def score_bar_html(score):
    pct = min(score, 100)
    color = (
        "#ff7b72" if score >= 80 else
        "#ffa657" if score >= 60 else
        "#f7b731" if score >= 40 else
        "#484f58"
    )
    return (
        f'<div class="score-bar-wrap">'
        f'<div class="score-bar" style="width:{pct}%;background:{color};"></div>'
        f'</div>'
    )


def is_disqualified(title, summary, source):
    """Returns (True, reason) if article should be hard-removed."""
    text = (title + " " + summary + " " + source).lower()

    # Hard disqualifiers
    for d in HARD_DISQUALIFIERS:
        if d in text:
            return True, f"Blocked term: '{d}'"

    # Foreign-only check
    has_india   = any(s in text for s in INDIA_SIGNALS)
    has_foreign = any(s in text for s in FOREIGN_ONLY)
    if has_foreign and not has_india:
        return True, "Foreign market only — no India signal"

    return False, ""


# ══════════════════════════════════════════════════════════════════
# DEDUPLICATION
# ══════════════════════════════════════════════════════════════════

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def deduplicate(articles, threshold=0.80):
    """
    Remove duplicate articles using:
    1. Exact title match
    2. Fuzzy title similarity (≥80% match = duplicate)
    Keeps the article with the highest relevance score.
    """
    unique = []
    for article in articles:
        is_dup = False
        for kept in unique:
            sim = similar(article["title"], kept["title"])
            if sim >= threshold:
                # Keep the one with higher score
                if article.get("relevance", 0) > kept.get("relevance", 0):
                    unique.remove(kept)
                    unique.append(article)
                is_dup = True
                break
        if not is_dup:
            unique.append(article)
    return unique


# ══════════════════════════════════════════════════════════════════
# LLM INTENT CLASSIFICATION (Groq)
# ══════════════════════════════════════════════════════════════════

def classify_intent_llm(articles, api_key):
    """Use Groq to classify intent and extract key insight."""
    if not api_key:
        for a in articles:
            intent_score, intent = compute_intent_score_keyword(a["title"], a["summary"])
            a["intent"]       = intent
            a["intent_score"] = intent_score
            a["category"]     = INTENT_TO_CATEGORY.get(intent, "Other")
            a["key_insight"]  = "Add Groq API key for AI-powered insights"
        return articles

    client = Groq(api_key=api_key)
    intents_list = list(INTENT_SCORES.keys())

    for a in articles:
        prompt = f"""You are a market intelligence analyst for an electrical safety PPE manufacturer in India.
Products: electrical insulating gloves, rubber insulating mats, arc flash suits.
Competitors tracked: Honeywell, Salisbury, CATU, Novax, Ansell, DPL, MN Rubber, Jayco, Morning Pride.
Geography focus: INDIA market only.

Classify this article's intent into EXACTLY ONE of:
{json.dumps(intents_list)}

Write ONE key insight in max 12 words, India-market focused.

Title: {a['title']}
Summary: {a['summary']}

Reply ONLY in valid JSON (no markdown, no explanation):
{{"intent":"...","key_insight":"..."}}"""
        try:
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80, temperature=0.1,
            )
            result      = json.loads(resp.choices[0].message.content.strip())
            intent      = result.get("intent", "General News / Mention")
            if intent not in INTENT_SCORES:
                intent  = "General News / Mention"
            a["intent"]       = intent
            a["intent_score"] = INTENT_SCORES[intent]
            a["category"]     = INTENT_TO_CATEGORY.get(intent, "Other")
            a["key_insight"]  = result.get("key_insight", "—")

            # Recompute final score with LLM intent
            kw_s, _, _   = compute_keyword_score(a["title"], a["summary"])
            comp_s, _, _ = compute_competitor_score(a["title"], a["summary"])
            a["relevance"] = final_relevance_score(kw_s, comp_s, a["intent_score"])

        except Exception:
            intent_score, intent = compute_intent_score_keyword(a["title"], a["summary"])
            a["intent"]       = intent
            a["intent_score"] = intent_score
            a["category"]     = INTENT_TO_CATEGORY.get(intent, "Other")
            a["key_insight"]  = "—"
        time.sleep(0.3)
    return articles


# ══════════════════════════════════════════════════════════════════
# NEWS FETCH PIPELINE
# ══════════════════════════════════════════════════════════════════

def fetch_google_news(query, days_back=30):
    # Always append India to keep results India-focused
    india_query = f"{query} India" if "india" not in query.lower() else query
    encoded = urllib.parse.quote(india_query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
    feed   = feedparser.parse(url)
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
                "summary":   entry.get("summary", "")[:400],
                "query":     query,
            })
    return articles


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_news(queries_tuple, days_back, api_key):
    # 1. Fetch
    raw = []
    for q in queries_tuple:
        raw.extend(fetch_google_news(q, days_back))
        time.sleep(0.15)

    # 2. Hard disqualify first (fast, before scoring)
    kept, removed = [], []
    for a in raw:
        disq, reason = is_disqualified(a["title"], a["summary"], a["source"])
        if disq:
            a["discard_reason"] = reason
            removed.append(a)
        else:
            kept.append(a)

    # 3. Score each kept article (keyword + competitor; intent via LLM below)
    for a in kept:
        kw_score,  kw_type,  kw_hits  = compute_keyword_score(a["title"], a["summary"])
        comp_score, comp_hits, comp_bonus = compute_competitor_score(a["title"], a["summary"])
        intent_score, intent             = compute_intent_score_keyword(a["title"], a["summary"])
        final = final_relevance_score(kw_score, comp_score, intent_score)

        a["kw_score"]    = kw_score
        a["kw_type"]     = kw_type
        a["comp_score"]  = comp_score
        a["comp_hits"]   = comp_hits
        a["intent"]      = intent
        a["intent_score"]= intent_score
        a["relevance"]   = final
        a["category"]    = INTENT_TO_CATEGORY.get(intent, "Other")
        a["key_insight"] = ""
        a["score_breakdown"] = (
            f"KW:{kw_score}({kw_type}) × 0.4  +  "
            f"Comp:{comp_score}({'|'.join(comp_hits) if comp_hits else 'none'}) × 0.3  +  "
            f"Intent:{intent_score}({intent}) × 0.3  =  {final}"
        )

    # 4. Remove low-scoring articles (intent = Irrelevant or score < 20)
    kept = [a for a in kept if a["relevance"] >= 20 and a["intent"] != "Irrelevant"]

    # 5. Deduplicate using fuzzy title matching
    kept = deduplicate(kept, threshold=0.80)

    # 6. LLM intent refinement + key insight (only on kept articles)
    kept = classify_intent_llm(kept, api_key)

    # 7. Final sort by score
    kept.sort(key=lambda x: x["relevance"], reverse=True)

    return kept, removed


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


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚡ Intel Platform")
    st.markdown("**Electrical Safety PPE · 🇮🇳 India**")
    st.markdown('<div class="header-bar"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">🔑 API Key</div>', unsafe_allow_html=True)
    try:
        api_key = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        api_key = ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    st.markdown('<div class="section-head">🏭 Competitors</div>', unsafe_allow_html=True)
    sel_competitors = st.multiselect("Select competitors", COMPETITORS, default=COMPETITORS)
    new_co = st.text_input("➕ Add competitor", placeholder="e.g. Karam Industries")
    if new_co:
        sel_competitors.append(new_co)

    st.markdown('<div class="section-head">📦 Product Lines</div>', unsafe_allow_html=True)
    product_lines = st.multiselect(
        "Select product lines",
        ["🧤 Gloves", "🟫 Mats", "🦺 Arc Suits", "🌐 Common"],
        default=["🧤 Gloves", "🟫 Mats", "🦺 Arc Suits", "🌐 Common"],
    )
    available_groups = [
        g for g in ALL_KEYWORD_GROUPS
        if any(pl.split(" ")[0] in g for pl in product_lines) or "Common" in g
    ]
    sel_groups      = st.multiselect("Keyword groups", available_groups, default=available_groups)
    include_comp_kw = st.checkbox("Include competitor keywords", value=True)

    st.markdown('<div class="section-head">📅 Filters</div>', unsafe_allow_html=True)
    days_back      = st.slider("Days of news", 7, 90, 30)
    selected_cats  = st.multiselect("Categories", CATEGORIES, default=CATEGORIES)
    min_score      = st.slider("Min relevance score (0–100)", 0, 100, 40,
                               help="40+ = Low, 60+ = Medium, 80+ = High")
    show_discarded = st.checkbox("Audit discarded articles", value=False)

    st.markdown('<div class="section-head">⚖️ Score Weights</div>', unsafe_allow_html=True)
    w_kw     = st.slider("Keyword weight",    0.0, 1.0, 0.4, 0.05)
    w_comp   = st.slider("Competitor weight", 0.0, 1.0, 0.3, 0.05)
    w_intent = st.slider("Intent weight",     0.0, 1.0, 0.3, 0.05)
    total_w  = round(w_kw + w_comp + w_intent, 2)
    if abs(total_w - 1.0) > 0.05:
        st.warning(f"⚠️ Weights sum to {total_w} (should be 1.0)")

    fetch_btn = st.button("⚡ Fetch & Analyse News")


# ══════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════

st.markdown("# ⚡ Electrical Safety Market Intelligence")
st.markdown("*🇮🇳 India-focused · Gloves · Mats · Arc Suits · Weighted Relevance Scoring*")
st.markdown('<div class="header-bar"></div>', unsafe_allow_html=True)

# Formula banner
st.markdown("""
<div class="info-box">
<b>📐 Relevance Formula:</b> &nbsp;
Score = (Keyword Score × <b>0.4</b>) + (Competitor Score × <b>0.3</b>) + (Intent Score × <b>0.3</b>)
&nbsp;&nbsp;|&nbsp;&nbsp;
🔥 <b>80–100</b> Immediate attention &nbsp;
⚡ <b>60–79</b> Track &nbsp;
🟡 <b>40–59</b> Optional &nbsp;
❌ <b>&lt;40</b> Filtered out
</div>
""", unsafe_allow_html=True)

if fetch_btn or "intel_data" in st.session_state:
    if fetch_btn:
        queries = build_queries(sel_competitors, sel_groups, include_comp_kw)
        st.info(f"🔍 Running **{len(queries)} queries** — India-focused · deduplication ON · Salisbury Journal blocked")
        with st.spinner("Fetching, scoring & deduplicating…"):
            kept, removed = fetch_all_news(tuple(queries), days_back, api_key or "")
            # Re-apply custom weights from sidebar
            for a in kept:
                a["relevance"] = final_relevance_score(
                    a["kw_score"], a["comp_score"], a["intent_score"],
                    w_kw, w_comp, w_intent
                )
                a["score_breakdown"] = (
                    f"KW:{a['kw_score']}({a['kw_type']}) × {w_kw}  +  "
                    f"Comp:{a['comp_score']}({'|'.join(a['comp_hits']) if a['comp_hits'] else 'none'}) × {w_comp}  +  "
                    f"Intent:{a['intent_score']}({a['intent']}) × {w_intent}  =  {a['relevance']}"
                )
            kept.sort(key=lambda x: x["relevance"], reverse=True)
            st.session_state["intel_data"]   = kept
            st.session_state["removed_data"] = removed

    kept    = st.session_state.get("intel_data",   [])
    removed = st.session_state.get("removed_data", [])

    df     = pd.DataFrame(kept)
    df_rem = pd.DataFrame(removed)

    if df.empty:
        st.warning("No relevant articles found. Try a longer time range or adjust the min score slider.")
    else:
        df_f = df[
            df["category"].isin(selected_cats) &
            (df["relevance"] >= min_score)
        ].copy()

        # ── METRICS ──────────────────────────────────────────────
        c1,c2,c3,c4,c5 = st.columns(5)
        high_rel = len(df_f[df_f["relevance"] >= 80])
        for col, val, lbl in [
            (c1, len(df_f),                                          "Relevant Articles"),
            (c2, high_rel,                                           "🔥 High Priority"),
            (c3, len(removed),                                       "Auto-Filtered Out"),
            (c4, len(df_f[df_f["intent"]=="M&A / Partnership"]),    "M&A Signals"),
            (c5, round(df_f["relevance"].mean(),1) if len(df_f) else 0, "Avg Score"),
        ]:
            col.markdown(
                f'<div class="metric-card"><div class="metric-number">{val}</div>'
                f'<div class="metric-label">{lbl}</div></div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── CHARTS ───────────────────────────────────────────────
        ch1, ch2 = st.columns(2)
        with ch1:
            cat_df = df_f["category"].value_counts().reset_index()
            cat_df.columns = ["Category","Count"]
            fig = px.bar(cat_df, x="Count", y="Category", orientation="h",
                         color="Category", color_discrete_map=CATEGORY_COLORS,
                         title="📊 Articles by Intelligence Category")
            fig.update_layout(plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                font_color="#e6edf3", showlegend=False,
                margin=dict(l=10,r=10,t=40,b=10),
                xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
            st.plotly_chart(fig, use_container_width=True)

        with ch2:
            score_bins = pd.cut(df_f["relevance"],
                                bins=[0,39,59,79,100],
                                labels=["❌ <40","🟡 40–59","⚡ 60–79","🔥 80–100"])
            bin_df = score_bins.value_counts().reset_index()
            bin_df.columns = ["Band","Count"]
            band_colors = {"🔥 80–100":"#ff7b72","⚡ 60–79":"#ffa657",
                           "🟡 40–59":"#f7b731","❌ <40":"#484f58"}
            fig2 = px.bar(bin_df, x="Band", y="Count", color="Band",
                          color_discrete_map=band_colors,
                          title="📊 Relevance Score Distribution")
            fig2.update_layout(plot_bgcolor="#161b22", paper_bgcolor="#161b22",
                font_color="#e6edf3", showlegend=False,
                margin=dict(l=10,r=10,t=40,b=10),
                xaxis=dict(gridcolor="#30363d"), yaxis=dict(gridcolor="#30363d"))
            st.plotly_chart(fig2, use_container_width=True)

        # ── NEWS FEED ─────────────────────────────────────────────
        st.markdown("### 📰 Intelligence Feed")
        fc1, fc2, fc3 = st.columns([2,1,1])
        with fc1:
            search = st.text_input("🔎 Search", placeholder="e.g. Honeywell, IEC 60903, arc flash…")
        with fc2:
            all_glove_kw = [k for v in KEYWORDS_GLOVES.values() for k in v]
            all_mat_kw   = [k for v in KEYWORDS_MATS.values()   for k in v]
            all_arc_kw   = [k for v in KEYWORDS_ARC.values()    for k in v]
            filter_product = st.selectbox("Product line", ["All","Gloves","Mats","Arc Suits"])
        with fc3:
            show_breakdown = st.checkbox("Show score breakdown", value=False)

        if search:
            df_f = df_f[df_f["title"].str.contains(search, case=False, na=False)]
        if filter_product != "All":
            pm = {"Gloves": all_glove_kw, "Mats": all_mat_kw, "Arc Suits": all_arc_kw}
            df_f = df_f[df_f["query"].isin(pm[filter_product])]

        st.markdown(
            f"Showing **{len(df_f)}** articles · "
            f"**{len(removed)}** auto-removed · "
            f"Sorted by relevance score ↓"
        )

        for _, row in df_f.iterrows():
            bc            = BADGE_CLASS.get(row.get("category","Other"), "badge-oth")
            score         = row.get("relevance", 0)
            slabel, sbadge = score_label(score)
            bar           = score_bar_html(score)
            breakdown     = row.get("score_breakdown","—")
            comp_hits_str = ", ".join(row.get("comp_hits",[])) or "none"

            st.markdown(f"""
            <div class="news-card">
                <div class="news-title">
                    <a href="{row['link']}" target="_blank"
                       style="color:#e6edf3;text-decoration:none;">{row['title']}</a>
                </div>
                <div style="margin:6px 0 2px 0;">
                    <span class="badge {bc}">{row.get('category','—')}</span>
                    <span class="badge {sbadge}">{slabel} &nbsp;{score}/100</span>
                    <span class="badge" style="background:#1c2128;color:#8b949e;border:1px solid #30363d;">
                        🏭 {comp_hits_str}
                    </span>
                </div>
                {bar}
                <div class="news-meta">
                    🗞️ {row['source']} &nbsp;|&nbsp;
                    📅 {row['published'].strftime('%d %b %Y')} &nbsp;|&nbsp;
                    🎯 Intent: {row.get('intent','—')} &nbsp;|&nbsp;
                    💡 {row.get('key_insight','—')}
                </div>
                {"<div class='score-breakdown'>📐 " + breakdown + "</div>" if show_breakdown else ""}
            </div>""", unsafe_allow_html=True)

        # ── DISCARDED ─────────────────────────────────────────────
        if show_discarded and not df_rem.empty:
            st.markdown("---")
            st.markdown(f"### ❌ Auto-Discarded Articles ({len(df_rem)})")
            for _, row in df_rem.iterrows():
                st.markdown(f"""
                <div class="news-card" style="border-left:3px solid #484f58;opacity:0.5;">
                    <div class="news-title" style="color:#8b949e;">{row['title']}</div>
                    <div class="news-meta">❌ {row.get('discard_reason','—')} &nbsp;|&nbsp; 🗞️ {row['source']}</div>
                </div>""", unsafe_allow_html=True)

        # ── EXPORT ────────────────────────────────────────────────
        st.markdown("### 📥 Export")
        ec1, ec2 = st.columns(2)
        export_cols = ["title","category","relevance","intent","intent_score",
                       "kw_score","comp_score","comp_hits","key_insight",
                       "score_breakdown","source","published","link"]
        out = df_f[[c for c in export_cols if c in df_f.columns]].copy()
        out["published"] = out["published"].dt.strftime("%Y-%m-%d")
        full = df[[c for c in export_cols if c in df.columns]].copy()
        full["published"] = full["published"].dt.strftime("%Y-%m-%d")
        with ec1:
            st.download_button("⬇️ Filtered CSV", out.to_csv(index=False),
                f"intel_filtered_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
        with ec2:
            st.download_button("⬇️ Full CSV", full.to_csv(index=False),
                f"intel_full_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")

else:
    # Landing page
    st.info("👈 Configure settings in the sidebar, then click **⚡ Fetch & Analyse News**")

    st.markdown("### 📐 Relevance Score Formula")
    st.markdown("""
    <div class="info-box">
    <b>Score = (Keyword Score × 0.4) + (Competitor Score × 0.3) + (Intent Score × 0.3)</b><br><br>
    <b>Component 1 — Keyword Score (0–100)</b><br>
    &nbsp;&nbsp;Brand + Product (e.g. Salisbury arc flash suit) → 100 &nbsp;|&nbsp;
    Standard (IEC/ASTM/NFPA) → 90 &nbsp;|&nbsp; Spec (Class/kV/cal) → 80<br>
    &nbsp;&nbsp;Core product (arc suit, gloves, mat) → 70 &nbsp;|&nbsp;
    Technical/feature (FR fabric) → 50 &nbsp;|&nbsp; Generic → 20<br>
    &nbsp;&nbsp;+10 if keyword in title &nbsp;|&nbsp; +10 if 2+ high-value keywords<br><br>
    <b>Component 2 — Competitor Score (0–100)</b><br>
    &nbsp;&nbsp;Direct competitor (Honeywell, CATU…) → 100 &nbsp;|&nbsp;
    Indirect mention → 60 &nbsp;|&nbsp; No mention → 20 &nbsp;|&nbsp; 2+ competitors → +10<br><br>
    <b>Component 3 — Intent Score (0–100) — Most Important</b><br>
    &nbsp;&nbsp;Investment/Capacity or M&A → 100 &nbsp;|&nbsp; New Product → 90 &nbsp;|&nbsp;
    Technology → 85 &nbsp;|&nbsp; Regulatory → 80 &nbsp;|&nbsp; Contract → 75 &nbsp;|&nbsp; General → 40<br><br>
    <b>❌ Hard Disqualifiers (auto-removed before scoring):</b><br>
    &nbsp;&nbsp;Salisbury Journal/News/University &nbsp;|&nbsp; Unrelated safety (fire, fall, helmets) &nbsp;|&nbsp;
    Consumer electronics &nbsp;|&nbsp; Academic journals &nbsp;|&nbsp; Foreign market with no India mention
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏭 Competitors Tracked")
    comp_cols = st.columns(5)
    for i, co in enumerate(COMPETITORS):
        with comp_cols[i % 5]:
            st.markdown(
                f'<div class="metric-card" style="padding:10px;margin-bottom:8px;">'
                f'<div style="font-size:0.8rem;color:#e6edf3;font-weight:600;">{co}</div></div>',
                unsafe_allow_html=True
            )
