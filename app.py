import streamlit as st
import feedparser
import pandas as pd
import plotly.express as px
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #05060f !important; color: #f0f0ff; }

.hero {
    background: linear-gradient(135deg,#0f0c29 0%,#302b63 55%,#1a1040 100%);
    padding: 26px 28px 20px; position: relative; overflow: hidden;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.hero::before {
    content:''; position:absolute; top:-50px; right:-30px;
    width:240px; height:240px;
    background:radial-gradient(circle,rgba(247,183,49,0.13),transparent 70%);
    border-radius:50%;
}
.hero-title {
    font-family:'Syne',sans-serif; font-size:1.5rem; font-weight:800;
    background:linear-gradient(90deg,#fff 25%,#f7b731 60%,#ff5e62 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:4px;
}
.hero-sub { font-size:0.74rem; color:#666; }
.hero-pills { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; }
.hero-pill {
    background:rgba(247,183,49,0.1); border:1px solid rgba(247,183,49,0.3);
    border-radius:20px; padding:3px 12px; font-size:0.65rem; color:#f7b731;
}

.mcard {
    border-radius:12px; padding:16px 14px; position:relative;
    overflow:hidden; margin-bottom:4px;
}
.mcard::after {
    content:''; position:absolute; top:0; left:0; right:0;
    height:3px; border-radius:12px 12px 0 0;
}
.mc1{background:linear-gradient(135deg,#1a1040,#2d1b69);} .mc1::after{background:linear-gradient(90deg,#7c3aed,#a78bfa);}
.mc2{background:linear-gradient(135deg,#200a0a,#6b0f1a);} .mc2::after{background:linear-gradient(90deg,#ff5e62,#ff9966);}
.mc3{background:linear-gradient(135deg,#051a10,#064e3b);} .mc3::after{background:linear-gradient(90deg,#10b981,#34d399);}
.mc4{background:linear-gradient(135deg,#1a1000,#78350f);} .mc4::after{background:linear-gradient(90deg,#f59e0b,#fcd34d);}
.mc5{background:linear-gradient(135deg,#050e1f,#1e3a5f);} .mc5::after{background:linear-gradient(90deg,#3b82f6,#93c5fd);}
.mnum{font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;line-height:1.1;}
.mc1 .mnum{color:#a78bfa;} .mc2 .mnum{color:#ff8585;} .mc3 .mnum{color:#34d399;} .mc4 .mnum{color:#fcd34d;} .mc5 .mnum{color:#93c5fd;}
.mlbl{font-size:0.6rem;text-transform:uppercase;letter-spacing:1.5px;color:#555;margin-top:4px;}
.mdelta{font-size:0.67rem;color:#34d399;margin-top:3px;}

.ncard {
    background:rgba(255,255,255,0.025); border:1px solid rgba(255,255,255,0.07);
    border-radius:12px; padding:14px 16px; margin-bottom:10px;
    display:flex; gap:14px; align-items:flex-start;
    transition:border-color 0.2s,background 0.2s;
}
.ncard:hover{border-color:rgba(247,183,49,0.25);background:rgba(247,183,49,0.03);}
.score-ring{
    flex-shrink:0; width:46px; height:46px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-family:'Syne',sans-serif; font-weight:800; font-size:0.78rem;
}
.ring-high{background:linear-gradient(135deg,#ff5e62,#ff9966);color:#fff;}
.ring-med{background:linear-gradient(135deg,#f59e0b,#fcd34d);color:#000;}
.ring-low{background:rgba(255,255,255,0.07);color:#888;border:1px solid #2a2a3a;}
.ring-ig{background:#111;color:#333;border:1px solid #222;}

.ntitle{font-size:0.87rem;font-weight:600;color:#e8e8ff;margin-bottom:5px;line-height:1.4;}
.nbadges{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:4px;}
.nbadge{font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:20px;
        letter-spacing:0.5px;text-transform:uppercase;}
.nb-ma  {background:rgba(124,58,237,0.18);color:#a78bfa;border:1px solid rgba(124,58,237,0.3);}
.nb-cap {background:rgba(59,130,246,0.15);color:#93c5fd;border:1px solid rgba(59,130,246,0.3);}
.nb-tech{background:rgba(16,185,129,0.15);color:#34d399;border:1px solid rgba(16,185,129,0.3);}
.nb-prod{background:rgba(245,158,11,0.15);color:#fcd34d;border:1px solid rgba(245,158,11,0.3);}
.nb-reg {background:rgba(255,94,98,0.15);color:#ff8585;border:1px solid rgba(255,94,98,0.3);}
.nb-mkt {background:rgba(6,182,212,0.15);color:#67e8f9;border:1px solid rgba(6,182,212,0.3);}
.nb-fin {background:rgba(52,211,153,0.12);color:#6ee7b7;border:1px solid rgba(52,211,153,0.3);}
.nb-oth {background:rgba(255,255,255,0.05);color:#666;border:1px solid #2a2a3a;}
.nb-hi  {background:rgba(255,94,98,0.18);color:#ff8585;border:1px solid rgba(255,94,98,0.35);}
.nb-med {background:rgba(245,158,11,0.15);color:#fcd34d;border:1px solid rgba(245,158,11,0.3);}
.nb-low {background:rgba(255,255,255,0.05);color:#888;border:1px solid #333;}
.nb-comp{background:rgba(167,139,250,0.15);color:#c4b5fd;border:1px solid rgba(167,139,250,0.3);}

.nmeta{font-size:0.65rem;color:#444;line-height:1.7;margin-top:4px;}
.sbar-wrap{background:rgba(255,255,255,0.05);border-radius:4px;height:4px;margin:5px 0 2px 0;}
.sbar{height:4px;border-radius:4px;}
.score-bd{background:#0a0a1a;border:1px solid #1a1a2e;border-radius:6px;
          padding:7px 12px;font-size:0.63rem;color:#555;margin-top:6px;line-height:1.6;}
.sec-title{font-family:'Syne',sans-serif;font-size:0.88rem;font-weight:700;
           color:#e0e0ff;margin:16px 0 12px 0;}
.comp-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.07);
           border-radius:12px;padding:14px 16px;margin-bottom:10px;}
.info-box{background:rgba(247,183,49,0.05);border:1px solid rgba(247,183,49,0.2);
          border-radius:10px;padding:12px 16px;font-size:0.78rem;color:#aaa;
          margin-bottom:14px;line-height:1.8;}
.sh{font-family:'Syne',sans-serif;font-size:0.63rem;text-transform:uppercase;
    letter-spacing:1.8px;color:#f7b731;margin:16px 0 6px 0;
    border-bottom:1px solid rgba(247,183,49,0.2);padding-bottom:4px;}
div[data-testid="stSidebarContent"]{background:#07071a !important;border-right:1px solid rgba(255,255,255,0.05);}
.stButton>button{
    background:linear-gradient(135deg,#f7b731,#ff5e62) !important;
    color:#000 !important;border:none !important;font-weight:700 !important;
    border-radius:8px !important;width:100% !important;
}
/* Streamlit tab styling */
.stTabs [data-baseweb="tab-list"] {
    background:rgba(255,255,255,0.02);
    border-radius:10px; padding:4px; gap:4px;
    border:1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius:8px; color:#666; font-size:0.8rem; font-weight:500;
    padding:8px 16px;
}
.stTabs [aria-selected="true"] {
    background:linear-gradient(135deg,rgba(247,183,49,0.15),rgba(255,94,98,0.12)) !important;
    color:#fff !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ── MASTER DATA ──────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

# Competitors (Morning Pride removed)
COMPETITORS = [
    "Honeywell Safety","Honeywell Salisbury","Salisbury",
    "CATU","Novax","Ansell","DPL","MN Rubber","Jayco",
]
# Short lowercase names used in text matching
COMP_NAMES = [
    "honeywell","salisbury","catu","novax","ansell","dpl","mn rubber","jayco",
]

# ── Competitor-specific search keywords (from your original table)
COMPETITOR_KEYWORDS = [
    # Salisbury / Honeywell
    "Salisbury insulating gloves","Salisbury Class 2 gloves",
    "Salisbury electrical gloves","Salisbury arc flash suit",
    "Salisbury insulating mats",
    "Honeywell electrical gloves","Honeywell insulating gloves",
    "Honeywell insulating mats","Honeywell arc flash PPE",
    # CATU
    "CATU insulating gloves","CATU electrical gloves",
    "CATU IEC 60903 gloves","CATU Class 1 gloves",
    "CATU insulating mats","CATU arc flash suit",
    # Novax
    "Novax electrical gloves","Novax rubber insulating gloves",
    "Novax insulating gloves","Novax Class 0 gloves",
    "Novax ASTM D120 gloves",
    # Ansell
    "Ansell electrical gloves","Ansell arc flash PPE",
    # DPL
    "DPL electrical gloves","DPL insulating gloves",
    "DPL rubber mats","DPL arc flash suit",
    # MN Rubber
    "MN Rubber electrical gloves","MN Rubber insulating mats",
    # Jayco
    "Jayco electrical gloves","Jayco insulating mats","Jayco arc flash PPE",
]

# ── ALL KEYWORDS — full universe from your spreadsheet ────────────
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
    "Type": [
        "Type I rubber gloves","Type II rubber gloves",
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
    "Common": [
        "electric hand gloves","insulated hand gloves",
        "safety hand gloves electrical","power line gloves",
        "shock resistant gloves","high voltage safety equipment",
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
        "electrical floor mat","panel room mat","rubber insulating matting",
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
        "substation mat","electrical room flooring",
        "HT panel mat","LT panel mat",
    ],
    "Feature": [
        "anti skid electrical mat","flame retardant mat",
        "fire resistant rubber mat","oil resistant mat",
        "heat resistant electrical mat","corrugated rubber mat","non conductive mat",
    ],
    "Common": [
        "rubber mat for electrical safety","insulation mat for floor",
        "shock proof mat","non conductive mat",
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
        "flame resistant suit FR suit",
    ],
}

KEYWORDS_COMMON = [
    "electrical PPE India","electrical safety equipment India",
    "electrical protective equipment India","live line PPE India",
    "high voltage safety equipment India","industrial safety PPE electrical India",
    "power sector safety gear India","electrical safety India",
    "electrical PPE","live line PPE","electrical safety equipment",
]

ALL_KEYWORD_GROUPS = {
    "🧤 Gloves — Core":      KEYWORDS_GLOVES["Core"],
    "🧤 Gloves — Technical": KEYWORDS_GLOVES["Technical"],
    "🧤 Gloves — Standards": KEYWORDS_GLOVES["Standards"],
    "🧤 Gloves — Class":     KEYWORDS_GLOVES["Class"],
    "🧤 Gloves — Type":      KEYWORDS_GLOVES["Type"],
    "🧤 Gloves — Voltage":   KEYWORDS_GLOVES["Voltage"],
    "🧤 Gloves — Material":  KEYWORDS_GLOVES["Material"],
    "🧤 Gloves — Use Case":  KEYWORDS_GLOVES["Use Case"],
    "🧤 Gloves — Feature":   KEYWORDS_GLOVES["Feature"],
    "🧤 Gloves — Common":    KEYWORDS_GLOVES["Common"],
    "🟫 Mats — Core":        KEYWORDS_MATS["Core"],
    "🟫 Mats — Technical":   KEYWORDS_MATS["Technical"],
    "🟫 Mats — Standards":   KEYWORDS_MATS["Standards"],
    "🟫 Mats — Class":       KEYWORDS_MATS["Class"],
    "🟫 Mats — Voltage":     KEYWORDS_MATS["Voltage"],
    "🟫 Mats — Use Case":    KEYWORDS_MATS["Use Case"],
    "🟫 Mats — Feature":     KEYWORDS_MATS["Feature"],
    "🟫 Mats — Common":      KEYWORDS_MATS["Common"],
    "🦺 Arc — Core":         KEYWORDS_ARC["Core"],
    "🦺 Arc — Technical":    KEYWORDS_ARC["Technical"],
    "🦺 Arc — Standards":    KEYWORDS_ARC["Standards"],
    "🦺 Arc — Type":         KEYWORDS_ARC["Type"],
    "🦺 Arc — Use Case":     KEYWORDS_ARC["Use Case"],
    "🦺 Arc — Feature":      KEYWORDS_ARC["Feature"],
    "🦺 Arc — Common":       KEYWORDS_ARC["Common"],
    "🌐 Common":             KEYWORDS_COMMON,
}

ALL_GLOVE_KW = [k for v in KEYWORDS_GLOVES.values() for k in v]
ALL_MAT_KW   = [k for v in KEYWORDS_MATS.values()   for k in v]
ALL_ARC_KW   = [k for v in KEYWORDS_ARC.values()    for k in v]
ALL_PRODUCT_KW = ALL_GLOVE_KW + ALL_MAT_KW + ALL_ARC_KW + KEYWORDS_COMMON

# Short tokens for matching inside article text (single/two words, easier to match)
PRODUCT_TOKENS = [
    # gloves
    "insulating glove","electrical glove","dielectric glove","rubber glove",
    "high voltage glove","arc flash glove","lineman glove","class 0","class 1",
    "class 2","class 3","class 4","class 00","11kv glove","33kv glove",
    "live line glove","voltage glove","iec 60903","astm d120","is 4770",
    "en 60903","nfpa 70e glove","osha 1910.137",
    # mats
    "insulating mat","dielectric mat","switchboard mat","panel mat",
    "substation mat","rubber mat","iec 61111","is 15652","11kv mat","33kv mat",
    "anti shock mat","electrical mat",
    # arc suits
    "arc flash","arc suit","arc rated","arc flash suit","arc flash ppe",
    "arc flash hood","arc flash jacket","arc flash coverall","arc flash helmet",
    "iec 61482","astm f1506","nfpa 70e","atpv","cal/cm2","8 cal","25 cal","40 cal",
    "flame resistant suit","fr suit","arc protection",
    # general electrical safety (short)
    "electrical ppe","live line ppe","high voltage ppe","electrical safety",
    "electrical insulation","dielectric protection","substation safety",
    "switchgear safety","electrical protective",
]

STANDARDS_TOKENS = [
    "iec 60903","iec 61111","iec 61482","astm d120","astm f1506","astm f2675",
    "nfpa 70e","is 4770","is 15652","en 60903","osha 1910","bis certification",
    "qco electrical","quality control order electrical",
]

INDIA_TOKENS = [
    "india","indian","bharat","mumbai","delhi","bangalore","bengaluru",
    "chennai","hyderabad","pune","kolkata","gujarat","maharashtra",
    "bis ","is 4770","is 15652","dgfasli","pgiel","make in india",
    "ntpc","bhel","ongc","powergrid","tata power","adani","torrent power",
]

# ── HARD DISQUALIFIERS ────────────────────────────────────────────
# Non-Salisbury-product Salisbury references
SALISBURY_BLOCKS = [
    "salisbury journal","salisbury news","salisbury post","the salisbury",
    "salisbury university","salisbury cathedral","salisbury plain",
    "salisbury poisoning","salisbury novichok","salisbury uk",
    "salisbury maryland","salisbury steak","salisbury hospital",
    "salisbury city","salisbury wiltshire","salisbury museum",
]
# Competitor in clearly unrelated context — only block if no product token present
COMP_UNRELATED = [
    # Honeywell non-elec-safety
    ("honeywell","thermostat"),("honeywell","hvac"),("honeywell","aerospace"),
    ("honeywell","aircraft"),("honeywell","defense"),("honeywell","refrigerant"),
    ("honeywell","fire alarm"),("honeywell","process control"),
    ("honeywell","smart home"),("honeywell","security system"),
    ("honeywell","building control"),
    # Ansell non-elec-safety
    ("ansell","surgical"),("ansell","medical glove"),("ansell","exam glove"),
    ("ansell","food handling"),("ansell","chemical glove"),("ansell","nitrile"),
    ("ansell","cut resistant"),
]
# Consumer/academic — always block
ALWAYS_BLOCK = [
    "home appliance","consumer electronic","led bulb","smartphone",
    "laptop charger","television","washing machine","refrigerator",
    "air conditioner","ev battery pack","battery management system",
    "journal of ","doi:10.","pubmed","elsevier journal","springer nature",
    "ieee xplore","sciencedirect","peer-reviewed",
]

# ══════════════════════════════════════════════════════════════════
# ── KEYWORD SCORING MAP ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

KEYWORD_SCORE_MAP = [
    # Brand + Product → 100
    ("salisbury arc flash",100,"Brand+Product"),
    ("salisbury insulating glove",100,"Brand+Product"),
    ("salisbury insulating mat",100,"Brand+Product"),
    ("salisbury class",100,"Brand+Product"),
    ("salisbury rubber glove",100,"Brand+Product"),
    ("honeywell arc flash",100,"Brand+Product"),
    ("honeywell insulating glove",100,"Brand+Product"),
    ("honeywell insulating mat",100,"Brand+Product"),
    ("honeywell electrical safety",100,"Brand+Product"),
    ("catu arc flash",100,"Brand+Product"),
    ("catu insulating glove",100,"Brand+Product"),
    ("catu insulating mat",100,"Brand+Product"),
    ("catu iec 60903",100,"Brand+Product"),
    ("novax insulating glove",100,"Brand+Product"),
    ("novax rubber insulating",100,"Brand+Product"),
    ("novax astm d120",100,"Brand+Product"),
    ("ansell arc flash",100,"Brand+Product"),
    ("ansell electrical glove",100,"Brand+Product"),
    ("ansell insulating",100,"Brand+Product"),
    ("dpl insulating glove",100,"Brand+Product"),
    ("dpl rubber mat",100,"Brand+Product"),
    ("dpl arc flash",100,"Brand+Product"),
    ("mn rubber electrical",100,"Brand+Product"),
    ("mn rubber insulating",100,"Brand+Product"),
    ("jayco insulating",100,"Brand+Product"),
    ("jayco arc flash",100,"Brand+Product"),
    # Standards → 90
    ("iec 60903",90,"Standard"),("iec 61111",90,"Standard"),
    ("iec 61482",90,"Standard"),("astm d120",90,"Standard"),
    ("astm f1506",90,"Standard"),("astm f2675",90,"Standard"),
    ("nfpa 70e",90,"Standard"),("is 4770",90,"Standard"),
    ("is 15652",90,"Standard"),("en 60903",90,"Standard"),
    ("osha 1910.137",90,"Standard"),("atpv",90,"Standard"),
    # Specs → 80
    ("class 00",80,"Spec"),("class 0 ",80,"Spec"),("class 1 ",80,"Spec"),
    ("class 2 ",80,"Spec"),("class 3 ",80,"Spec"),("class 4 ",80,"Spec"),
    ("class a mat",80,"Spec"),("class b mat",80,"Spec"),("class c mat",80,"Spec"),
    ("11kv",80,"Spec"),("33kv",80,"Spec"),("36kv",80,"Spec"),
    ("8 cal",80,"Spec"),("25 cal",80,"Spec"),("40 cal",80,"Spec"),
    ("cal/cm2",80,"Spec"),
    # Core Products → 70
    ("arc flash suit",70,"Core Product"),("arc flash ppe",70,"Core Product"),
    ("arc flash protection",70,"Core Product"),("arc rated suit",70,"Core Product"),
    ("arc flash coverall",70,"Core Product"),("arc flash clothing",70,"Core Product"),
    ("insulating glove",70,"Core Product"),("electrical insulating glove",70,"Core Product"),
    ("rubber insulating glove",70,"Core Product"),("dielectric glove",70,"Core Product"),
    ("high voltage glove",70,"Core Product"),("electrical safety glove",70,"Core Product"),
    ("insulating mat",70,"Core Product"),("dielectric mat",70,"Core Product"),
    ("switchboard mat",70,"Core Product"),("electrical safety mat",70,"Core Product"),
    ("rubber mat electrical",70,"Core Product"),("electrical mat",70,"Core Product"),
    # Technical / Feature → 50
    ("fr fabric",50,"Technical"),("flame resistant",50,"Technical"),
    ("fire retardant",50,"Technical"),("arc rated",50,"Technical"),
    ("dielectric",50,"Technical"),("live line",50,"Technical"),
    ("energized work",50,"Technical"),("electrical hazard",50,"Technical"),
    ("ozone resistant",50,"Technical"),("anti shock mat",50,"Technical"),
    ("voltage rated",50,"Technical"),("electrical ppe",50,"Technical"),
    ("lineman glove",50,"Technical"),("substation safety",50,"Technical"),
    ("switchgear safety",50,"Technical"),("high voltage ppe",50,"Technical"),
    ("arc flash hood",50,"Technical"),("arc flash helmet",50,"Technical"),
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
INTENT_TO_CAT = {
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
    "Financial Results":"#6ee7b7","Other":"#444",
}

# ══════════════════════════════════════════════════════════════════
# ── FILTER LOGIC ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

def has_product_token(text):
    """True if article text contains at least one product/standard token."""
    for t in PRODUCT_TOKENS + STANDARDS_TOKENS:
        if t in text:
            return True
    return False

def get_comp_hits(text):
    return [c for c in COMP_NAMES if c in text]

def is_disqualified(title, summary, source):
    """
    Hard remove. Returns (True, reason) or (False, '').
    IMPORTANT: Only disqualify if the article truly is not about
    electrical safety PPE — always check for product token first.
    """
    text = (title + " " + summary + " " + source).lower()

    # 1. Salisbury non-product references — always block
    for s in SALISBURY_BLOCKS:
        if s in text:
            return True, f"Non-product Salisbury reference"

    # 2. Always-block terms (academic, consumer electronics)
    for s in ALWAYS_BLOCK:
        if s in text:
            # But if article also clearly mentions our products, keep it
            if not has_product_token(text):
                return True, f"Consumer/academic content"

    # 3. Competitor in unrelated context — only block if NO product token
    if not has_product_token(text):
        for comp, unrelated in COMP_UNRELATED:
            if comp in text and unrelated in text:
                return True, f"{comp.title()} in unrelated context ({unrelated})"

    return False, ""

def is_relevant(title, summary):
    """
    Relevance filter — 3 rules:
    Rule 1: Competitor + (another competitor OR any product token OR standard)
    Rule 2: Product/standard token present (even without competitor)
    Rule 3: Article must be within electrical safety universe

    Key fix: Uses SHORT TOKEN matching (not long phrases) so short summaries match.
    """
    text = (title + " " + summary).lower()
    comp_hits = get_comp_hits(text)
    has_comp  = len(comp_hits) > 0
    has_prod  = has_product_token(text)

    # Rule 1: Competitor + electrical safety content
    if has_comp and has_prod:
        return True, comp_hits

    # Rule 1b: Two or more competitors together
    if len(comp_hits) >= 2:
        return True, comp_hits

    # Rule 2: Clear product/standard content without competitor
    if has_prod:
        # Count how many tokens match — need at least 1 strong signal
        matches = [t for t in PRODUCT_TOKENS + STANDARDS_TOKENS if t in text]
        if len(matches) >= 1:
            return True, comp_hits

    # Rule 3: Competitor in title with electrical safety context
    title_lower = title.lower()
    if has_comp and any(t in title_lower for t in PRODUCT_TOKENS + STANDARDS_TOKENS):
        return True, comp_hits

    return False, comp_hits

# ══════════════════════════════════════════════════════════════════
# ── SCORING ENGINE ───────────────────────────────────────────────
# Formula: Score = (KW×0.4) + (Comp×0.3) + (Intent×0.3)
# ══════════════════════════════════════════════════════════════════

def compute_kw_score(title, summary):
    text_full  = (title + " " + summary).lower()
    text_title = title.lower()
    best, best_type, matched, high_ct = 0, "Generic", [], 0
    for pat, base, ktype in KEYWORD_SCORE_MAP:
        if pat in text_full:
            matched.append((pat, base, ktype))
            if base > best: best, best_type = base, ktype
            if base >= 70: high_ct += 1
    if not matched: return 10, "None"
    score = best
    if any(pat in text_title for pat, base, _ in matched if base == best): score += 10
    if high_ct >= 2: score += 10
    return min(score, 100), best_type

def compute_comp_score(text):
    hits  = get_comp_hits(text)
    bonus = len(hits) >= 2
    if not hits: return 20, []
    return min(100 + (10 if bonus else 0), 100), hits

def compute_intent_kw(title, summary):
    t = (title + " " + summary).lower()
    if any(k in t for k in ["new plant","expansion","invest","greenfield","new facility","new manufacturing","capacity increase","brownfield"]):
        return 100,"Investment / Capacity Expansion"
    if any(k in t for k in ["acqui","merger","joint venture","partnership","stake","buyout","takeover","collaboration","alliance"]):
        return 100,"M&A / Partnership"
    if any(k in t for k in ["launch","new product","new model","introduces","unveil","new range","new line","new glove","new suit","new mat"]):
        return 90,"New Product Launch"
    if any(k in t for k in ["innovation","patent","r&d","technology","new material","fr fabric","composite","new design","new tech"]):
        return 85,"Technology / Innovation"
    if any(k in t for k in ["regulat","standard","compliance","bis","qco","mandatory","norms","dgfasli","pgiel","certification","is 4770","is 15652","iec 60903"]):
        return 80,"Regulatory / Compliance"
    if any(k in t for k in ["contract","order","supply deal","tender","award","procurement","large order","supply agreement"]):
        return 75,"Large Order / Contract"
    return 40,"General News / Mention"

def final_score(kw, comp, intent, w_kw=0.4, w_comp=0.3, w_intent=0.3):
    return round((kw * w_kw) + (comp * w_comp) + (intent * w_intent))

def score_label(score):
    if score >= 80: return "🔥 High",   "nb-hi"
    if score >= 60: return "⚡ Medium",  "nb-med"
    if score >= 40: return "🟡 Low",    "nb-low"
    return "❌ Ignore","nb-oth"

def ring_cls(score):
    if score >= 80: return "ring-high"
    if score >= 60: return "ring-med"
    if score >= 40: return "ring-low"
    return "ring-ig"

def sbar_html(score):
    c = ("#ff5e62" if score>=80 else "#f59e0b" if score>=60 else "#f7b731" if score>=40 else "#333")
    return f'<div class="sbar-wrap"><div class="sbar" style="width:{min(score,100)}%;background:{c};"></div></div>'

# ══════════════════════════════════════════════════════════════════
# ── DEDUPLICATION ────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

def deduplicate(articles, threshold=0.82):
    """Fuzzy title match — keep highest-scored version of duplicates."""
    unique = []
    for art in articles:
        dup = False
        for kept in unique:
            if SequenceMatcher(None,
               art["title"].lower(), kept["title"].lower()).ratio() >= threshold:
                if art.get("relevance", 0) > kept.get("relevance", 0):
                    unique.remove(kept); unique.append(art)
                dup = True; break
        if not dup:
            unique.append(art)
    return unique

# ══════════════════════════════════════════════════════════════════
# ── LLM INTENT ───────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

def classify_llm(articles, api_key):
    if not api_key:
        for a in articles:
            is_, intent = compute_intent_kw(a["title"], a["summary"])
            a["intent"]      = intent
            a["intent_score"]= is_
            a["category"]    = INTENT_TO_CAT.get(intent, "Other")
            a["key_insight"] = "Add Groq API key for AI-powered insights"
        return articles

    client = Groq(api_key=api_key)
    intents = list(INTENT_SCORES.keys())
    for a in articles:
        prompt = f"""You are a market intelligence analyst for an electrical safety PPE manufacturer in India.
Products: electrical insulating gloves, rubber insulating mats, arc flash suits.
Competitors: Honeywell, Salisbury, CATU, Novax, Ansell, DPL, MN Rubber, Jayco.
Geography: India focus.

Classify intent into EXACTLY ONE of: {json.dumps(intents)}
Write ONE key insight max 12 words, India-focused.

Title: {a['title']}
Summary: {a['summary']}

Reply ONLY in valid JSON: {{"intent":"...","key_insight":"..."}}"""
        try:
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role":"user","content":prompt}],
                max_tokens=80, temperature=0.1,
            )
            r = json.loads(resp.choices[0].message.content.strip())
            intent = r.get("intent","General News / Mention")
            if intent not in INTENT_SCORES: intent = "General News / Mention"
            a["intent"]      = intent
            a["intent_score"]= INTENT_SCORES[intent]
            a["category"]    = INTENT_TO_CAT.get(intent,"Other")
            a["key_insight"] = r.get("key_insight","—")
        except Exception:
            is_, intent = compute_intent_kw(a["title"], a["summary"])
            a["intent"]=intent; a["intent_score"]=is_
            a["category"]=INTENT_TO_CAT.get(intent,"Other"); a["key_insight"]="—"
        time.sleep(0.3)
    return articles

# ══════════════════════════════════════════════════════════════════
# ── NEWS FETCH PIPELINE ──────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

def fetch_google_news(query, days_back=30):
    """Fetch from Google News RSS. Append 'India' only if not already present."""
    iq  = f"{query} India" if "india" not in query.lower() else query
    url = (f"https://news.google.com/rss/search?"
           f"q={urllib.parse.quote(iq)}&hl=en-IN&gl=IN&ceid=IN:en")
    try:
        feed = feedparser.parse(url)
    except Exception:
        return []
    cutoff = datetime.now() - timedelta(days=days_back)
    out = []
    for e in feed.entries:
        try:    pub = datetime(*e.published_parsed[:6])
        except: pub = datetime.now()
        if pub >= cutoff:
            out.append({
                "title":   e.title,
                "link":    e.link,
                "published": pub,
                "source":  e.get("source",{}).get("title","Unknown"),
                "summary": e.get("summary","")[:500],
                "query":   query,
            })
    return out

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_all_news(queries_tuple, days_back, api_key, w_kw, w_comp, w_intent):
    # ── Step 1: Fetch all raw articles
    raw = []
    for q in queries_tuple:
        raw.extend(fetch_google_news(q, days_back))
        time.sleep(0.12)

    # ── Step 2: Title-exact dedup first (fast)
    seen_titles = set()
    deduped_raw = []
    for a in raw:
        if a["title"] not in seen_titles:
            seen_titles.add(a["title"]); deduped_raw.append(a)

    # ── Step 3: Hard disqualify
    kept, removed = [], []
    for a in deduped_raw:
        disq, reason = is_disqualified(a["title"], a["summary"], a["source"])
        if disq:
            a["discard_reason"] = reason; removed.append(a)
        else:
            kept.append(a)

    # ── Step 4: Relevance filter (3-rule logic with token matching)
    relevant, irrelevant = [], []
    for a in kept:
        rel, comp_hits = is_relevant(a["title"], a["summary"])
        if rel:
            a["comp_hits_rel"] = comp_hits; relevant.append(a)
        else:
            a["discard_reason"] = "Failed relevance: no product token + competitor combo"
            irrelevant.append(a)
    removed += irrelevant

    # ── Step 5: Score every relevant article
    for a in relevant:
        text = (a["title"] + " " + a["summary"]).lower()
        kw_s, kw_type      = compute_kw_score(a["title"], a["summary"])
        cs,   comp_hits    = compute_comp_score(text)
        is_,  intent       = compute_intent_kw(a["title"], a["summary"])
        fs = final_score(kw_s, cs, is_, w_kw, w_comp, w_intent)
        a.update({
            "kw_score":kw_s, "kw_type":kw_type,
            "comp_score":cs, "comp_hits":comp_hits,
            "intent":intent, "intent_score":is_,
            "relevance":fs,  "category":INTENT_TO_CAT.get(intent,"Other"),
            "key_insight":"",
            "score_breakdown":(
                f"KW:{kw_s}({kw_type})×{w_kw} + "
                f"Comp:{cs}({'|'.join(comp_hits) if comp_hits else 'none'})×{w_comp} + "
                f"Intent:{is_}({intent})×{w_intent} = {fs}"
            ),
        })

    # ── Step 6: Fuzzy dedup (catches same story from multiple sources)
    relevant = deduplicate(relevant, threshold=0.82)

    # ── Step 7: LLM intent refinement
    relevant = classify_llm(relevant, api_key)

    # ── Step 8: Re-score with LLM intent + recompute breakdown
    for a in relevant:
        fs = final_score(a["kw_score"], a["comp_score"], a["intent_score"], w_kw, w_comp, w_intent)
        a["relevance"] = fs
        a["score_breakdown"] = (
            f"KW:{a['kw_score']}({a['kw_type']})×{w_kw} + "
            f"Comp:{a['comp_score']}({'|'.join(a['comp_hits']) if a['comp_hits'] else 'none'})×{w_comp} + "
            f"Intent:{a['intent_score']}({a['intent']})×{w_intent} = {fs}"
        )

    relevant.sort(key=lambda x: x["relevance"], reverse=True)
    return relevant, removed

def build_queries(sel_comp, sel_groups, inc_comp_kw):
    q = list(sel_comp)
    for g in sel_groups: q.extend(ALL_KEYWORD_GROUPS.get(g, []))
    if inc_comp_kw: q.extend(COMPETITOR_KEYWORDS)
    seen, u = set(), []
    for x in q:
        if x not in seen: seen.add(x); u.append(x)
    return u

# ══════════════════════════════════════════════════════════════════
# ── SIDEBAR ──────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## ⚡ SafeIntel")
    st.markdown("**Electrical Safety · 🇮🇳 India**")
    st.markdown('<div style="background:linear-gradient(90deg,#f7b731,#ff5e62);height:2px;border-radius:2px;margin-bottom:16px;"></div>', unsafe_allow_html=True)

    st.markdown('<div class="sh">🔑 API Key</div>', unsafe_allow_html=True)
    try:    api_key = st.secrets.get("GROQ_API_KEY","")
    except: api_key = ""
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    st.markdown('<div class="sh">🏭 Competitors</div>', unsafe_allow_html=True)
    sel_comp = st.multiselect("Select competitors", COMPETITORS, default=COMPETITORS)
    new_co   = st.text_input("➕ Add competitor", placeholder="e.g. Karam Industries")
    if new_co: sel_comp.append(new_co)

    st.markdown('<div class="sh">📦 Products & Keywords</div>', unsafe_allow_html=True)
    product_lines = st.multiselect(
        "Product lines",
        ["🧤 Gloves","🟫 Mats","🦺 Arc Suits","🌐 Common"],
        default=["🧤 Gloves","🟫 Mats","🦺 Arc Suits","🌐 Common"],
    )
    avail_grp = [g for g in ALL_KEYWORD_GROUPS
                 if any(pl.split(" ")[0] in g for pl in product_lines) or "Common" in g]
    sel_groups   = st.multiselect("Keyword groups", avail_grp, default=avail_grp)
    inc_comp_kw  = st.checkbox("Competitor-specific keywords", value=True)

    st.markdown('<div class="sh">📅 Filters</div>', unsafe_allow_html=True)
    days_back      = st.slider("Days of news", 7, 90, 30)
    selected_cats  = st.multiselect("Categories", CATEGORIES, default=CATEGORIES)
    min_score      = st.slider("Min score (0–100)", 0, 100, 30,
                                help="Recommended: 30+ to catch all relevant articles")
    show_discard   = st.checkbox("Show discarded articles", value=False)
    show_breakdown = st.checkbox("Show score breakdown", value=False)

    st.markdown('<div class="sh">⚖️ Score Weights</div>', unsafe_allow_html=True)
    w_kw     = st.slider("Keyword weight",    0.0, 1.0, 0.4, 0.05)
    w_comp   = st.slider("Competitor weight", 0.0, 1.0, 0.3, 0.05)
    w_intent = st.slider("Intent weight",     0.0, 1.0, 0.3, 0.05)
    wt = round(w_kw + w_comp + w_intent, 2)
    if abs(wt - 1.0) > 0.05: st.warning(f"⚠️ Weights = {wt} (should be 1.0)")

    fetch_btn = st.button("⚡ Fetch & Analyse News")

# ══════════════════════════════════════════════════════════════════
# ── HERO ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero">
  <div class="hero-title">Electrical Safety Market Intelligence</div>
  <div class="hero-sub">Gloves · Mats · Arc Suits · 9 Competitors · 200+ Keywords · 🇮🇳 India Only</div>
  <div class="hero-pills">
    <span class="hero-pill">🧤 Gloves</span>
    <span class="hero-pill">🟫 Mats</span>
    <span class="hero-pill">🦺 Arc Suits</span>
    <span class="hero-pill">🇮🇳 India Focused</span>
    <span class="hero-pill">⚡ Weighted Scoring</span>
    <span class="hero-pill">🔁 Deduplication ON</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ── MAIN DASHBOARD ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════

if fetch_btn or "intel_data" in st.session_state:
    if fetch_btn:
        queries = build_queries(sel_comp, sel_groups, inc_comp_kw)
        st.info(f"🔍 Running **{len(queries)} queries** — strict electrical safety filter · dedup ON · India-focused")
        with st.spinner("Fetching, filtering, scoring, deduplicating…"):
            kept, removed = fetch_all_news(
                tuple(queries), days_back, api_key or "",
                w_kw, w_comp, w_intent
            )
            st.session_state["intel_data"]   = kept
            st.session_state["removed_data"] = removed

    kept    = st.session_state.get("intel_data",   [])
    removed = st.session_state.get("removed_data", [])
    df      = pd.DataFrame(kept)    if kept    else pd.DataFrame()
    df_rem  = pd.DataFrame(removed) if removed else pd.DataFrame()

    if df.empty:
        st.warning("⚠️ No articles found. Try: (1) increase Days slider to 60–90, (2) lower Min Score to 20, (3) check your keyword group selections in the sidebar.")
    else:
        df_f = df[df["category"].isin(selected_cats) & (df["relevance"] >= min_score)].copy()

        # ── TABS ─────────────────────────────────────────────────
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📰 Intelligence Feed",
            "🏭 Competitors",
            "📦 Products",
            "📋 Regulatory",
            "📈 Trends",
        ])

        # ═══════════════════════════════
        # TAB 1 — FEED
        # ═══════════════════════════════
        with tab1:
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
            # Metrics
            c1,c2,c3,c4,c5 = st.columns(5)
            for col, val, lbl, cls, delta in [
                (c1, len(df_f),                                         "Relevant Articles","mc1", f"of {len(df)} total"),
                (c2, len(df_f[df_f["relevance"]>=80]),                  "🔥 High Priority", "mc2", "score ≥ 80"),
                (c3, len(removed),                                       "Auto-Filtered",    "mc3", "noise removed"),
                (c4, len(df_f[df_f["intent"]=="M&A / Partnership"]),    "M&A Signals",      "mc4", "partnerships · deals"),
                (c5, round(df_f["relevance"].mean(),1) if len(df_f) else 0, "Avg Score",   "mc5", "out of 100"),
            ]:
                col.markdown(
                    f'<div class="mcard {cls}">'
                    f'<div class="mnum">{val}</div>'
                    f'<div class="mlbl">{lbl}</div>'
                    f'<div class="mdelta">{delta}</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)

            # Charts
            ch1, ch2 = st.columns(2)
            with ch1:
                cat_df = df_f["category"].value_counts().reset_index()
                cat_df.columns = ["Category","Count"]
                fig = px.bar(cat_df, x="Count", y="Category", orientation="h",
                             color="Category", color_discrete_map=CAT_COLORS,
                             title="Articles by Category")
                fig.update_layout(
                    plot_bgcolor="#0a0a1a", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#888", showlegend=False,
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig, use_container_width=True)
            with ch2:
                bands = pd.cut(df_f["relevance"],bins=[0,39,59,79,100],
                               labels=["❌ <40","🟡 40–59","⚡ 60–79","🔥 80–100"])
                bd = bands.value_counts().reset_index()
                bd.columns = ["Band","Count"]
                fig2 = px.bar(bd, x="Band", y="Count", color="Band",
                              color_discrete_map={"🔥 80–100":"#ff5e62","⚡ 60–79":"#f59e0b",
                                                  "🟡 40–59":"#f7b731","❌ <40":"#2a2a3a"},
                              title="Score Distribution")
                fig2.update_layout(
                    plot_bgcolor="#0a0a1a", paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#888", showlegend=False,
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig2, use_container_width=True)

            # Feed filters
            fc1,fc2,fc3 = st.columns([2,1,1])
            with fc1: srch = st.text_input("🔎 Search","", placeholder="e.g. Honeywell, IEC 60903, arc flash…")
            with fc2: fp   = st.selectbox("Product",["All","Gloves","Mats","Arc Suits"])
            with fc3: sb   = st.selectbox("Sort",["Highest score","Latest first"])

            df_show = df_f.copy()
            if srch: df_show = df_show[df_show["title"].str.contains(srch,case=False,na=False)]
            if fp != "All":
                pm = {"Gloves":ALL_GLOVE_KW,"Mats":ALL_MAT_KW,"Arc Suits":ALL_ARC_KW}
                df_show = df_show[df_show["query"].isin(pm[fp])]
            if sb == "Latest first":
                df_show = df_show.sort_values("published",ascending=False)

            st.markdown(
                f'<div style="font-size:0.76rem;color:#444;margin-bottom:10px;">'
                f'Showing <b style="color:#e0e0ff">{len(df_show)}</b> articles · '
                f'<b style="color:#444">{len(removed)}</b> removed</div>',
                unsafe_allow_html=True
            )

            for _, row in df_show.iterrows():
                sc          = row.get("relevance",0)
                slbl, sbdg  = score_label(sc)
                cbc         = CAT_BADGE.get(row.get("category","Other"),"nb-oth")
                comp_str    = ", ".join(row.get("comp_hits",[]) or []) or "—"
                ki          = row.get("key_insight","—") or "—"
                bd          = row.get("score_breakdown","—")

                st.markdown(f"""
                <div class="ncard">
                  <div class="score-ring {ring_cls(sc)}">{sc}</div>
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
                    {sbar_html(sc)}
                    <div class="nmeta">
                      🗞️ {row['source']} &nbsp;|&nbsp;
                      📅 {row['published'].strftime('%d %b %Y')} &nbsp;|&nbsp;
                      🎯 {row.get('intent','—')} &nbsp;|&nbsp;
                      💡 {ki}
                    </div>
                    {"<div class='score-bd'>📐 "+bd+"</div>" if show_breakdown else ""}
                  </div>
                </div>""", unsafe_allow_html=True)

            if show_discard and not df_rem.empty:
                st.markdown("---")
                st.markdown(f"**❌ Discarded Articles ({len(df_rem)})**")
                for _, row in df_rem.iterrows():
                    st.markdown(f"""
                    <div class="ncard" style="opacity:0.35;border-color:#1a1a2e;">
                      <div class="score-ring ring-ig">✗</div>
                      <div style="flex:1;">
                        <div class="ntitle" style="color:#444;">{row['title']}</div>
                        <div class="nmeta">❌ {row.get('discard_reason','—')} · 🗞️ {row['source']}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

            # Export
            st.markdown("---")
            e1,e2 = st.columns(2)
            ec = ["title","category","relevance","intent","kw_score","comp_score",
                  "comp_hits","key_insight","score_breakdown","source","published","link"]
            out  = df_show[[c for c in ec if c in df_show.columns]].copy()
            full = df[[c for c in ec if c in df.columns]].copy()
            for d in [out, full]:
                if "published" in d.columns:
                    d["published"] = d["published"].dt.strftime("%Y-%m-%d")
            with e1: st.download_button("⬇️ Filtered CSV", out.to_csv(index=False),
                        f"intel_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")
            with e2: st.download_button("⬇️ Full CSV", full.to_csv(index=False),
                        f"intel_full_{datetime.now().strftime('%Y%m%d')}.csv","text/csv")

        # ═══════════════════════════════
        # TAB 2 — COMPETITORS
        # ═══════════════════════════════
        with tab2:
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">🏭 Competitor Activity</div>', unsafe_allow_html=True)
            colors = ["#a78bfa","#ff8585","#34d399","#fcd34d","#93c5fd",
                      "#67e8f9","#fb923c","#f472b6","#a3e635"]
            rows = []
            for i, cn in enumerate(COMP_NAMES):
                mask = df["comp_hits"].apply(lambda x: cn in x if isinstance(x,list) else False)
                sub  = df[mask]
                if len(sub) == 0: continue
                col = colors[i % len(colors)]
                pct = int(sub["relevance"].mean())
                sl, _ = score_label(pct)
                rows.append({"Competitor":cn.title(),"Articles":len(sub),
                              "Avg Score":pct,"High":len(sub[sub["relevance"]>=80]),
                              "Top Intent":sub["intent"].mode()[0],"Color":col})
                st.markdown(f"""
                <div class="comp-card">
                  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                    <div style="font-family:'Syne',sans-serif;font-weight:700;font-size:0.95rem;color:{col};">{cn.title()}</div>
                    <div style="display:flex;gap:6px;">
                      <span class="nbadge nb-med">{len(sub)} articles</span>
                      <span class="nbadge nb-hi">{len(sub[sub['relevance']>=80])} 🔥</span>
                    </div>
                  </div>
                  <div class="sbar-wrap" style="height:5px;"><div class="sbar" style="width:{pct}%;background:{col};height:5px;"></div></div>
                  <div class="nmeta" style="margin-top:5px;">Avg Score: <b style="color:{col};">{pct}/100</b> &nbsp;|&nbsp; Top Intent: {sub['intent'].mode()[0]}</div>
                </div>""", unsafe_allow_html=True)

            if rows:
                cdf = pd.DataFrame(rows)
                fig = px.bar(cdf, x="Competitor", y="Avg Score", color="Competitor",
                             color_discrete_sequence=colors,
                             title="Competitor Average Relevance Score")
                fig.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#888",showlegend=False,
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    yaxis=dict(gridcolor="#1a1a2e",range=[0,100]),
                    xaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig, use_container_width=True)

        # ═══════════════════════════════
        # TAB 3 — PRODUCTS
        # ═══════════════════════════════
        with tab3:
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">📦 Product Line Intelligence</div>', unsafe_allow_html=True)
            p1,p2,p3 = st.columns(3)
            for col, em, lbl, kws, cls in [
                (p1,"🧤","Insulating Gloves", ALL_GLOVE_KW,"mc1"),
                (p2,"🟫","Insulating Mats",   ALL_MAT_KW,  "mc3"),
                (p3,"🦺","Arc Flash Suits",   ALL_ARC_KW,  "mc2"),
            ]:
                sub = df[df["query"].isin(kws)] if "query" in df.columns else pd.DataFrame()
                col.markdown(
                    f'<div class="mcard {cls}" style="text-align:left;">'
                    f'<div style="font-size:1.6rem;margin-bottom:4px;">{em}</div>'
                    f'<div class="mnum">{len(sub)}</div>'
                    f'<div class="mlbl">{lbl}</div>'
                    f'<div class="mdelta">Avg: {round(sub["relevance"].mean(),1) if len(sub) else 0}/100</div>'
                    f'</div>', unsafe_allow_html=True
                )

            for plbl, kws in [("🧤 Gloves",ALL_GLOVE_KW),("🟫 Mats",ALL_MAT_KW),("🦺 Arc Suits",ALL_ARC_KW)]:
                sub = df_f[df_f["query"].isin(kws)].head(5) if "query" in df_f.columns else pd.DataFrame()
                if not sub.empty:
                    st.markdown(f'<div class="sec-title" style="margin-top:18px;">{plbl} — Top Articles</div>', unsafe_allow_html=True)
                    for _, row in sub.iterrows():
                        sc = row.get("relevance",0)
                        sl, _ = score_label(sc)
                        st.markdown(f"""
                        <div class="ncard">
                          <div class="score-ring {ring_cls(sc)}">{sc}</div>
                          <div style="flex:1;">
                            <div class="ntitle"><a href="{row['link']}" target="_blank" style="color:#e8e8ff;text-decoration:none;">{row['title']}</a></div>
                            <div class="nmeta">🗞️ {row['source']} · 📅 {row['published'].strftime('%d %b %Y')} · {sl}</div>
                          </div>
                        </div>""", unsafe_allow_html=True)

        # ═══════════════════════════════
        # TAB 4 — REGULATORY
        # ═══════════════════════════════
        with tab4:
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">📋 Regulatory & Compliance · India</div>', unsafe_allow_html=True)
            reg = df_f[df_f["category"]=="Regulatory Change"]
            if reg.empty:
                st.info("No regulatory articles in current results. Try increasing the time range.")
            else:
                st.markdown(f'<div class="info-box">⚠️ <b>{len(reg)} regulatory alerts</b> · Standards: IS 4770 · IS 15652 · IEC 60903 · IEC 61111 · IEC 61482 · NFPA 70E · BIS QCO · CEA · DGFASLI</div>', unsafe_allow_html=True)
                for _, row in reg.iterrows():
                    sc = row.get("relevance",0)
                    sl, _ = score_label(sc)
                    st.markdown(f"""
                    <div class="ncard" style="border-color:rgba(255,94,98,0.25);">
                      <div class="score-ring {ring_cls(sc)}">{sc}</div>
                      <div style="flex:1;">
                        <div class="ntitle"><a href="{row['link']}" target="_blank" style="color:#e8e8ff;text-decoration:none;">{row['title']}</a></div>
                        <div class="nbadges"><span class="nbadge nb-reg">📋 Regulatory</span><span class="nbadge nb-hi">{sl} {sc}/100</span></div>
                        <div class="nmeta">🗞️ {row['source']} · 📅 {row['published'].strftime('%d %b %Y')} · 💡 {row.get('key_insight','—')}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

        # ═══════════════════════════════
        # TAB 5 — TRENDS
        # ═══════════════════════════════
        with tab5:
            st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-title">📈 Intelligence Trends</div>', unsafe_allow_html=True)
            if len(df_f) > 0:
                df_f2 = df_f.copy()
                df_f2["week"] = df_f2["published"].dt.to_period("W").astype(str)
                trend = df_f2.groupby(["week","category"]).size().reset_index(name="count")
                fig_t = px.line(trend, x="week", y="count", color="category",
                                color_discrete_map=CAT_COLORS,
                                title="Weekly Intelligence Volume", markers=True)
                fig_t.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#888",legend=dict(bgcolor="rgba(0,0,0,0)",font_size=10),
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig_t, use_container_width=True)

                sc_trend = df_f2.groupby("week")["relevance"].mean().reset_index()
                sc_trend.columns = ["week","avg_score"]
                fig_s = px.area(sc_trend, x="week", y="avg_score",
                                title="Avg Relevance Score Over Time",
                                color_discrete_sequence=["#f7b731"])
                fig_s.update_traces(fill="tozeroy",fillcolor="rgba(247,183,49,0.07)",line_color="#f7b731")
                fig_s.update_layout(
                    plot_bgcolor="#0a0a1a",paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#888",
                    title_font=dict(family="Syne",size=13,color="#e0e0ff"),
                    margin=dict(l=10,r=10,t=36,b=10),
                    xaxis=dict(gridcolor="#1a1a2e"),yaxis=dict(gridcolor="#1a1a2e"),
                )
                st.plotly_chart(fig_s, use_container_width=True)

# ── LANDING PAGE ──────────────────────────────────────────────────
else:
    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
    <b>📐 Formula:</b> Score = (Keyword × 0.4) + (Competitor × 0.3) + (Intent × 0.3) &nbsp;|&nbsp;
    🔥 80–100 Immediate &nbsp; ⚡ 60–79 Track &nbsp; 🟡 40–59 Optional &nbsp; ❌ &lt;40 Filtered
    </div>""", unsafe_allow_html=True)

    r1,r2,r3 = st.columns(3)
    for col, cls, num, title, desc in [
        (r1,"mc1","1","Competitor + Combo","Competitor + another competitor OR product token OR standard → RELEVANT"),
        (r2,"mc3","2","Product / Standard Focus","Articles about gloves/mats/arc suits or standards kept even without competitor mention"),
        (r3,"mc2","3","Strict Electrical Safety","Honeywell HVAC, Ansell medical, fire safety, Salisbury Journal — all auto-blocked"),
    ]:
        col.markdown(f"""
        <div class="mcard {cls}" style="text-align:left;padding:18px;min-height:130px;">
          <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#f7b731;margin-bottom:6px;">Rule {num}</div>
          <div style="font-weight:700;color:#e0e0ff;font-size:0.85rem;margin-bottom:6px;">{title}</div>
          <div style="font-size:0.74rem;color:#555;line-height:1.5;">{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">🏭 Competitors Tracked</div>', unsafe_allow_html=True)
    colors = ["#a78bfa","#ff8585","#34d399","#fcd34d","#93c5fd","#67e8f9","#fb923c","#f472b6","#a3e635"]
    cc = st.columns(5)
    for i, co in enumerate(COMPETITORS):
        with cc[i%5]:
            st.markdown(
                f'<div class="mcard" style="padding:10px;margin-bottom:8px;border-top:2px solid {colors[i%len(colors)]};">'
                f'<div style="font-size:0.78rem;color:#e0e0ff;font-weight:600;">{co}</div></div>',
                unsafe_allow_html=True
            )
