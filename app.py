import streamlit as st
import feedparser
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from datetime import datetime, timedelta
import urllib.parse
import time
import json
from difflib import SequenceMatcher

# ══════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SafeIntel · Electrical Safety India",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════
# BOLD & VIBRANT CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;1,400&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #05060f; color: #f0f0ff; }

/* ── TOP NAV ───────────────────────────────────────────────── */
.topnav {
    display: flex; align-items: center; gap: 0;
    padding: 0 20px;
    background: rgba(8,8,24,0.97);
    border-bottom: 1px solid rgba(255,255,255,0.07);
    height: 54px;
    position: sticky; top: 0; z-index: 999;
    backdrop-filter: blur(16px);
    margin-bottom: 0;
}
.nav-logo {
    font-family: 'Syne', sans-serif; font-weight: 800;
    font-size: 1rem; letter-spacing: 1.5px; color: #fff;
    margin-right: 28px; display: flex; align-items: center; gap: 8px;
    white-space: nowrap;
}
.nav-bolt {
    width: 30px; height: 30px;
    background: linear-gradient(135deg, #f7b731, #ff5e62);
    border-radius: 7px; display: flex; align-items: center;
    justify-content: center; font-size: 0.9rem;
}
.nav-tab {
    padding: 0 16px; height: 54px; display: flex; align-items: center;
    font-size: 0.78rem; font-weight: 500; color: #666; cursor: pointer;
    border-bottom: 2px solid transparent; transition: all 0.2s;
    white-space: nowrap; user-select: none;
}
.nav-tab:hover { color: #ccc; }
.nav-tab.active { color: #fff; border-bottom: 2px solid #f7b731; }
.nav-right { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.nav-pill {
    background: linear-gradient(135deg,rgba(247,183,49,0.15),rgba(255,94,98,0.15));
    border: 1px solid rgba(247,183,49,0.3);
    color: #f7b731; font-size: 0.65rem; font-weight: 700;
    padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px;
}
.nav-btn {
    background: linear-gradient(135deg, #f7b731, #ff5e62);
    color: #000; border: none; padding: 7px 16px;
    border-radius: 8px; font-size: 0.78rem; font-weight: 700;
    cursor: pointer; letter-spacing: 0.3px; font-family: 'DM Sans', sans-serif;
}

/* ── HERO STRIP ────────────────────────────────────────────── */
.hero {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #1a1040 100%);
    padding: 24px 28px 18px; position: relative; overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; top:-60px; right:-40px;
    width:260px; height:260px;
    background: radial-gradient(circle, rgba(247,183,49,0.12), transparent 70%);
    border-radius: 50%;
}
.hero::after {
    content: ''; position: absolute; bottom:-40px; left:35%;
    width:200px; height:200px;
    background: radial-gradient(circle, rgba(255,94,98,0.10), transparent 70%);
    border-radius: 50%;
}
.hero-title {
    font-family: 'Syne', sans-serif; font-size: 1.45rem; font-weight: 800;
    background: linear-gradient(90deg, #fff 30%, #f7b731 65%, #ff5e62 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 4px; line-height: 1.2;
}
.hero-sub { font-size: 0.75rem; color: #777; letter-spacing: 0.4px; }
.hero-pills { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
.hero-pill {
    background: rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1);
    border-radius:20px; padding:3px 12px; font-size:0.65rem; color:#999;
}
.hero-pill.on { background:rgba(247,183,49,0.12); border-color:rgba(247,183,49,0.4); color:#f7b731; }

/* ── PAGE TABS ─────────────────────────────────────────────── */
.page { display: none; }
.page.active { display: block; }

/* ── METRIC CARDS ──────────────────────────────────────────── */
.metrics { display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin-bottom:20px; }
.mcard {
    border-radius:13px; padding:16px 14px; position:relative; overflow:hidden;
    cursor:default;
}
.mcard::after {
    content:''; position:absolute; top:0; left:0; right:0;
    height:3px; border-radius:13px 13px 0 0;
}
.mc1{background:linear-gradient(135deg,#1a1040,#2d1b69);}
.mc1::after{background:linear-gradient(90deg,#7c3aed,#a78bfa);}
.mc2{background:linear-gradient(135deg,#200a0a,#6b0f1a);}
.mc2::after{background:linear-gradient(90deg,#ff5e62,#ff9966);}
.mc3{background:linear-gradient(135deg,#051a10,#064e3b);}
.mc3::after{background:linear-gradient(90deg,#10b981,#34d399);}
.mc4{background:linear-gradient(135deg,#1a1000,#78350f);}
.mc4::after{background:linear-gradient(90deg,#f59e0b,#fcd34d);}
.mc5{background:linear-gradient(135deg,#050e1f,#1e3a5f);}
.mc5::after{background:linear-gradient(90deg,#3b82f6,#93c5fd);}
.mnum{font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;line-height:1;}
.mc1 .mnum{color:#a78bfa;} .mc2 .mnum{color:#ff8585;}
.mc3 .mnum{color:#34d399;} .mc4 .mnum{color:#fcd34d;}
.mc5 .mnum{color:#93c5fd;}
.mlbl{font-size:0.62rem;text-transform:uppercase;letter-spacing:1.5px;color:#555;margin-top:4px;}
.mdelta{font-size:0.68rem;color:#34d399;margin-top:3px;}

/* ── CHART CARDS ───────────────────────────────────────────── */
.chart-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 16px;
}
.chart-title {
    font-family:'Syne',sans-serif; font-size:0.82rem;
    font-weight:700; margin-bottom:12px; color:#e0e0ff;
}

/* ── NEWS CARDS ────────────────────────────────────────────── */
.ncard {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 13px; padding: 14px 16px; margin-bottom: 10px;
    display: flex; gap: 14px; align-items: flex-start;
    transition: border-color 0.2s, background 0.2s;
}
.ncard:hover {
    border-color: rgba(247,183,49,0.25);
    background: rgba(247,183,49,0.03);
}
.score-ring {
    flex-shrink:0; width:46px; height:46px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-family:'Syne',sans-serif; font-weight:800; font-size:0.8rem;
}
.ring-high{background:linear-gradient(135deg,#ff5e62,#ff9966);color:#fff;}
.ring-med {background:linear-gradient(135deg,#f59e0b,#fcd34d);color:#000;}
.ring-low {background:rgba(255,255,255,0.06);color:#888;border:1px solid #2a2a2a;}
.ring-ignore{background:#111;color:#444;border:1px solid #222;}
.ntitle{font-size:0.88rem;font-weight:600;color:#e8e8ff;margin-bottom:5px;line-height:1.4;}
.nbadges{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:5px;}
.nbadge{font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:20px;
        letter-spacing:0.5px;text-transform:uppercase;}
.nb-ma   {background:rgba(124,58,237,0.18);color:#a78bfa;border:1px solid rgba(124,58,237,0.3);}
.nb-cap  {background:rgba(59,130,246,0.15);color:#93c5fd;border:1px solid rgba(59,130,246,0.3);}
.nb-tech {background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);}
.nb-prod {background:rgba(245,158,11,0.15);color:#fcd34d;border:1px solid rgba(245,158,11,0.3);}
.nb-reg  {background:rgba(255,94,98,0.15);color:#ff8585;border:1px solid rgba(255,94,98,0.3);}
.nb-mkt  {background:rgba(6,182,212,0.15);color:#67e8f9;border:1px solid rgba(6,182,212,0.3);}
.nb-fin  {background:rgba(52,211,153,0.12);color:#6ee7b7;border:1px solid rgba(52,211,153,0.3);}
.nb-oth  {background:rgba(255,255,255,0.05);color:#888;border:1px solid #2a2a2a;}
.nb-high {background:linear-gradient(135deg,rgba(255,94,98,0.2),rgba(255,153,102,0.2));
          color:#ff8585;border:1px solid rgba(255,94,98,0.35);}
.nb-med  {background:rgba(245,158,11,0.15);color:#fcd34d;border:1px solid rgba(245,158,11,0.3);}
.nb-low  {background:rgba(255,255,255,0.05);color:#aaa;border:1px solid #333;}
.nb-comp {background:rgba(167,139,250,0.15);color:#c4b5fd;border:1px solid rgba(167,139,250,0.3);}
.nmeta{font-size:0.65rem;color:#4a4a6a;line-height:1.7;}
.sbar-wrap{background:rgba(255,255,255,0.05);border-radius:4px;height:4px;margin:5px 0 2px 0;}
.sbar{height:4px;border-radius:4px;}
.score-breakdown{
    background:#0a0a1a;border:1px solid #1a1a2e;border-radius:6px;
    padding:7px 12px;font-size:0.65rem;color:#555;margin-top:6px;
    font-family:'DM Sans',monospace;line-height:1.6;
}

/* ── SECTION TITLE ─────────────────────────────────────────── */
.sec-title{
    font-family:'Syne',sans-serif;font-size:0.9rem;font-weight:700;
    color:#e0e0ff;margin-bottom:14px;margin-top:4px;
}

/* ── COMPETITOR CARD ───────────────────────────────────────── */
.comp-card{
    border-radius:12px;padding:16px;margin-bottom:10px;
    border:1px solid rgba(255,255,255,0.07);
    background:rgba(255,255,255,0.025);
}

/* ── INFO BOX ──────────────────────────────────────────────── */
.info-box{
    background:rgba(247,183,49,0.06);border:1px solid rgba(247,183,49,0.2);
    border-radius:10px;padding:12px 16px;font-size:0.78rem;
    color:#bbb;margin-bottom:16px;line-height:1.8;
}

/* ── SIDEBAR ───────────────────────────────────────────────── */
.section-head{
    font-family:'Syne',sans-serif;font-size:0.65rem;text-transform:uppercase;
    letter-spacing:1.8px;color:#f7b731;margin:16px 0 6px 0;
    border-bottom:1px solid rgba(247,183,49,0.2);padding-bottom:4px;
}
div[data-testid="stSidebarContent"]{background:#07071a;border-right:1px solid rgba(255,255,255,0.06);}
.stButton>button{
    background:linear-gradient(135deg,#f7b731,#ff5e62) !important;
    color:#000 !important;border:none !important;font-weight:700 !important;
    border-radius:8px !important;width:100% !important;letter-spacing:0.3px !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MASTER DATA
# ══════════════════════════════════════════════════════════════════

COMPETITORS = [
    "Honeywell Safety","Honeywell Salisbury","Salisbury",
    "CATU","Novax","Ansell","DPL","MN Rubber","Jayco","Morning Pride",
]
COMPETITOR_NAMES_LOWER = [
    "honeywell","salisbury","catu","novax","ansell",
    "dpl","mn rubber","jayco","morning pride",
]

# ── ELECTRICAL SAFETY PRODUCT UNIVERSE (the only universe we care about)
ELECTRICAL_SAFETY_PRODUCTS = [
    # Gloves
    "insulating glove","electrical glove","rubber glove insulating",
    "dielectric glove","high voltage glove","lineman glove",
    "class 0 glove","class 1 glove","class 2 glove","class 3 glove","class 4 glove",
    "class 00 glove","live line glove","arc rated glove","arc flash glove",
    "voltage rated glove","electrician glove","electrical safety glove",
    "rubber insulating glove","low voltage glove",
    # Mats
    "insulating mat","electrical mat","dielectric mat","rubber mat electrical",
    "switchboard mat","panel mat","substation mat","anti shock mat",
    "electrical floor mat","insulating matting",
    # Arc Suits
    "arc flash suit","arc flash ppe","arc rated suit","arc flash coverall",
    "arc flash protection","arc flash clothing","arc flash jacket",
    "arc flash hood","arc flash helmet","arc flash face shield",
    "flame resistant suit","fr suit","arc flash balaclava",
    # Cross-product electrical safety
    "electrical ppe","electrical safety equipment","live line ppe",
    "high voltage ppe","electrical protective equipment",
    "electrical safety gear","substation safety","switchgear safety",
    "electrical insulation","dielectric protection",
]

# ── ELECTRICAL SAFETY STANDARDS UNIVERSE
ELECTRICAL_STANDARDS = [
    "iec 60903","en 60903","astm d120","astm f2675","is 4770",
    "iec 61111","is 15652","astm f696",
    "iec 61482","astm f1506","nfpa 70e","atpv","cal/cm2",
    "osha 1910.137","ansi z535",
]

# ── COMPETITOR-SPECIFIC PHRASES
COMPETITOR_PRODUCT_PHRASES = [
    "salisbury arc flash","salisbury insulating glove","salisbury insulating mat",
    "salisbury class","salisbury rubber glove",
    "honeywell arc flash","honeywell insulating glove","honeywell insulating mat",
    "honeywell electrical safety","honeywell ppe electrical",
    "catu arc flash","catu insulating glove","catu insulating mat",
    "catu iec 60903","catu class",
    "novax insulating glove","novax rubber insulating","novax class",
    "novax astm d120","novax electrical",
    "ansell arc flash","ansell electrical glove","ansell insulating",
    "dpl insulating glove","dpl rubber mat","dpl arc flash","dpl electrical",
    "mn rubber electrical","mn rubber insulating","mn rubber glove",
    "jayco insulating","jayco arc flash","jayco electrical glove",
    "morning pride arc flash","morning pride electrical",
]

# ── INDIA SIGNALS
INDIA_SIGNALS = [
    "india","indian","bharat","mumbai","delhi","bangalore","bengaluru",
    "chennai","hyderabad","pune","kolkata","gujarat","maharashtra",
    "rajasthan","uttar pradesh","tamil nadu",
    "bis ","bureau of indian standards","is 4770","is 15652",
    "cea ","dgfasli","pgiel","bqco","make in india","atmanirbhar",
    "msme","rupee","₹","inr","ntpc","bhel","ongc","powergrid",
    "tata power","adani power","torrent power","cesc","bses","wbsedcl",
]

# ══════════════════════════════════════════════════════════════════
# HARD DISQUALIFIERS — Removed BEFORE scoring
# These are terms that indicate articles are definitely NOT about
# electrical safety PPE (gloves/mats/arc suits)
# ══════════════════════════════════════════════════════════════════

# 1. Competitor mentioned but paired with UNRELATED product/sector
COMPETITOR_UNRELATED_PAIRS = [
    # Honeywell non-electrical-safety products
    ("honeywell","thermostat"),("honeywell","hvac"),("honeywell","building automation"),
    ("honeywell","aircraft"),("honeywell","aerospace"),("honeywell","defense"),
    ("honeywell","gas detection"),("honeywell","fire alarm"),
    ("honeywell","process control"),("honeywell","refrigerant"),
    ("honeywell","smart home"),("honeywell","security system"),
    # Ansell non-electrical-safety
    ("ansell","surgical glove"),("ansell","medical glove"),("ansell","exam glove"),
    ("ansell","food handling"),("ansell","chemical protection"),
    ("ansell","cut resistant"),("ansell","nitrile glove"),
    # Generic safety that is NOT electrical
    ("salisbury","wiltshire"),("salisbury","cathedral"),("salisbury","university"),
    ("salisbury","hospital"),("salisbury","journal"),("salisbury","newspaper"),
    ("salisbury","poisoning"),("salisbury","novichok"),("salisbury","uk town"),
    ("salisbury","maryland"),("salisbury","plain"),("salisbury","museum"),
    ("salisbury","steak"),("salisbury","city"),
]

# 2. Pure unrelated safety categories — only block if NO electrical safety keyword present
UNRELATED_SAFETY_ONLY = [
    "fall protection harness","safety harness fall","hard hat manufacturer",
    "safety helmet manufacturer","industrial hearing protection",
    "respiratory protection manufacturer","gas mask manufacturer",
    "safety footwear manufacturer","safety boot manufacturer",
    "fire safety equipment manufacturer","fire suppression system",
    "fall arrest system","scaffolding safety",
]

# 3. Consumer/non-industrial electricals — always block
CONSUMER_ELECTRICAL = [
    "led lighting","led bulb","home appliance","consumer electronics",
    "smartphone","laptop","television","washing machine","refrigerator",
    "air conditioner","microwave","ev battery pack","battery management",
    "solar panel","solar inverter","ups system",
]

# 4. Academic/journal — always block
ACADEMIC_SIGNALS = [
    "journal of","doi:","pubmed","elsevier","springer nature",
    "ieee xplore","sciencedirect","research paper abstract",
    "peer reviewed","scholarly article",
]

# 5. Strictly non-India foreign markets with no India mention
FOREIGN_ONLY = [
    "u.s. market only","us market only","north american market",
    "european market only","uk market only","german market only",
]

# ══════════════════════════════════════════════════════════════════
# KEYWORD SCORING MAP
# ══════════════════════════════════════════════════════════════════

KEYWORD_SCORE_MAP = [
    # Brand + Product combos → 100
    ("salisbury arc flash",100,"Brand+Product"),
    ("salisbury insulating glove",100,"Brand+Product"),
    ("salisbury insulating mat",100,"Brand+Product"),
    ("honeywell arc flash",100,"Brand+Product"),
    ("honeywell insulating glove",100,"Brand+Product"),
    ("honeywell insulating mat",100,"Brand+Product"),
    ("catu arc flash",100,"Brand+Product"),
    ("catu insulating glove",100,"Brand+Product"),
    ("catu insulating mat",100,"Brand+Product"),
    ("novax insulating glove",100,"Brand+Product"),
    ("novax rubber insulating",100,"Brand+Product"),
    ("ansell arc flash",100,"Brand+Product"),
    ("ansell electrical glove",100,"Brand+Product"),
    ("dpl insulating glove",100,"Brand+Product"),
    ("dpl rubber mat",100,"Brand+Product"),
    ("mn rubber electrical",100,"Brand+Product"),
    ("mn rubber insulating",100,"Brand+Product"),
    ("jayco insulating",100,"Brand+Product"),
    ("morning pride arc",100,"Brand+Product"),
    # Standards → 90
    ("iec 60903",90,"Standard"),("iec 61111",90,"Standard"),
    ("iec 61482",90,"Standard"),("astm d120",90,"Standard"),
    ("astm f1506",90,"Standard"),("astm f2675",90,"Standard"),
    ("nfpa 70e",90,"Standard"),("is 4770",90,"Standard"),
    ("is 15652",90,"Standard"),("en 60903",90,"Standard"),
    ("osha 1910.137",90,"Standard"),
    # Specs → 80
    ("class 00 glove",80,"Spec"),("class 0 glove",80,"Spec"),
    ("class 1 glove",80,"Spec"),("class 2 glove",80,"Spec"),
    ("class 3 glove",80,"Spec"),("class 4 glove",80,"Spec"),
    ("class a mat",80,"Spec"),("class b mat",80,"Spec"),
    ("class c mat",80,"Spec"),
    ("11kv glove",80,"Spec"),("33kv glove",80,"Spec"),
    ("36kv glove",80,"Spec"),("11kv mat",80,"Spec"),("33kv mat",80,"Spec"),
    ("8 cal",80,"Spec"),("25 cal",80,"Spec"),("40 cal",80,"Spec"),
    ("cal/cm2",80,"Spec"),("atpv",80,"Spec"),
    # Core products → 70
    ("arc flash suit",70,"Core Product"),("arc flash ppe",70,"Core Product"),
    ("arc flash protection",70,"Core Product"),("arc rated suit",70,"Core Product"),
    ("arc flash coverall",70,"Core Product"),("arc flash clothing",70,"Core Product"),
    ("insulating glove",70,"Core Product"),("electrical insulating glove",70,"Core Product"),
    ("rubber insulating glove",70,"Core Product"),("dielectric glove",70,"Core Product"),
    ("high voltage glove",70,"Core Product"),("electrical safety glove",70,"Core Product"),
    ("insulating mat",70,"Core Product"),("dielectric mat",70,"Core Product"),
    ("switchboard mat",70,"Core Product"),("electrical safety mat",70,"Core Product"),
    ("rubber mat electrical",70,"Core Product"),
    # Technical/Feature → 50
    ("fr fabric",50,"Technical"),("flame resistant",50,"Technical"),
    ("fire retardant",50,"Technical"),("arc rated",50,"Technical"),
    ("dielectric",50,"Technical"),("live line",50,"Technical"),
    ("energized work",50,"Technical"),("electrical hazard",50,"Technical"),
    ("ozone resistant glove",50,"Technical"),("anti shock mat",50,"Technical"),
    ("voltage rated",50,"Technical"),("electrical ppe",50,"Technical"),
    ("lineman glove",50,"Technical"),("substation safety",50,"Technical"),
    ("switchgear safety",50,"Technical"),("high voltage ppe",50,"Technical"),
    # Generic → 20
    ("safety equipment",20,"Generic"),("industrial safety",20,"Generic"),
    ("protective equipment",20,"Generic"),("electrical safety",20,"Generic"),
]

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
    "M&A / Partnerships","Capacity Development","Technology Update",
    "New Product Launch","Regulatory Change","Market Expansion",
    "Financial Results","Other",
]
CAT_BADGE = {
    "M&A / Partnerships":"nb-ma","Capacity Development":"nb-cap",
    "Technology Update":"nb-tech","New Product Launch":"nb-prod",
    "Regulatory Change":"nb-reg","Market Expansion":"nb-mkt",
    "Financial Results":"nb-fin","Other":"nb-oth",
}
CAT_COLORS = {
    "M&A / Partnerships":"#a78bfa","Capacity Development":"#93c5fd",
    "Technology Update":"#34d399","New Product Launch":"#fcd34d",
    "Regulatory Change":"#ff8585","Market Expansion":"#67e8f9",
    "Financial Results":"#6ee7b7","Other":"#555",
}

KEYWORDS_GLOVES = {
    "Core":["electrical safety gloves","electrical insulating gloves","rubber insulating gloves","electrician gloves","high voltage gloves","low voltage gloves","dielectric gloves","shock proof gloves"],
    "Technical":["voltage rated gloves","dielectric rubber gloves","electrical PPE gloves","live line gloves","arc flash gloves","arc rated gloves","energized work gloves"],
    "Standards":["IEC 60903 gloves","ASTM D120 gloves","IS 4770 electrical gloves","NFPA 70E gloves","EN 60903 gloves"],
    "Class":["Class 00 gloves","Class 0 gloves","Class 1 gloves","Class 2 gloves","Class 3 gloves","Class 4 gloves"],
    "Voltage":["11kV gloves","33kV gloves","500V gloves","high voltage insulating gloves","medium voltage gloves"],
    "Use Case":["lineman gloves","substation gloves","switchgear gloves","maintenance electrician gloves","transmission line gloves","EV maintenance gloves"],
    "Feature":["arc flash rated gloves","flame resistant gloves","ozone resistant gloves","oil resistant electrical gloves"],
}
KEYWORDS_MATS = {
    "Core":["electrical safety mat","insulating rubber mat","electrical insulating mat","dielectric mat","switchboard mat"],
    "Technical":["rubber insulating matting","anti shock mat","electrical protection mat","electrical floor mat","panel room mat"],
    "Standards":["IEC 61111 mat","IS 15652 mat","ASTM insulating mat"],
    "Voltage":["11kV mat","33kV mat","high voltage insulating mat"],
    "Use Case":["switchgear mat","transformer room mat","control panel mat","substation mat","HT panel mat","LT panel mat"],
    "Feature":["anti skid electrical mat","flame retardant mat","corrugated rubber mat","non conductive mat"],
}
KEYWORDS_ARC = {
    "Core":["arc flash suit","arc flash PPE","arc flash protection suit","arc rated suit"],
    "Technical":["arc flash clothing","arc flash protective clothing","arc flash coverall"],
    "Standards":["NFPA 70E arc flash suit","IEC 61482 arc flash suit","ASTM F1506 arc flash","8 cal arc flash suit","25 cal arc flash suit"],
    "Type":["arc flash hood","arc flash face shield","arc flash helmet","arc flash jacket","arc flash balaclava"],
    "Use Case":["substation arc flash suit","switchgear arc flash PPE","electrical maintenance PPE","high voltage PPE suit"],
    "Feature":["flame resistant suit","fire retardant suit","arc rated clothing"],
}
KEYWORDS_COMMON = [
    "electrical PPE India","electrical safety equipment India",
    "live line PPE India","high voltage safety equipment India","electrical safety India",
]
COMPETITOR_KEYWORDS = [
    "Salisbury arc flash suit","Salisbury insulating gloves","Salisbury insulating mats",
    "Honeywell electrical gloves India","Honeywell arc flash PPE India",
    "CATU insulating gloves","CATU arc flash suit","CATU IEC 60903 gloves",
    "Novax electrical gloves","Novax rubber insulating gloves","Novax Class 0 gloves",
    "Ansell electrical gloves India","Ansell arc flash PPE India",
    "DPL electrical gloves","DPL insulating gloves","DPL rubber mats",
    "MN Rubber electrical gloves","MN Rubber insulating mats",
    "Jayco electrical gloves","Jayco insulating mats","Jayco arc flash PPE",
    "Morning Pride arc flash suit",
]
ALL_KEYWORD_GROUPS = {
    "🧤 Gloves — Core":KEYWORDS_GLOVES["Core"],
    "🧤 Gloves — Technical":KEYWORDS_GLOVES["Technical"],
    "🧤 Gloves — Standards":KEYWORDS_GLOVES["Standards"],
    "🧤 Gloves — Class":KEYWORDS_GLOVES["Class"],
    "🧤 Gloves — Voltage":KEYWORDS_GLOVES["Voltage"],
    "🧤 Gloves — Use Case":KEYWORDS_GLOVES["Use Case"],
    "🧤 Gloves — Feature":KEYWORDS_GLOVES["Feature"],
    "🟫 Mats — Core":KEYWORDS_MATS["Core"],
    "🟫 Mats — Technical":KEYWORDS_MATS["Technical"],
    "🟫 Mats — Standards":KEYWORDS_MATS["Standards"],
    "🟫 Mats — Voltage":KEYWORDS_MATS["Voltage"],
    "🟫 Mats — Use Case":KEYWORDS_MATS["Use Case"],
    "🟫 Mats — Feature":KEYWORDS_MATS["Feature"],
    "🦺 Arc Suits — Core":KEYWORDS_ARC["Core"],
    "🦺 Arc Suits — Technical":KEYWORDS_ARC["Technical"],
    "🦺 Arc Suits — Standards":KEYWORDS_ARC["Standards"],
    "🦺 Arc Suits — Type":KEYWORDS_ARC["Type"],
    "🦺 Arc Suits — Use Case":KEYWORDS_ARC["Use Case"],
    "🦺 Arc Suits — Feature":KEYWORDS_ARC["Feature"],
    "🌐 Common":KEYWORDS_COMMON,
}

ALL_GLOVE_KW  = [k for v in KEYWORDS_GLOVES.values() for k in v]
ALL_MAT_KW    = [k for v in KEYWORDS_MATS.values()   for k in v]
ALL_ARC_KW    = [k for v in KEYWORDS_ARC.values()    for k in v]

# ══════════════════════════════════════════════════════════════════
# RELEVANCE LOGIC (Fixed per user's 3 rules)
# ══════════════════════════════════════════════════════════════════

def has_electrical_safety_content(text):
    """True if text mentions any product/standard in our universe."""
    for kw in ELECTRICAL_SAFETY_PRODUCTS + ELECTRICAL_STANDARDS:
        if kw in text:
            return True
    return False

def get_competitor_hits(text):
    return [c for c in COMPETITOR_NAMES_LOWER if c in text]

def get_product_hits(text):
    return [p for p in ELECTRICAL_SAFETY_PRODUCTS if p in text]

def get_standard_hits(text):
    return [s for s in ELECTRICAL_STANDARDS if s in text]

def is_relevant_article(title, summary):
    """
    NEW RELEVANCE LOGIC (3 rules):
    Rule 1: Competitor + (another competitor OR product OR keyword) → RELEVANT
    Rule 2: No competitor but has electrical safety product/standard keyword → RELEVANT
    Rule 3: Must stay strictly within electrical safety keyword universe
    """
    text = (title + " " + summary).lower()

    comp_hits    = get_competitor_hits(text)
    product_hits = get_product_hits(text)
    std_hits     = get_standard_hits(text)

    has_comp     = len(comp_hits) > 0
    has_product  = len(product_hits) > 0
    has_standard = len(std_hits) > 0

    # Rule 1: Competitor + (another competitor OR product OR standard keyword)
    if has_comp and (len(comp_hits) >= 2 or has_product or has_standard):
        return True, comp_hits, product_hits

    # Rule 2: No competitor needed if article is squarely about our products/standards
    if (has_product or has_standard) and not has_comp:
        # Must have at least 2 product/standard signals OR one strong signal
        strong = [p for p in product_hits if any(
            p in k[0] for k in KEYWORD_SCORE_MAP if k[1] >= 70
        )]
        if len(strong) >= 1 or len(product_hits) + len(std_hits) >= 2:
            return True, comp_hits, product_hits

    # Rule 1 variant: Competitor alone (single mention) with electrical safety context
    if has_comp and has_electrical_safety_content(text):
        return True, comp_hits, product_hits

    return False, comp_hits, product_hits


def is_disqualified(title, summary, source):
    """
    Hard remove — but ONLY if the article is clearly not about
    electrical safety gloves/mats/arc suits.
    Smart check: if article has electrical safety content → don't disqualify.
    """
    text  = (title + " " + summary + " " + source).lower()
    title_lower = title.lower()

    # Always block Salisbury non-product references
    salisbury_blocks = [
        "salisbury journal","salisbury news","salisbury post",
        "the salisbury","salisbury university","salisbury cathedral",
        "salisbury plain","salisbury poisoning","salisbury novichok",
        "salisbury uk","salisbury maryland","salisbury steak",
        "salisbury wiltshire","salisbury city council","salisbury hospital",
    ]
    for s in salisbury_blocks:
        if s in text:
            return True, f"Blocked: non-product Salisbury reference ('{s}')"

    # Always block academic
    for s in ACADEMIC_SIGNALS:
        if s in text:
            return True, f"Blocked: academic/journal content"

    # Always block consumer electrical (if no electrical safety content)
    for s in CONSUMER_ELECTRICAL:
        if s in text and not has_electrical_safety_content(text):
            return True, f"Blocked: consumer electrical ('{s}')"

    # Block competitor + unrelated product ONLY if no electrical safety content
    if not has_electrical_safety_content(text):
        for comp, unrelated in COMPETITOR_UNRELATED_PAIRS:
            if comp in text and unrelated in text:
                return True, f"Blocked: {comp} in unrelated context ('{unrelated}')"

        # Block pure unrelated safety categories
        for s in UNRELATED_SAFETY_ONLY:
            if s in text:
                return True, f"Blocked: unrelated safety category ('{s}')"

        # Foreign-only with no India signal
        has_india   = any(s in text for s in INDIA_SIGNALS)
        has_foreign = any(s in text for s in FOREIGN_ONLY)
        if has_foreign and not has_india:
            return True, "Blocked: foreign market only, no India signal"

    return False, ""


# ══════════════════════════════════════════════════════════════════
# SCORING ENGINE
# Formula: Score = (KW×0.4) + (Comp×0.3) + (Intent×0.3)
# ══════════════════════════════════════════════════════════════════

def compute_keyword_score(title, summary):
    text_full  = (title+" "+summary).lower()
    text_title = title.lower()
    best_score, best_type = 0, "Generic"
    matched, high_val = [], 0
    for pattern, base, ktype in KEYWORD_SCORE_MAP:
        if pattern in text_full:
            matched.append((pattern, base, ktype))
            if base > best_score:
                best_score, best_type = base, ktype
            if base >= 70:
                high_val += 1
    if not matched:
        return 10, "None", []
    score = best_score
    for pattern, base, _ in matched:
        if pattern in text_title and base == best_score:
            score += 10; break
    if high_val >= 2:
        score += 10
    return min(score, 100), best_type, matched


def compute_competitor_score(text):
    hits    = get_competitor_hits(text)
    has_ind = any(s in text for s in [
        "global ppe leader","leading ppe manufacturer","major safety brand",
        "international safety company",
    ])
    if not hits and not has_ind:
        return 20, [], False
    if hits:
        bonus = len(hits) >= 2
        return min(100 + (10 if bonus else 0), 100), hits, bonus
    return 60, [], False


def compute_intent_kw(title, summary):
    text = (title+" "+summary).lower()
    if any(k in text for k in ["new plant","expansion","invest","greenfield","brownfield","capacity increase","new facility"]):
        return 100,"Investment / Capacity Expansion"
    if any(k in text for k in ["acqui","merger","joint venture","partnership","stake","buyout","takeover","collaboration"]):
        return 100,"M&A / Partnership"
    if any(k in text for k in ["launch","new product","new model","introduces","unveil","new range","new line"]):
        return 90,"New Product Launch"
    if any(k in text for k in ["innovation","patent","r&d","technology","new material","fr fabric","composite","new design"]):
        return 85,"Technology / Innovation"
    if any(k in text for k in ["regulat","standard","compliance","bis","qco","mandatory","norms","dgfasli","pgiel","certification"]):
        return 80,"Regulatory / Compliance"
    if any(k in text for k in ["contract","order","supply deal","tender","award","procurement","large order"]):
        return 75,"Large Order / Contract"
    return 40,"General News / Mention"


def final_score(kw, comp, intent, w_kw=0.4, w_comp=0.3, w_intent=0.3):
    return round((kw*w_kw) + (comp*w_comp) + (intent*w_intent))


def score_label_badge(score):
    if score >= 80: return "🔥 High",   "nb-high"
    if score >= 60: return "⚡ Medium",  "nb-med"
    if score >= 40: return "🟡 Low",    "nb-low"
    return "❌ Ignore","nb-oth"


def score_bar(score):
    color = ("#ff5e62" if score>=80 else "#f59e0b" if score>=60
             else "#f7b731" if score>=40 else "#333")
    return (f'<div class="sbar-wrap"><div class="sbar" '
            f'style="width:{min(score,100)}%;background:{color};"></div></div>')


def score_ring_cls(score):
    if score >= 80: return "ring-high"
    if score >= 60: return "ring-med"
    if score >= 40: return "ring-low"
    return "ring-ignore"


# ══════════════════════════════════════════════════════════════════
# DEDUPLICATION
# ══════════════════════════════════════════════════════════════════

def deduplicate(articles, threshold=0.82):
    unique = []
    for art in articles:
        dup = False
        for kept in unique:
            sim = SequenceMatcher(None,
                art["title"].lower(), kept["title"].lower()).ratio()
            if sim >= threshold:
                if art.get("relevance",0) > kept.get("relevance",0):
                    unique.remove(kept); unique.append(art)
                dup = True; break
        if not dup:
            unique.append(art)
    return unique


# ══════════════════════════════════════════════════════════════════
# LLM INTENT
# ══════════════════════════════════════════════════════════════════

def classify_intent_llm(articles, api_key):
    if not api_key:
        for a in articles:
            is_, intent = compute_intent_kw(a["title"], a["summary"])
            a["intent"] = intent; a["intent_score"] = is_
            a["category"] = INTENT_TO_CATEGORY.get(intent,"Other")
            a["key_insight"] = "Add Groq API key for AI insights"
        return articles
    client = Groq(api_key=api_key)
    intents_list = list(INTENT_SCORES.keys())
    for a in articles:
        prompt = f"""You are a market intelligence analyst for an electrical safety PPE manufacturer in India.
Products: electrical insulating gloves, rubber insulating mats, arc flash suits.
Competitors: Honeywell, Salisbury, CATU, Novax, Ansell, DPL, MN Rubber, Jayco, Morning Pride.
Geography: INDIA market focus.

Classify this article's intent into EXACTLY ONE of:
{json.dumps(intents_list)}

Write ONE key insight max 12 words, India-focused.

Title: {a['title']}
Summary: {a['summary']}

Reply ONLY in valid JSON:
{{"intent":"...","key_insight":"..."}}"""
        try:
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role":"user","content":prompt}],
                max_tokens=80, temperature=0.1,
            )
            result  = json.loads(resp.choices[0].message.content.strip())
            intent  = result.get("intent","General News / Mention")
            if intent not in INTENT_SCORES: intent = "General News / Mention"
            a["intent"]       = intent
            a["intent_score"] = INTENT_SCORES[intent]
            a["category"]     = INTENT_TO_CATEGORY.get(intent,"Other")
            a["key_insight"]  = result.get("key_insight","—")
            kw_s,_,_ = compute_keyword_score(a["title"],a["summary"])
            cs,_,_   = compute_competitor_score((a["title"]+" "+a["summary"]).lower())
            a["relevance"] = final_score(kw_s, cs, a["intent_score"])
        except Exception:
            is_, intent = compute_intent_kw(a["title"],a["summary"])
            a["intent"]=intent; a["intent_score"]=is_
            a["category"]=INTENT_TO_CATEGORY.get(intent,"Other")
            a["key_insight"]="—"
        time.sleep(0.3)
    return articles


# ══════════════════════════════════════════════════════════════════
# NEWS FETCH PIPELINE
# ══════════════════════════════════════════════════════════════════

def fetch_google_news(query, days_back=30):
    iq = f"{query} India" if "india" not in query.lower() else query
    url = (f"https://news.google.com/rss/search?"
           f"q={urllib.parse.quote(iq)}&hl=en-IN&gl=IN&ceid=IN:en")
    feed   = feedparser.parse(url)
    cutoff = datetime.now() - timedelta(days=days_back)
    out    = []
    for e in feed.entries:
        try:    pub = datetime(*e.published_parsed[:6])
        except: pub = datetime.now()
        if pub >= cutoff:
            out.append({
                "title":e.title, "link":e.link, "published":pub,
                "source":e.get("source",{}).get("title","Unknown"),
                "summary":e.get("summary","")[:400], "query":query,
            })
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_news(queries_tuple, days_back, api_key, w_kw, w_comp, w_intent):
    # 1. Fetch
    raw = []
    for q in queries_tuple:
        raw.extend(fetch_google_news(q, days_back))
        time.sleep(0.15)

    # 2. Hard disqualify
    post_disq, removed = [], []
    for a in raw:
        disq, reason = is_disqualified(a["title"], a["summary"], a["source"])
        if disq:
            a["discard_reason"] = reason; removed.append(a)
        else:
            post_disq.append(a)

    # 3. Relevance filter (new 3-rule logic)
    relevant, irrelevant = [], []
    for a in post_disq:
        rel, comp_hits, prod_hits = is_relevant_article(a["title"], a["summary"])
        if rel:
            a["comp_hits_rel"] = comp_hits
            a["prod_hits_rel"] = prod_hits
            relevant.append(a)
        else:
            a["discard_reason"] = "No competitor+product combo or insufficient electrical safety signals"
            irrelevant.append(a)

    removed += irrelevant

    # 4. Score
    for a in relevant:
        text = (a["title"]+" "+a["summary"]).lower()
        kw_s, kw_type, _   = compute_keyword_score(a["title"], a["summary"])
        cs, comp_hits, bon = compute_competitor_score(text)
        is_, intent         = compute_intent_kw(a["title"], a["summary"])
        fs = final_score(kw_s, cs, is_, w_kw, w_comp, w_intent)
        a.update({
            "kw_score":kw_s,"kw_type":kw_type,
            "comp_score":cs,"comp_hits":comp_hits,
            "intent":intent,"intent_score":is_,
            "relevance":fs,"category":INTENT_TO_CATEGORY.get(intent,"Other"),
            "key_insight":"",
            "score_breakdown":(
                f"KW:{kw_s}({kw_type})×{w_kw} + "
                f"Comp:{cs}({'|'.join(comp_hits) if comp_hits else 'none'})×{w_comp} + "
                f"Intent:{is_}({intent})×{w_intent} = {fs}"
            ),
        })

    # 5. Deduplicate
    relevant = deduplicate(relevant, threshold=0.82)

    # 6. LLM
    relevant = classify_intent_llm(relevant, api_key)

    # 7. Re-apply weights after LLM
    for a in relevant:
        a["relevance"] = final_score(
            a["kw_score"], a["comp_score"], a["intent_score"],
            w_kw, w_comp, w_intent
        )
        a["score_breakdown"] = (
            f"KW:{a['kw_score']}({a['kw_type']})×{w_kw} + "
            f"Comp:{a['comp_score']}({'|'.join(a['comp_hits']) if a['comp_hits'] else 'none'})×{w_comp} + "
            f"Intent:{a['intent_score']}({a['intent']})×{w_intent} = {a['relevance']}"
        )

    relevant.sort(key=lambda x: x["relevance"], reverse=True)
    return relevant, removed


def build_queries(sel_comp, sel_groups, inc_comp_kw):
    q = list(sel_comp)
    for g in sel_groups: q.extend(ALL_KEYWORD_GROUPS.get(g,[]))
    if inc_comp_kw: q.extend(COMPETITOR_KEYWORDS)
    seen,u = set(),[]
    for x in q:
        if x not in seen: seen.add(x); u.append(x)
    return u


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚡ SafeIntel")
    st.markdown("**Electrical Safety · 🇮🇳 India**")
    st.markdown('<div style="background:linear-gradient(90deg,#f7b731,#ff5e62);height:2px;border-radius:2px;margin-bottom:16px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-head">🔑 API Key</div>', unsafe_allow_html=True)
    try:    api_key = st.secrets.get("GROQ_API_KEY","")
    except: api_key = ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    st.markdown('<div class="section-head">🏭 Competitors</div>', unsafe_allow_html=True)
    sel_comp = st.multiselect("Select competitors", COMPETITORS, default=COMPETITORS)
    new_co = st.text_input("➕ Add competitor", placeholder="e.g. Karam Industries")
    if new_co: sel_comp.append(new_co)

    st.markdown('<div class="section-head">📦 Products & Keywords</div>', unsafe_allow_html=True)
    product_lines = st.multiselect(
        "Product lines",
        ["🧤 Gloves","🟫 Mats","🦺 Arc Suits","🌐 Common"],
        default=["🧤 Gloves","🟫 Mats","🦺 Arc Suits","🌐 Common"],
    )
    avail_groups = [g for g in ALL_KEYWORD_GROUPS
                    if any(pl.split(" ")[0] in g for pl in product_lines) or "Common" in g]
    sel_groups   = st.multiselect("Keyword groups", avail_groups, default=avail_groups)
    inc_comp_kw  = st.checkbox("Competitor-specific keywords", value=True)

    st.markdown('<div class="section-head">📅 Time & Filters</div>', unsafe_allow_html=True)
    days_back     = st.slider("Days of news", 7, 90, 30)
    selected_cats = st.multiselect("Categories", CATEGORIES, default=CATEGORIES)
    min_score     = st.slider("Min score (0–100)", 0, 100, 40)
    show_discard  = st.checkbox("Show discarded articles", value=False)
    show_breakdown= st.checkbox("Show score breakdown", value=False)

    st.markdown('<div class="section-head">⚖️ Score Weights</div>', unsafe_allow_html=True)
    w_kw     = st.slider("Keyword weight",    0.0, 1.0, 0.4, 0.05)
    w_comp   = st.slider("Competitor weight", 0.0, 1.0, 0.3, 0.05)
    w_intent = st.slider("Intent weight",     0.0, 1.0, 0.3, 0.05)
    wt = round(w_kw+w_comp+w_intent,2)
    if abs(wt-1.0)>0.05: st.warning(f"⚠️ Weights sum to {wt}, should be 1.0")

    fetch_btn = st.button("⚡ Fetch & Analyse News")


# ══════════════════════════════════════════════════════════════════
# MAIN DASHBOARD
# ══════════════════════════════════════════════════════════════════

# ── TOP NAV ───────────────────────────────────────────────────────
st.markdown("""
<div class="topnav">
  <div class="nav-logo">
    <div class="nav-bolt">⚡</div>SAFEINTEL
  </div>
  <div class="nav-tab active" id="tab-feed"    onclick="switchPage('feed',this)">📰 Intelligence Feed</div>
  <div class="nav-tab"        id="tab-comp"    onclick="switchPage('comp',this)">🏭 Competitors</div>
  <div class="nav-tab"        id="tab-product" onclick="switchPage('product',this)">📦 Products</div>
  <div class="nav-tab"        id="tab-reg"     onclick="switchPage('reg',this)">📋 Regulatory</div>
  <div class="nav-tab"        id="tab-trends"  onclick="switchPage('trends',this)">📈 Trends</div>
  <div class="nav-right">
    <span class="nav-pill">🇮🇳 India Only</span>
  </div>
</div>
<script>
function switchPage(pageId, el){
  document.querySelectorAll('.nav-tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.dash-page').forEach(p=>p.style.display='none');
  el.classList.add('active');
  var pg = document.getElementById('page-'+pageId);
  if(pg) pg.style.display='block';
}
</script>
""", unsafe_allow_html=True)

# ── HERO ──────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-title">Electrical Safety Market Intelligence</div>
  <div class="hero-sub">Tracking Gloves · Mats · Arc Suits · 10 Competitors · 150+ Keywords · Powered by AI</div>
  <div class="hero-pills">
    <span class="hero-pill on">🧤 Gloves</span>
    <span class="hero-pill on">🟫 Mats</span>
    <span class="hero-pill on">🦺 Arc Suits</span>
    <span class="hero-pill on">🇮🇳 India Only</span>
    <span class="hero-pill on">⚡ Weighted Scoring</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── FETCH & RENDER ────────────────────────────────────────────────
if fetch_btn or "intel_data" in st.session_state:
    if fetch_btn:
        queries = build_queries(sel_comp, sel_groups, inc_comp_kw)
        st.info(f"🔍 Running **{len(queries)} queries** — strict electrical safety filter · India-focused · deduplication ON")
        with st.spinner("Fetching, filtering, scoring…"):
            kept, removed = fetch_all_news(
                tuple(queries), days_back, api_key or "",
                w_kw, w_comp, w_intent
            )
            st.session_state["intel_data"]    = kept
            st.session_state["removed_data"]  = removed

    kept    = st.session_state.get("intel_data",   [])
    removed = st.session_state.get("removed_data", [])
    df      = pd.DataFrame(kept)   if kept    else pd.DataFrame()
    df_rem  = pd.DataFrame(removed) if removed else pd.DataFrame()

    if df.empty:
        st.warning("No relevant articles found. Try a longer time range, lower min score, or check keyword groups.")
    else:
        df_f = df[df["category"].isin(selected_cats) & (df["relevance"]>=min_score)].copy()

        # ── Streamlit tabs (since JS page switching needs full re-render trick)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📰 Intelligence Feed",
            "🏭 Competitors",
            "📦 Products",
            "📋 Regulatory",
            "📈 Trends",
        ])

        # ═════════════════════════════════════════════
        # TAB 1 — INTELLIGENCE FEED
        # ═════════════════════════════════════════════
        with tab1:
            # METRICS
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            c1,c2,c3,c4,c5 = st.columns(5)
            high_cnt = len(df_f[df_f["relevance"]>=80])
            ma_cnt   = len(df_f[df_f["intent"]=="M&A / Partnership"])
            reg_cnt  = len(df_f[df_f["intent"]=="Regulatory / Compliance"])
            avg_s    = round(df_f["relevance"].mean(),1) if len(df_f) else 0
            for col, num, lbl, cls, delta in [
                (c1, len(df_f),   "Relevant Articles", "mc1", f"of {len(df)} fetched"),
                (c2, high_cnt,    "🔥 High Priority",  "mc2", "score ≥ 80"),
                (c3, len(removed),"Auto-Filtered Out",  "mc3", "noise removed"),
                (c4, ma_cnt,      "M&A Signals",        "mc4", "partnerships · deals"),
                (c5, avg_s,       "Avg Score",          "mc5", "out of 100"),
            ]:
                col.markdown(
                    f'<div class="mcard {cls}">'
                    f'<div class="mnum">{num}</div>'
                    f'<div class="mlbl">{lbl}</div>'
                    f'<div class="mdelta">{delta}</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

            # CHARTS
            ch1, ch2 = st.columns(2)
            with ch1:
                cat_df = df_f["category"].value_counts().reset_index()
                cat_df.columns = ["Category","Count"]
                fig = px.bar(cat_df, x="Count", y="Category", orientation="h",
                             color="Category", color_discrete_map=CAT_COLORS,
                             title="Articles by Intelligence Category")
                fig.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#aaa",showlegend=False,
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig, use_container_width=True)

            with ch2:
                score_bands = pd.cut(df_f["relevance"],
                    bins=[0,39,59,79,100],
                    labels=["❌ <40","🟡 40–59","⚡ 60–79","🔥 80–100"])
                bd = score_bands.value_counts().reset_index()
                bd.columns = ["Band","Count"]
                bc = {"🔥 80–100":"#ff5e62","⚡ 60–79":"#f59e0b",
                      "🟡 40–59":"#f7b731","❌ <40":"#2a2a3a"}
                fig2 = px.bar(bd, x="Band", y="Count", color="Band",
                              color_discrete_map=bc, title="Relevance Score Distribution")
                fig2.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#aaa",showlegend=False,
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # FEED FILTERS
            fc1,fc2,fc3 = st.columns([2,1,1])
            with fc1: search = st.text_input("🔎 Search","",placeholder="e.g. Honeywell, IEC 60903, arc flash…")
            with fc2: fp = st.selectbox("Product",["All","Gloves","Mats","Arc Suits"])
            with fc3: sb = st.selectbox("Sort",["Highest score","Latest first"])

            df_show = df_f.copy()
            if search:
                df_show = df_show[df_show["title"].str.contains(search,case=False,na=False)]
            if fp != "All":
                pm = {"Gloves":ALL_GLOVE_KW,"Mats":ALL_MAT_KW,"Arc Suits":ALL_ARC_KW}
                df_show = df_show[df_show["query"].isin(pm[fp])]
            if sb == "Latest first":
                df_show = df_show.sort_values("published",ascending=False)

            st.markdown(
                f'<div style="font-size:0.78rem;color:#555;margin-bottom:10px;">'
                f'Showing <b style="color:#e0e0ff">{len(df_show)}</b> articles · '
                f'<b style="color:#555">{len(removed)}</b> auto-removed</div>',
                unsafe_allow_html=True
            )

            for _, row in df_show.iterrows():
                sc   = row.get("relevance",0)
                slbl, sbdg = score_label_badge(sc)
                cbc  = CAT_BADGE.get(row.get("category","Other"),"nb-oth")
                ring = score_ring_cls(sc)
                comp_str = ", ".join(row.get("comp_hits",[])) or "—"
                bar  = score_bar(sc)
                bd   = row.get("score_breakdown","—")
                ki   = row.get("key_insight","—")
                st.markdown(f"""
                <div class="ncard">
                  <div class="score-ring {ring}">{sc}</div>
                  <div style="flex:1;min-width:0;">
                    <div class="ntitle">
                      <a href="{row['link']}" target="_blank"
                         style="color:#e8e8ff;text-decoration:none;">{row['title']}</a>
                    </div>
                    <div class="nbadges">
                      <span class="nbadge {cbc}">{row.get('category','—')}</span>
                      <span class="nbadge {sbdg}">{slbl} {sc}/100</span>
                      <span class="nbadge nb-comp">🏭 {comp_str}</span>
                    </div>
                    {bar}
                    <div class="nmeta">
                      🗞️ {row['source']} &nbsp;|&nbsp;
                      📅 {row['published'].strftime('%d %b %Y')} &nbsp;|&nbsp;
                      🎯 {row.get('intent','—')} &nbsp;|&nbsp;
                      💡 {ki}
                    </div>
                    {"<div class='score-breakdown'>📐 "+bd+"</div>" if show_breakdown else ""}
                  </div>
                </div>""", unsafe_allow_html=True)

            # Discarded
            if show_discard and not df_rem.empty:
                st.markdown("---")
                st.markdown(f"**❌ Auto-Discarded ({len(df_rem)})**")
                for _, row in df_rem.iterrows():
                    st.markdown(f"""
                    <div class="ncard" style="opacity:0.4;border-color:#1a1a2e;">
                      <div class="score-ring ring-ignore">✗</div>
                      <div style="flex:1;">
                        <div class="ntitle" style="color:#555;">{row['title']}</div>
                        <div class="nmeta">❌ {row.get('discard_reason','—')} · 🗞️ {row['source']}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

            # Export
            st.markdown("---")
            ec1,ec2 = st.columns(2)
            ecols = ["title","category","relevance","intent","intent_score",
                     "kw_score","comp_score","comp_hits","key_insight",
                     "score_breakdown","source","published","link"]
            out = df_show[[c for c in ecols if c in df_show.columns]].copy()
            out["published"] = out["published"].dt.strftime("%Y-%m-%d")
            full = df[[c for c in ecols if c in df.columns]].copy()
            full["published"] = full["published"].dt.strftime("%Y-%m-%d")
            with ec1:
                st.download_button("⬇️ Filtered CSV", out.to_csv(index=False),
                    f"intel_filtered_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
            with ec2:
                st.download_button("⬇️ Full CSV", full.to_csv(index=False),
                    f"intel_full_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")

        # ═════════════════════════════════════════════
        # TAB 2 — COMPETITORS
        # ═════════════════════════════════════════════
        with tab2:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">🏭 Competitor Activity Dashboard</div>', unsafe_allow_html=True)
            comp_rows = []
            for cn in COMPETITOR_NAMES_LOWER:
                mask = df["comp_hits"].apply(lambda x: cn in x if isinstance(x,list) else False)
                sub  = df[mask]
                if len(sub) > 0:
                    comp_rows.append({
                        "Competitor": cn.title(),
                        "Articles": len(sub),
                        "Avg Score": round(sub["relevance"].mean(),1),
                        "High Priority": len(sub[sub["relevance"]>=80]),
                        "Top Intent": sub["intent"].mode()[0] if len(sub)>0 else "—",
                    })
            if comp_rows:
                comp_df = pd.DataFrame(comp_rows).sort_values("Avg Score",ascending=False)
                colors  = ["#a78bfa","#ff8585","#34d399","#fcd34d","#93c5fd",
                           "#67e8f9","#fb923c","#f472b6","#a3e635","#e879f9"]
                for i, (_, row) in enumerate(comp_df.iterrows()):
                    pct = int(row["Avg Score"])
                    col = colors[i % len(colors)]
                    sl, sb = score_label_badge(pct)
                    st.markdown(f"""
                    <div class="comp-card">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                        <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.95rem;color:{col};">
                          {row['Competitor']}
                        </div>
                        <div style="display:flex;gap:8px;">
                          <span class="nbadge nb-med">{row['Articles']} articles</span>
                          <span class="nbadge nb-high">{row['High Priority']} 🔥 high</span>
                        </div>
                      </div>
                      <div class="sbar-wrap" style="height:6px;">
                        <div class="sbar" style="width:{pct}%;background:{col};height:6px;"></div>
                      </div>
                      <div class="nmeta" style="margin-top:6px;">
                        Avg Score: <b style="color:{col};">{row['Avg Score']}/100</b> &nbsp;|&nbsp;
                        Top Intent: {row['Top Intent']}
                      </div>
                    </div>""", unsafe_allow_html=True)

                fig_c = px.bar(comp_df, x="Competitor", y="Avg Score",
                               color="Competitor",
                               color_discrete_sequence=colors,
                               title="Competitor Average Relevance Score")
                fig_c.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#aaa",showlegend=False,
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e",range=[0,100]),
                )
                st.plotly_chart(fig_c, use_container_width=True)

        # ═════════════════════════════════════════════
        # TAB 3 — PRODUCTS
        # ═════════════════════════════════════════════
        with tab3:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">📦 Product Line Intelligence</div>', unsafe_allow_html=True)
            p1,p2,p3 = st.columns(3)
            for col, emoji, label, kws, cls in [
                (p1,"🧤","Electrical Insulating Gloves",ALL_GLOVE_KW,"mc1"),
                (p2,"🟫","Electrical Insulating Mats",  ALL_MAT_KW,  "mc3"),
                (p3,"🦺","Arc Flash Suits",              ALL_ARC_KW,  "mc2"),
            ]:
                sub = df[df["query"].isin(kws)] if "query" in df.columns else pd.DataFrame()
                cnt = len(sub)
                avg = round(sub["relevance"].mean(),1) if cnt>0 else 0
                col.markdown(
                    f'<div class="mcard {cls}" style="text-align:left;min-height:110px;">'
                    f'<div style="font-size:1.8rem;margin-bottom:6px;">{emoji}</div>'
                    f'<div class="mnum">{cnt}</div>'
                    f'<div class="mlbl">{label}</div>'
                    f'<div class="mdelta">Avg score: {avg}</div></div>',
                    unsafe_allow_html=True
                )
            # Product articles
            for plabel, kws in [("🧤 Gloves",ALL_GLOVE_KW),("🟫 Mats",ALL_MAT_KW),("🦺 Arc Suits",ALL_ARC_KW)]:
                sub = df_f[df_f["query"].isin(kws)].head(5) if "query" in df_f.columns else pd.DataFrame()
                if not sub.empty:
                    st.markdown(f'<div class="sec-title" style="margin-top:20px;">{plabel} — Top Articles</div>', unsafe_allow_html=True)
                    for _, row in sub.iterrows():
                        sc   = row.get("relevance",0)
                        slbl,sbdg = score_label_badge(sc)
                        ring = score_ring_cls(sc)
                        st.markdown(f"""
                        <div class="ncard">
                          <div class="score-ring {ring}">{sc}</div>
                          <div style="flex:1;">
                            <div class="ntitle">
                              <a href="{row['link']}" target="_blank" style="color:#e8e8ff;text-decoration:none;">{row['title']}</a>
                            </div>
                            <div class="nmeta">🗞️ {row['source']} · 📅 {row['published'].strftime('%d %b %Y')} · {slbl}</div>
                          </div>
                        </div>""", unsafe_allow_html=True)

        # ═════════════════════════════════════════════
        # TAB 4 — REGULATORY
        # ═════════════════════════════════════════════
        with tab4:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">📋 Regulatory & Compliance Alerts · India</div>', unsafe_allow_html=True)
            reg_df = df_f[df_f["category"]=="Regulatory Change"].copy()
            if reg_df.empty:
                st.info("No regulatory articles found in current results. Try a longer time range.")
            else:
                st.markdown(f'<div class="info-box">⚠️ <b>{len(reg_df)} regulatory articles</b> found · Standards tracked: IS 4770 · IS 15652 · IEC 60903 · IEC 61111 · IEC 61482 · NFPA 70E · BIS QCO · CEA · DGFASLI</div>', unsafe_allow_html=True)
                for _, row in reg_df.iterrows():
                    sc   = row.get("relevance",0)
                    slbl,sbdg = score_label_badge(sc)
                    ring = score_ring_cls(sc)
                    st.markdown(f"""
                    <div class="ncard" style="border-color:rgba(255,94,98,0.3);">
                      <div class="score-ring {ring}">{sc}</div>
                      <div style="flex:1;">
                        <div class="ntitle">
                          <a href="{row['link']}" target="_blank" style="color:#e8e8ff;text-decoration:none;">{row['title']}</a>
                        </div>
                        <div class="nbadges">
                          <span class="nbadge nb-reg">📋 Regulatory</span>
                          <span class="nbadge {sbdg}">{slbl} {sc}/100</span>
                        </div>
                        <div class="nmeta">🗞️ {row['source']} · 📅 {row['published'].strftime('%d %b %Y')} · 💡 {row.get('key_insight','—')}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

        # ═════════════════════════════════════════════
        # TAB 5 — TRENDS
        # ═════════════════════════════════════════════
        with tab5:
            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">📈 Intelligence Trends Over Time</div>', unsafe_allow_html=True)
            if "published" in df_f.columns and len(df_f)>0:
                df_f["week"] = df_f["published"].dt.to_period("W").astype(str)
                trend = df_f.groupby(["week","category"]).size().reset_index(name="count")
                fig_t = px.line(trend, x="week", y="count", color="category",
                                color_discrete_map=CAT_COLORS,
                                title="Weekly Intelligence Volume by Category",
                                markers=True)
                fig_t.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#aaa",
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    legend=dict(bgcolor="rgba(0,0,0,0)",font_size=10),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig_t, use_container_width=True)

                # Score over time
                score_trend = df_f.groupby("week")["relevance"].mean().reset_index()
                score_trend.columns = ["week","avg_score"]
                fig_s = px.area(score_trend, x="week", y="avg_score",
                                title="Average Relevance Score Over Time",
                                color_discrete_sequence=["#f7b731"])
                fig_s.update_traces(fill="tozeroy",
                    fillcolor="rgba(247,183,49,0.08)",
                    line_color="#f7b731")
                fig_s.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#aaa",
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig_s, use_container_width=True)

else:
    # ── LANDING PAGE ──────────────────────────────────────────────
    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    <b>📐 Relevance Formula:</b> &nbsp;
    Score = (Keyword×<b>0.4</b>) + (Competitor×<b>0.3</b>) + (Intent×<b>0.3</b>)
    &nbsp;|&nbsp; 🔥 80–100 Immediate &nbsp;⚡ 60–79 Track &nbsp;🟡 40–59 Optional &nbsp;❌ &lt;40 Filtered
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sec-title">📐 Relevance Rules</div>', unsafe_allow_html=True)
    r1,r2,r3 = st.columns(3)
    for col, num, title, desc in [
        (r1,"1","Competitor + Combo","Article must mention a competitor AND at least one other competitor OR a product keyword OR a standard. Single competitor mentions alone are filtered."),
        (r2,"2","Product / Standard Focus","Articles about our specific products (gloves, mats, arc suits) or standards (IEC 60903, IS 4770…) are kept even without a competitor mention."),
        (r3,"3","Strict Electrical Safety","Only articles within the electrical safety PPE universe. Honeywell HVAC, Ansell medical gloves, fire safety — all filtered out automatically."),
    ]:
        col.markdown(f"""
        <div class="mcard mc{num}" style="text-align:left;padding:18px;min-height:130px;">
          <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;
               color:#f7b731;margin-bottom:6px;">Rule {num}</div>
          <div style="font-weight:700;color:#e0e0ff;font-size:0.85rem;margin-bottom:6px;">{title}</div>
          <div style="font-size:0.75rem;color:#666;line-height:1.5;">{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">🏭 Competitors Tracked</div>', unsafe_allow_html=True)
    cc = st.columns(5)
    colors = ["#a78bfa","#ff8585","#34d399","#fcd34d","#93c5fd","#67e8f9","#fb923c","#f472b6","#a3e635","#e879f9"]
    for i,co in enumerate(COMPETITORS):
        with cc[i%5]:
            st.markdown(
                f'<div class="mcard" style="padding:12px;margin-bottom:8px;border-top:2px solid {colors[i]};">'
                f'<div style="font-size:0.8rem;color:#e0e0ff;font-weight:600;">{co}</div></div>',
                unsafe_allow_html=True
            )
