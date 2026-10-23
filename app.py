import os
import textwrap
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from evidence import (
    load_initial_evidence_register,
    get_hidden_catalogue,
    request_hidden_evidence,
    validate_evidence_ids,
    read_pdf,
    read_email,
    read_text
)
from investigator import (
    build_timeline,
    detect_conflicts,
    ask_investigation_assistant
)
from evaluator import (
    RUBRIC_CRITERIA,
    validate_submission_inputs,
    evaluate_decision_with_llm,
    record_submission_attempt
)
from report import generate_investigation_report, generate_investigation_report_txt
from copilot import ask_copilot

load_dotenv()

# Production Page Configuration
st.set_page_config(
    page_title="Evidence to Decision Simulator | Case PO-88421",
    page_icon="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to prevent python markdown from treating indented HTML as indented code blocks
def render_html(html_str: str):
    cleaned_lines = [line.strip() for line in html_str.strip().splitlines()]
    clean_html = "\n".join(cleaned_lines)
    st.markdown(clean_html, unsafe_allow_html=True)

DESIGN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400;1,6..72,500;1,6..72,600&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-white: #FFFFFF;
    --bg-surface-0: #F8FAFC;
    --bg-surface-1: #FFFFFF;
    --bg-surface-2: #F1F5F9;
    --bg-surface-3: #E2E8F0;
    
    /* Signature Papaya Orange Accents */
    --papaya-orange: #FF7A30;
    --papaya-orange-hover: #FF8F4D;
    --papaya-orange-dark: #E65C10;
    --papaya-glow: rgba(255, 122, 48, 0.28);
    --papaya-subtle: rgba(255, 122, 48, 0.12);
    --papaya-border: rgba(255, 122, 48, 0.35);
    
    --border-hairline: #E2E8F0;
    --border-medium: #CBD5E1;
    --border-prominent: #94A3B8;
    
    --text-pure-black: #000000;
    --text-charcoal: #0F172A;
    --text-slate: #334155;
    --text-muted: #64748B;
    
    --font-sans: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    --font-serif: 'Newsreader', Georgia, serif;
    --font-mono: 'JetBrains Mono', monospace;
}

/* Minimalistic Fancy Startup Loading Screen (White Canvas) */
#startup-loader {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: #FFFFFF;
    z-index: 99999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    animation: loaderDissolve 2.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes loaderDissolve {
    0% { opacity: 1; visibility: visible; }
    70% { opacity: 1; visibility: visible; }
    92% { opacity: 0; visibility: visible; transform: scale(1.01); }
    100% { opacity: 0; visibility: hidden; display: none; }
}

.loader-content {
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    max-width: 640px;
    padding: 24px;
    animation: loaderContentFade 1.8s ease-out forwards;
}

@keyframes loaderContentFade {
    0% { opacity: 0; transform: translateY(14px); }
    25% { opacity: 1; transform: translateY(0); }
    82% { opacity: 1; transform: translateY(0); }
    100% { opacity: 0; transform: translateY(-8px); }
}

.loader-badge {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #C2410C;
    background: rgba(255, 122, 48, 0.12);
    border: 1px solid rgba(255, 122, 48, 0.4);
    padding: 5px 16px;
    border-radius: 999px;
    margin-bottom: 20px;
    box-shadow: 0 0 16px rgba(255, 122, 48, 0.18);
}

.loader-title {
    font-family: var(--font-sans);
    font-size: 2.4rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.04em;
    margin-bottom: 8px;
    line-height: 1.15;
}

.loader-sub {
    font-family: var(--font-serif);
    font-size: 1.15rem;
    font-style: italic;
    color: #475569;
    margin-bottom: 30px;
}

.loader-bar-container {
    width: 260px;
    height: 3px;
    background: #E2E8F0;
    border-radius: 999px;
    overflow: hidden;
    position: relative;
    margin-bottom: 16px;
}

.loader-bar {
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 0%;
    background: linear-gradient(90deg, #FF7A30, #FF9955);
    box-shadow: 0 0 10px rgba(255, 122, 48, 0.4);
    animation: loaderProgress 1.5s cubic-bezier(0.65, 0, 0.35, 1) forwards;
}

@keyframes loaderProgress {
    0% { width: 0%; }
    40% { width: 55%; }
    80% { width: 88%; }
    100% { width: 100%; }
}

.loader-status {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 2px;
    color: #64748B;
    text-transform: uppercase;
}

/* Scroll-Triggered Dynamic Animation System */
@keyframes scrollFadeReveal {
    0% {
        opacity: 0;
        transform: translateY(28px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

@supports (animation-timeline: view()) {
    .space-card, .kpi-card, .timeline-track-item, [data-testid="stExpander"], .stAlert {
        animation: scrollFadeReveal linear both;
        animation-timeline: view();
        animation-range: entry 5% cover 30%;
    }
}

@supports not (animation-timeline: view()) {
    .space-card, .kpi-card, .timeline-track-item, [data-testid="stExpander"], .stAlert {
        opacity: 1;
        transform: none;
    }
}

/* KPI Metric Cards (Clean Institutional Design with Cross / Check Icons) */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 16px;
}
@media (max-width: 900px) {
    .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-card:hover {
    border-color: #CBD5E1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    transform: translateY(-1px);
}
.kpi-label {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: #475569;
    margin-bottom: 6px;
}
.kpi-value {
    font-family: var(--font-sans);
    font-size: 1.55rem;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
    margin-bottom: 8px;
    letter-spacing: -0.02em;
}
.kpi-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    width: fit-content;
    font-family: var(--font-mono);
    font-size: 0.73rem;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 4px;
    line-height: 1.3;
}
.kpi-badge-neutral {
    background: #F1F5F9;
    color: #334155;
    border: 1px solid #E2E8F0;
}
.kpi-badge-deficit {
    background: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FCA5A5;
}
.kpi-badge-warning {
    background: #FFFBEB;
    color: #D97706;
    border: 1px solid #FCD34D;
}
.kpi-badge-verified {
    background: #F0FDF4;
    color: #16A34A;
    border: 1px solid #86EFAC;
}
.kpi-badge-icon {
    font-weight: 700;
    font-size: 0.82rem;
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden; display: none !important;}
footer {visibility: hidden; display: none !important;}
header {visibility: hidden; display: none !important;}
[data-testid="stToolbar"] {visibility: hidden; display: none !important;}
[data-testid="stDecoration"] {visibility: hidden; display: none !important;}
[data-testid="stStatusWidget"] {visibility: hidden; display: none !important;}
.viewerBadge_container__1QSob {visibility: hidden; display: none !important;}

/* Full-bleed layout */
.block-container {
    padding-top: 1.6rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 97% !important;
}

/* Base Canvas & Resets: Ultra-Faint Technical Grid Background */
html, body, [class*="css"] {
    font-family: var(--font-sans) !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.stApp, [data-testid="stAppViewContainer"], section.main {
    background-color: #FAFAFA !important;
    background-image: 
        linear-gradient(to right, rgba(0, 0, 0, 0.016) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(0, 0, 0, 0.016) 1px, transparent 1px) !important;
    background-size: 24px 24px !important;
    background-position: 0 0 !important;
    color: var(--text-charcoal) !important;
}

/* Left Sidebar: Solid Normal White Background (NO grid, NO transparency) */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarContent"],
section[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    background-image: none !important;
    border-right: 1px solid #E2E8F0 !important;
}

/* E2D Brand Logo */
.e2d-brand-badge {
    display: flex;
    flex-direction: column;
    padding: 8px 0 16px 0;
}
.e2d-brand-logo {
    display: inline-flex;
    align-items: baseline;
    font-family: var(--font-sans);
    font-size: 5.17rem;
    line-height: 1;
    letter-spacing: -0.05em;
    user-select: none;
}
.e2d-brand-logo .e2d-char {
    font-weight: 800;
    font-style: normal;
    color: #0F172A;
    display: inline-block;
}
.e2d-brand-logo .e2d-two {
    font-weight: 900;
    font-style: italic;
    color: #FF7A30;
    display: inline-block;
    padding: 0 4px;
    transform: skewX(-6deg);
    text-shadow: 0 4px 16px rgba(255, 122, 48, 0.35);
}
.e2d-brand-logo .e2d-dot {
    display: inline-block;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    background: #FF7A30;
    margin-left: 6px;
    margin-bottom: 8px;
    box-shadow: 0 0 12px rgba(255, 122, 48, 0.5);
}
.e2d-case-label {
    font-family: var(--font-mono);
    font-size: 1.63rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #475569;
    margin-top: 10px;
}

[data-testid="stSidebar"] hr {
    border-color: var(--border-hairline) !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-charcoal);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li {
    color: var(--text-slate) !important;
}

/* Typography Hierarchy - Sharp High Contrast Black/Charcoal */
h1 {
    font-family: var(--font-sans) !important;
    font-size: 2.15rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.035em !important;
    color: var(--text-pure-black) !important;
    line-height: 1.15 !important;
    margin-bottom: 0.2rem !important;
}

h2 {
    font-family: var(--font-sans) !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.025em !important;
    color: var(--text-pure-black) !important;
    margin-top: 1.1rem !important;
    margin-bottom: 0.4rem !important;
}

h3 {
    font-family: var(--font-sans) !important;
    font-size: 1.12rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: var(--text-pure-black) !important;
}

h4 {
    font-family: var(--font-sans) !important;
    font-size: 0.96rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    color: var(--text-charcoal) !important;
}

p, li {
    font-family: var(--font-sans);
    color: var(--text-slate) !important;
    line-height: 1.6;
    font-size: 0.91rem;
}

.editorial-narrative {
    font-family: var(--font-serif) !important;
    font-size: 1.05rem !important;
    line-height: 1.68 !important;
    color: #1E293B !important;
    letter-spacing: -0.005em !important;
}

.editorial-quote {
    font-family: var(--font-serif) !important;
    font-style: italic !important;
    font-size: 1.08rem !important;
    line-height: 1.6 !important;
    color: #0F172A !important;
    border-left: 3px solid #FF7A30 !important;
    padding-left: 16px !important;
    margin: 10px 0 !important;
}

/* Space Card Containers - Clean White Elevation */
.space-card {
    background: #FFFFFF !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 10px !important;
    padding: 18px 22px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05) !important;
    transition: border-color 160ms ease, box-shadow 160ms ease !important;
}

.space-card:hover {
    border-color: var(--border-medium) !important;
    box-shadow: 0 4px 12px -2px rgba(0, 0, 0, 0.08) !important;
}

.card-panel {
    background: #FFFFFF !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 10px !important;
    padding: 18px 22px !important;
    margin-bottom: 14px !important;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
}

/* Metric Display Cards: Elevated Solid White Structure */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid var(--border-hairline) !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    transition: border-color 150ms ease, transform 150ms ease !important;
}

[data-testid="stMetric"]:hover {
    border-color: var(--border-medium) !important;
}

[data-testid="stMetricLabel"] {
    font-family: var(--font-sans) !important;
    font-size: 0.74rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
}

[data-testid="stMetricValue"] {
    font-family: var(--font-sans) !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: var(--text-pure-black) !important;
}

/* Institutional Tab Navigation: Elevated White Card Bar */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    padding: 6px !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-hairline) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    margin-bottom: 22px !important;
    overflow-x: auto !important;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
    height: 4px !important;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
    background: #CBD5E1 !important;
    border-radius: 4px !important;
}

/* Eliminate dark overflow gradient masks and paginators */
.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"],
.stTabs div[class*="StyledScrollPaginator"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-list"]::after,
.stTabs [data-baseweb="tab-list"]::before {
    display: none !important;
    content: none !important;
}

.stTabs [data-baseweb="tab"] {
    height: 38px !important;
    padding: 0 14px !important;
    background-color: transparent !important;
    border-radius: 6px !important;
    border: none !important;
    color: var(--text-slate) !important;
    font-family: var(--font-sans) !important;
    font-size: 0.84rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
    transition: color 130ms ease, background-color 130ms ease !important;
}

.stTabs [data-baseweb="tab"] p, .stTabs [data-baseweb="tab"] span {
    color: var(--text-slate) !important;
    -webkit-text-fill-color: var(--text-slate) !important;
}

.stTabs [aria-selected="true"] {
    background-color: #F8FAFC !important;
    background: #F8FAFC !important;
    color: var(--text-pure-black) !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #FF7A30 !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
}

.stTabs [aria-selected="true"] p, .stTabs [aria-selected="true"] span {
    color: var(--text-pure-black) !important;
    -webkit-text-fill-color: var(--text-pure-black) !important;
    font-weight: 700 !important;
}

/* ========================================================================== */
/* ELEVATED BUTTON SYSTEM: CLEAN SOLID CARDS & CRISP CONTRAST                 */
/* ========================================================================== */

/* 1. Primary Action & Download Buttons: Elevated Papaya Gradient Cards */
button[kind="primary"],
.stButton > button[kind="primary"],
[data-testid="stDownloadButton"] > button,
[data-testid="stDownloadButton"] a,
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #FF7A30 0%, #FF6817 100%) !important;
    border: 1px solid #E65100 !important;
    border-radius: 8px !important;
    box-shadow: 0 2px 8px rgba(255, 122, 48, 0.28) !important;
    padding: 8px 18px !important;
    min-height: 42px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 140ms ease !important;
    cursor: pointer !important;
}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover,
[data-testid="stDownloadButton"] > button:hover,
[data-testid="stDownloadButton"] a:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #FF8F4D 0%, #FF7A30 100%) !important;
    box-shadow: 0 4px 14px rgba(255, 122, 48, 0.4) !important;
    transform: translateY(-1px);
}

button[kind="primary"]:active,
[data-testid="stDownloadButton"] > button:active,
[data-testid="stFormSubmitButton"] > button:active {
    transform: scale(0.98) !important;
}

/* 2. Secondary & Standard Buttons: Elevated White Cards */
.stButton > button,
button[kind="secondary"],
[data-testid="stButton"] > button {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    padding: 8px 16px !important;
    min-height: 40px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 130ms ease !important;
    cursor: pointer !important;
}

.stButton > button:hover,
button[kind="secondary"]:hover,
[data-testid="stButton"] > button:hover {
    border-color: #FF7A30 !important;
    background-color: #FFF7ED !important;
    background: #FFF7ED !important;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.08) !important;
    transform: translateY(-1px);
}

.stButton > button:active,
button[kind="secondary"]:active,
[data-testid="stButton"] > button:active {
    transform: scale(0.98) !important;
}

/* 3. Strip nested inner borders, backgrounds, and margins from button children */
button[kind="primary"] *,
.stButton > button[kind="primary"] *,
[data-testid="stDownloadButton"] > button *,
[data-testid="stDownloadButton"] a *,
[data-testid="stFormSubmitButton"] > button * {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 0 !important;
    margin: 0 !important;
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-family: var(--font-sans) !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    letter-spacing: -0.01em !important;
    line-height: 1.3 !important;
}

.stButton > button *,
button[kind="secondary"] *,
[data-testid="stButton"] > button * {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
    padding: 0 !important;
    margin: 0 !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-family: var(--font-sans) !important;
    font-weight: 600 !important;
    font-size: 0.86rem !important;
    letter-spacing: -0.01em !important;
    line-height: 1.3 !important;
}

.stButton > button:hover *,
button[kind="secondary"]:hover *,
[data-testid="stButton"] > button:hover * {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
}

/* ========================================================================== */
/* UNIVERSAL FORM CONTROLS: ELEVATED WHITE CARDS & ZERO TRANSPARENCY          */
/* ========================================================================== */

/* Text inputs, Textareas, Selectboxes, Multiselects */
[data-baseweb="input"],
[data-baseweb="input"] > div,
[data-baseweb="base-input"],
[data-baseweb="textarea"],
[data-baseweb="textarea"] > div,
[data-baseweb="textarea"] textarea,
[data-baseweb="select"],
[data-baseweb="select"] > div,
[data-baseweb="select"] div[role="combobox"],
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[role="combobox"],
[data-testid="stMultiSelect"] div[role="combobox"],
.stTextArea textarea,
.stTextInput input,
input,
textarea {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    opacity: 1 !important;
}

/* Focus highlighting in signature Papaya Orange */
[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within,
[data-baseweb="select"]:focus-within,
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
input:focus,
textarea:focus {
    border-color: #FF7A30 !important;
    box-shadow: 0 0 0 2px rgba(255, 122, 48, 0.22), 0 1px 3px rgba(0, 0, 0, 0.06) !important;
}

/* Universal Containers & Form Wrappers: Elevated Solid White Structure */
[data-testid="stForm"],
[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
}

[data-testid="stForm"] {
    padding: 16px !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
}

/* Universal Tables: Elevated Solid White Structure (NO grid bleed through text) */
table,
[data-testid="stMarkdownContainer"] table {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04) !important;
    width: 100% !important;
    margin: 12px 0 !important;
}

th,
[data-testid="stMarkdownContainer"] th {
    background-color: #F8FAFC !important;
    background: #F8FAFC !important;
    color: #0F172A !important;
    font-family: var(--font-sans) !important;
    font-size: 0.86rem !important;
    font-weight: 700 !important;
    border-bottom: 2px solid #E2E8F0 !important;
    border-right: 1px solid #F1F5F9 !important;
    padding: 10px 14px !important;
    text-align: left !important;
}

td,
[data-testid="stMarkdownContainer"] td {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    color: #1E293B !important;
    font-size: 0.86rem !important;
    border-bottom: 1px solid #F1F5F9 !important;
    border-right: 1px solid #F1F5F9 !important;
    padding: 10px 14px !important;
}

tr:last-child td {
    border-bottom: none !important;
}

th:last-child, td:last-child {
    border-right: none !important;
}

tr:hover td {
    background-color: #FBFBFC !important;
}

/* Input labels */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label,
label[data-testid="stWidgetLabel"] {
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
}

/* Placeholders: Highly legible slate gray */
::placeholder,
::-webkit-input-placeholder,
::-moz-placeholder,
:-ms-input-placeholder,
textarea::placeholder,
input::placeholder {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
    opacity: 1 !important;
}

/* Form Helper & Submission Instructions */
[data-testid="InputInstructions"] {
    color: #64748B !important;
    -webkit-text-fill-color: #64748B !important;
}

/* Multiselect Tags (Selected Pills) */
[data-baseweb="tag"] {
    background-color: #FFF7ED !important;
    border: 1px solid rgba(255, 122, 48, 0.45) !important;
    border-radius: 4px !important;
    color: #C2410C !important;
}

[data-baseweb="tag"] span,
[data-baseweb="tag"] div,
[data-baseweb="tag"] * {
    color: #C2410C !important;
    -webkit-text-fill-color: #C2410C !important;
    font-weight: 700 !important;
    background: transparent !important;
}

[data-baseweb="tag"] svg {
    fill: #C2410C !important;
}

[data-baseweb="select"] svg {
    fill: #64748B !important;
}

/* Dropdown popover list & option items */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"],
li[role="option"] {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
}

li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background-color: #FFF7ED !important;
    color: #C2410C !important;
    -webkit-text-fill-color: #C2410C !important;
}

/* Disabled textareas (Report Viewer) */
[data-baseweb="textarea"] textarea:disabled,
textarea:disabled {
    background-color: #FAFAFA !important;
    color: #0F172A !important;
    -webkit-text-fill-color: #0F172A !important;
    opacity: 1 !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
    font-family: var(--font-mono) !important;
    font-size: 0.84rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}

/* Chat Messages: Elevated White Cards */
[data-testid="stChatMessage"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 12px 14px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}

[data-testid="stChatMessage"] * {
    color: #0F172A !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    color: #1E293B !important;
    line-height: 1.6 !important;
}

/* Expanders: Elevated White Cards */
[data-testid="stExpander"] {
    background: #FFFFFF !important;
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    color: #0F172A !important;
}

[data-testid="stExpander"] * {
    color: #0F172A !important;
}

[data-testid="stExpander"]:hover {
    border-color: var(--border-medium) !important;
}

/* Timeline Custom Connected Flow Elements */
.timeline-track-item {
    position: relative;
    padding-left: 28px;
    margin-bottom: 20px;
    border-left: 2px solid #CBD5E1;
}

.timeline-track-item::before {
    content: '';
    position: absolute;
    left: -7px;
    top: 6px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #FFFFFF;
    border: 2px solid #0F172A;
    box-shadow: 0 0 4px rgba(0, 0, 0, 0.15);
}

.timeline-track-item.critical::before {
    border-color: #EF4444;
    box-shadow: 0 0 8px rgba(239, 68, 68, 0.4);
}

.timeline-track-item.discrepancy::before {
    border-color: #F59E0B;
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
}

.timeline-track-item.breakthrough::before {
    border-color: #0284C7;
    box-shadow: 0 0 8px rgba(2, 132, 199, 0.4);
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: #F1F5F9;
}
::-webkit-scrollbar-thumb {
    background: #CBD5E1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: #94A3B8;
}

/* Subtle Hairline Dividers */
hr {
    border-color: var(--border-hairline) !important;
    margin: 1.4rem 0 !important;
}

/* Forensic Copilot Right Panel */
.copilot-panel {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 3px solid #FF7A30;
    border-radius: 10px;
    padding: 14px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}
.copilot-msg-user {
    background: #F1F5F9;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 10px;
    font-size: 0.88rem;
    color: #0F172A !important;
}
.copilot-msg-user * {
    color: #0F172A !important;
}
.copilot-msg-assistant {
    background: #FFF7ED;
    border: 1px solid rgba(255, 122, 48, 0.25);
    border-left: 3px solid #FF7A30;
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 12px;
    font-size: 0.88rem;
    color: #0F172A !important;
    line-height: 1.55;
}
.copilot-msg-assistant * {
    color: #0F172A !important;
}
</style>
"""
st.markdown(DESIGN_CSS, unsafe_allow_html=True)

# Minimalistic Fancy Startup Loading Screen (Dissolves into Workspace)
if "app_loaded" not in st.session_state:
    st.session_state.app_loaded = True
    render_html("""
    <div id="startup-loader">
        <div class="loader-content">
            <div class="loader-badge">CASE PO-88421</div>
            <div class="loader-title" style="display: inline-flex; align-items: baseline; justify-content: center; font-size: 2.8rem; letter-spacing: -0.05em; margin: 4px 0 8px 0;">
                <span style="font-weight: 800; font-style: normal; color: #0F172A;">E</span><span style="font-weight: 900; font-style: italic; color: #FF7A30; margin: 0 1px; transform: skewX(-6deg);">2</span><span style="font-weight: 800; font-style: normal; color: #0F172A;">D</span><span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #FF7A30; margin-left: 3px; margin-bottom: 5px;"></span>
            </div>
            <div class="loader-sub">Disputed Shipment Analysis</div>
            <div class="loader-bar-container">
                <div class="loader-bar"></div>
            </div>
            <div class="loader-status">Loading simulator...</div>
        </div>
    </div>
    """)

# Pure CSS Scroll-Driven Animations handle dynamic scroll reveal natively

# Initialize Session State
def init_session_state():
    if "evidence_register" not in st.session_state:
        st.session_state.evidence_register = load_initial_evidence_register()
    if "release_history" not in st.session_state:
        st.session_state.release_history = []
    if "attempt_history" not in st.session_state:
        st.session_state.attempt_history = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "selected_timeline_idx" not in st.session_state:
        st.session_state.selected_timeline_idx = 0
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [
            {
                "role": "assistant",
                "content": "Ask questions about case evidence, timeline events, vault records, or findings."
            }
        ]

init_session_state()

# Sidebar: Case Summary
with st.sidebar:
    render_html("""
    <div class="e2d-brand-badge">
        <div class="e2d-brand-logo">
            <span class="e2d-char">E</span><span class="e2d-two">2</span><span class="e2d-char">D</span><span class="e2d-dot"></span>
        </div>
        <div class="e2d-case-label">Case PO-88421</div>
    </div>
    """)
    
    st.divider()
    unlocked_hidden = len(st.session_state.release_history)
    total_evidence = len(st.session_state.evidence_register)
    attempts_count = len(st.session_state.attempt_history)
    
    render_html(f"""
    <div class="space-card" style="padding: 14px 16px; margin: 4px 0 14px 0;">
        <div style="font-family: var(--font-mono); font-size: 0.72rem; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: #475569; margin-bottom: 12px;">Case Parameters</div>
        <div style="display: flex; flex-direction: column; gap: 8px; font-size: 0.86rem; color: #0F172A;">
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">PO Reference:</span> <code>PO-88421</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Contract Value:</span> <code>INR 18,00,000</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Target Item:</span> <code>IC-902</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Ordered:</span> <code>500 Units (10 Ctn)</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Verified Inward:</span> <code>350 Units (7 Ctn)</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Disputed Shortfall:</span> <code>150 Units</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Active Documents:</span> <code>{total_evidence}</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Vault Records:</span> <code>{unlocked_hidden} / 3</code></div>
            <div style="display: flex; justify-content: space-between; align-items: center;"><span style="color: #64748B;">Determinations:</span> <code>{attempts_count}</code></div>
        </div>
    </div>
    """)
    if st.button("Reset Workspace", use_container_width=True):
        st.session_state.evidence_register = load_initial_evidence_register()
        st.session_state.release_history = []
        st.session_state.attempt_history = []
        st.session_state.chat_history = []
        st.session_state.selected_timeline_idx = 0
        st.session_state.pop("latest_evaluation", None)
        st.rerun()

# Main Header
st.title("Evidence to Decision Simulator")
render_html("""
<div style="display: flex; gap: 10px; align-items: center; margin-bottom: 14px; flex-wrap: wrap;">
    <span class="badge badge-papaya">Case PO-88421</span>
    <span class="badge badge-red">Disputed: 150 Units (INR 5,40,000)</span>
</div>
""")

col_workspace, col_copilot = st.columns([1.95, 1.05], gap="large")

with col_workspace:
    # Navigation Tabs
    tab_problem, tab_timeline, tab_evidence, tab_conflicts, tab_assistant, tab_hidden, tab_decision, tab_report = st.tabs([
        "Case Brief",
        "Timeline",
        "Evidence Register",
        "Contradictions",
        "Inquiry",
        "Vault",
        "Determination",
        "Report (.txt)"
    ])

    # ==============================================================================
    # TAB 1: CASE BRIEF
    # ==============================================================================
    with tab_problem:
        st.markdown("### Case Brief")
        st.caption("Commercial dispute summary, contract parameters, and consignment reconciliation.")

        # Financial & Commercial Exposure Metric Cards
        render_html("""
        <div class="kpi-grid">
            <div class="kpi-card space-card">
                <div class="kpi-label">Contract Quantity</div>
                <div class="kpi-value">500 Units</div>
                <div class="kpi-badge kpi-badge-verified">
                    <span class="kpi-badge-icon">✓</span> 10 Cartons Ordered
                </div>
            </div>
            <div class="kpi-card space-card">
                <div class="kpi-label">Contract Value</div>
                <div class="kpi-value">INR 18,00,000</div>
                <div class="kpi-badge kpi-badge-neutral">
                    @ INR 3,600 / Unit
                </div>
            </div>
            <div class="kpi-card space-card">
                <div class="kpi-label">Verified Inward</div>
                <div class="kpi-value">350 Units</div>
                <div class="kpi-badge kpi-badge-deficit">
                    <span class="kpi-badge-icon">✕</span> 150 Units Shortfall
                </div>
            </div>
            <div class="kpi-card space-card">
                <div class="kpi-label">Disputed Amount</div>
                <div class="kpi-value">INR 5,40,000</div>
                <div class="kpi-badge kpi-badge-deficit">
                    <span class="kpi-badge-icon">✕</span> 3 Cartons Missing
                </div>
            </div>
        </div>
        """)

        # Executive Summary
        render_html("""
        <div class="space-card" style="border-left: 3px solid #FF7A30;">
            <h4 style="margin: 0 0 10px 0; color: #0F172A; font-size: 1.05rem; font-weight: 700;">Executive Summary</h4>
            <p style="margin: 0 0 10px 0; color: #1E293B; font-size: 0.95rem; line-height: 1.65;">
                Buyer <strong>Zenith Electronics Ltd.</strong> (Pune) issued Purchase Order <strong>PO-88421</strong> for 500 units of Microcontroller IC-902 to supplier <strong>Apex Microtech Pvt. Ltd.</strong> (Bangalore) for <strong>INR 18,00,000</strong> under <strong>DDP Warehouse 1 (Pune)</strong> terms, with payment maturing only upon verified inward receipt.
            </p>
            <p style="margin: 0 0 10px 0; color: #1E293B; font-size: 0.95rem; line-height: 1.65;">
                Supplier Apex generated Invoice <code>DISP-6619</code> asserting all 10 cartons (40.0 kg) were handed over to logistics carrier <strong>SwiftLogix Express</strong> under Waybill <code>SLX-904821</code>, demanding full payment based on public tracking marked 'DELIVERED'.
            </p>
            <p style="margin: 0; color: #1E293B; font-size: 0.95rem; line-height: 1.65;">
                Upon physical receipt at Zenith Warehouse 1 (GRN-2026-0412), storekeepers verified only <strong>7 cartons (350 units)</strong>. Three cartons (#8, #9, and #10, containing 150 units worth INR 5,40,000) are missing. Carrier tracking reflects only an unverified gate signature at an unauthorized secondary annex.
            </p>
        </div>
        """)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Consignment Reconciliation Table
        st.markdown("#### Consignment Reconciliation")
        st.markdown("""
        | Chain Stage | Declared / Expected | Verified / Measured | Variance / Finding |
        | :--- | :--- | :--- | :--- |
        | **Purchase Order (PO-88421)** | 500 Units (10 Cartons, 40 kg) | — | Contract baseline DDP Bhosari Pune |
        | **Supplier Dispatch (DISP-6619)** | 500 Units (10 Cartons, 40 kg) | Unverified (Shipper count) | No certified scale ticket at origin |
        | **Pune Transit Hub Scale** | 40.0 kg Declared | 28.0 kg Scale Weight | **✕ -12.0 kg (-3 Cartons)** prior to Pune |
        | **Carrier Drop (Secondary Annex)** | Manifest marked 'DELIVERED' | Gate Guard R. Sharma signature | No carton intake verification |
        | **Warehouse Receipt (GRN-2026-0412)** | 500 Units Expected | 350 Units (7 Cartons, 28.1 kg) | **✕ Deficit: 150 Units (INR 5,40,000)** |
        """)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Two Columns: Discrepancies vs Objectives
        col_disc, col_obj = st.columns(2, gap="medium")
        with col_disc:
            render_html("""
            <div class="space-card" style="height: 100%;">
                <h4 style="margin: 0 0 10px 0; color: #0F172A; font-size: 0.98rem; font-weight: 700;">Key Discrepancies</h4>
                <ul style="padding-left: 18px; margin: 0; font-size: 0.88rem; line-height: 1.65; color: #334155;">
                    <li><strong style="color: #0F172A;">Transit Scale Deficit:</strong> SwiftLogix automated inward scale at Pune recorded 28.0 kg vs declared 40.0 kg (-12.0 kg). This proves the 3 missing cartons were absent before arrival in Pune.</li>
                    <li><strong style="color: #0F172A;">Spoofed Address Redirection:</strong> An unauthorized email from <code>operations-dispatch@apex-orders-update.com</code> (external spoofed domain) diverted delivery to an unstaffed secondary annex citing fictitious roof repairs.</li>
                    <li><strong style="color: #0F172A;">Unverified Gate Delivery:</strong> Tracking portal showed 'DELIVERED', but the signature was merely that of an annex gate security guard with zero carton intake count.</li>
                </ul>
            </div>
            """)
        with col_obj:
            render_html("""
            <div class="space-card" style="height: 100%;">
                <h4 style="margin: 0 0 10px 0; color: #0F172A; font-size: 0.98rem; font-weight: 700;">Investigation Objectives</h4>
                <ul style="padding-left: 18px; margin: 0; font-size: 0.88rem; line-height: 1.65; color: #334155;">
                    <li><strong style="color: #0F172A;">Pinpoint Loss Location:</strong> Determine whether the 150 units were withheld at supplier origin or lost during courier transit.</li>
                    <li><strong style="color: #0F172A;">Assess DDP Terms:</strong> Under DDP terms, supplier bears transit risk until verified delivery at the contracted destination.</li>
                    <li><strong style="color: #0F172A;">Commercial Remedy:</strong> Substantiate Zenith's legal entitlement to payment withholding and an immediate credit note of INR 5,40,000.</li>
                </ul>
            </div>
            """)

    # ==============================================================================
    # TAB 2: CHRONOLOGICAL SEQUENCE (TIMELINE RECONSTRUCTION)
    # ==============================================================================
    with tab_timeline:
        timeline = build_timeline(st.session_state.evidence_register)
        total_events = len(timeline)

        if st.session_state.selected_timeline_idx >= total_events:
            st.session_state.selected_timeline_idx = 0

        st.markdown("### Chronological Sequence & Chain-of-Custody Reconstruction")
        st.caption("Trace the sequence of events across time, custody locations, certified weigh-ins, and signatories before reviewing claims.")

        render_html(f"""
        <div class="kpi-grid">
            <div class="kpi-card space-card">
                <div class="kpi-label">Timeline Events</div>
                <div class="kpi-value">{total_events} Events</div>
                <div class="kpi-badge kpi-badge-neutral">
                    Chronological Sequence
                </div>
            </div>
            <div class="kpi-card space-card">
                <div class="kpi-label">Critical Breakpoint</div>
                <div class="kpi-value">Oct 13 • 08:30 AM</div>
                <div class="kpi-badge kpi-badge-deficit">
                    <span class="kpi-badge-icon">✕</span> Pune Hub -12 kg Variance
                </div>
            </div>
            <div class="kpi-card space-card">
                <div class="kpi-label">Custody Locations</div>
                <div class="kpi-value">5 Handover Points</div>
                <div class="kpi-badge kpi-badge-neutral">
                    Bangalore → Pune → Annex
                </div>
            </div>
            <div class="kpi-card space-card">
                <div class="kpi-label">Consignment Deficit</div>
                <div class="kpi-value">-150 Units</div>
                <div class="kpi-badge kpi-badge-deficit">
                    <span class="kpi-badge-icon">✕</span> 3 Cartons Undelivered
                </div>
            </div>
        </div>
        """)

        st.markdown("#### Sequence Scrubber")
        col_scrub_nav, col_filter = st.columns([3, 2])

        with col_filter:
            entity_filter = st.selectbox(
                "Filter Events by Entity:",
                ["All Custodians & Records", "Zenith Electronics (Buyer)", "Apex Microtech (Supplier)", "SwiftLogix Express (Carrier)", "Secondary Annex Security", "Confidential Audit Disclosures"]
            )

        filtered_indices = []
        for idx, ev in enumerate(timeline):
            party_str = ev.get("party", "")
            eid_str = ev.get("id", "")
            if entity_filter == "All Custodians & Records":
                filtered_indices.append(idx)
            elif entity_filter == "Zenith Electronics (Buyer)" and "Zenith" in party_str:
                filtered_indices.append(idx)
            elif entity_filter == "Apex Microtech (Supplier)" and "Apex" in party_str:
                filtered_indices.append(idx)
            elif entity_filter == "SwiftLogix Express (Carrier)" and "SwiftLogix" in party_str:
                filtered_indices.append(idx)
            elif entity_filter == "Secondary Annex Security" and ("Annex" in party_str or "Security" in party_str):
                filtered_indices.append(idx)
            elif entity_filter == "Confidential Audit Disclosures" and eid_str.startswith("HID-"):
                filtered_indices.append(idx)

        if not filtered_indices:
            filtered_indices = list(range(total_events))

        with col_scrub_nav:
            curr_idx = st.session_state.selected_timeline_idx
            col_prev, col_num, col_next = st.columns([1, 2, 1])
            with col_prev:
                if st.button("← Previous", use_container_width=True, disabled=(curr_idx <= 0)):
                    st.session_state.selected_timeline_idx = max(0, curr_idx - 1)
                    st.rerun()
            with col_num:
                active_event_label = f"Event {curr_idx + 1} of {total_events}: {timeline[curr_idx]['id']}"
                render_html(f"<div style='text-align: center; font-weight: 700; font-size: 0.92rem; color: #0F172A; padding-top: 6px;'>{active_event_label}</div>")
            with col_next:
                if st.button("Next →", use_container_width=True, disabled=(curr_idx >= total_events - 1)):
                    st.session_state.selected_timeline_idx = min(total_events - 1, curr_idx + 1)
                    st.rerun()

        render_html("<div style='margin-bottom: 8px; font-size: 0.8rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;'>Direct Milestone Selector:</div>")
        pill_cols = st.columns(len(filtered_indices))
        for p_col, idx_val in zip(pill_cols, filtered_indices):
            item = timeline[idx_val]
            is_selected = (idx_val == st.session_state.selected_timeline_idx)
            btn_label = f"#{idx_val+1} {item['id']}"
            with p_col:
                if st.button(btn_label, key=f"pill_step_{idx_val}", type="primary" if is_selected else "secondary", use_container_width=True):
                    st.session_state.selected_timeline_idx = idx_val
                    st.rerun()

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        col_timeline_stream, col_event_inspector = st.columns([1, 1], gap="medium")

        with col_timeline_stream:
            st.markdown("#### Chronological Flow")
            for idx in filtered_indices:
                ev = timeline[idx]
                is_active = (idx == st.session_state.selected_timeline_idx)
                sev = ev.get("severity", "normal")

                if sev == "critical":
                    badge_html = '<span class="badge badge-red"><span style="font-weight:700;">✕</span> CRITICAL SHORTAGE</span>'
                    item_class = "timeline-track-item critical"
                elif sev == "anomaly":
                    badge_html = '<span class="badge badge-red"><span style="font-weight:700;">✕</span> SECURITY ANOMALY</span>'
                    item_class = "timeline-track-item critical"
                elif sev == "discrepancy":
                    badge_html = '<span class="badge badge-amber"><span style="font-weight:700;">✕</span> DISCREPANCY</span>'
                    item_class = "timeline-track-item discrepancy"
                elif sev == "breakthrough":
                    badge_html = '<span class="badge badge-blue"><span style="font-weight:700;">✓</span> BREAKTHROUGH DISCLOSURE</span>'
                    item_class = "timeline-track-item breakthrough"
                else:
                    badge_html = '<span class="badge badge-neutral">STANDARD</span>'
                    item_class = "timeline-track-item"

                active_border = "border: 2px solid #FF7A30; box-shadow: 0 0 10px rgba(255,122,48,0.22);" if is_active else "border: 1px solid #E2E8F0;"

                render_html(f"""
                <div class="{item_class}">
                    <div class="space-card" style="padding: 14px 18px; margin-bottom: 0px; {active_border}">
                        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 4px;">
                            <span style="font-family: var(--font-mono); font-weight: 700; color: #0F172A; font-size: 0.85rem;">
                                Step {idx+1} &bull; {ev['date']} {ev['time']} IST
                            </span>
                            {badge_html}
                        </div>
                        <div style="font-weight: 700; color: #0F172A; font-size: 0.98rem; margin-bottom: 4px;">
                            {ev.get('step_title', ev.get('type', 'Milestone'))}
                        </div>
                        <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; margin-bottom: 8px;">
                            {ev['party']} &bull; Ref: <code>{ev['id']}</code>
                        </div>
                        <p style="margin: 0; font-size: 0.88rem; color: #334155; line-height: 1.5;">
                            {ev['event']}
                        </p>
                    </div>
                </div>
                """)

                if st.button(f"Inspect Step {idx+1} ({ev['id']})", key=f"btn_inspect_{idx}", use_container_width=True):
                    st.session_state.selected_timeline_idx = idx
                    st.rerun()

                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        with col_event_inspector:
            active_ev = timeline[st.session_state.selected_timeline_idx]
            active_idx = st.session_state.selected_timeline_idx

            st.markdown(f"#### Event Details: Step {active_idx+1}")
            status_tag = active_ev.get("status_flag", "MILESTONE RECORD")
            if any(term in status_tag.upper() for term in ["DISCREPANCY", "ANOMALY", "SHORTFALL", "UNVERIFIED"]):
                formatted_status = f"✕ {status_tag}"
            elif any(term in status_tag.upper() for term in ["BASELINE", "CONFIRMATION", "RECEIPT", "VERIFIED", "BREAKTHROUGH"]):
                formatted_status = f"✓ {status_tag}"
            else:
                formatted_status = status_tag

            render_html(f"""
            <div class="space-card" style="border-top: 3px solid #FF7A30;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span class="badge badge-dark">STEP {active_idx+1} OF {total_events}</span>
                    <span class="badge badge-neutral">{active_ev.get('phase', 'Phase Analysis')}</span>
                </div>
                <h3 style="margin: 0 0 4px 0; color: #0F172A; font-size: 1.22rem; font-weight: 700;">
                    {active_ev.get('step_title', active_ev.get('type', 'Event Overview'))}
                </h3>
                <div style="font-family: var(--font-mono); font-size: 0.86rem; color: #64748B; margin-bottom: 14px;">
                    Timestamp: <strong>{active_ev['date']} at {active_ev['time']} IST</strong> &bull; Citation: <code>{active_ev['id']}</code>
                </div>

                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Custody Details</div>
                    <div style="font-size: 0.88rem; margin-bottom: 5px; color: #1E293B;"><strong>Primary Entity:</strong> <span style="color: #0F172A; font-weight: 600;">{active_ev.get('party', 'N/A')}</span></div>
                    <div style="font-size: 0.88rem; margin-bottom: 5px; color: #1E293B;"><strong>Counterparty:</strong> <span style="color: #0F172A; font-weight: 600;">{active_ev.get('counterparty', 'N/A')}</span></div>
                    <div style="font-size: 0.88rem; margin-bottom: 5px; color: #1E293B;"><strong>Facility Location:</strong> <span style="color: #0F172A; font-weight: 600;">{active_ev.get('location', 'N/A')}</span></div>
                    <div style="font-size: 0.88rem; color: #1E293B;"><strong>Signatory:</strong> <span style="color: #0F172A; font-weight: 600;">{active_ev.get('signatory', 'N/A')}</span></div>
                </div>

                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; font-weight: 700; margin-bottom: 8px;">Consignment Status</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.86rem; color: #1E293B;">
                        <div><strong>Declared Count:</strong> <br><span style="color: #334155;">{active_ev.get('declared_qty', 'N/A')}</span></div>
                        <div><strong>Verified Count:</strong> <br><span style="color: #0F172A; font-weight: 700;">{active_ev.get('verified_qty', 'N/A')}</span></div>
                        <div><strong>Scale Weight:</strong> <br><span style="color: #334155;">{active_ev.get('weight', 'N/A')}</span></div>
                        <div><strong>Status Flag:</strong> <br><span style="color: #DC2626; font-weight: 700;">{formatted_status}</span></div>
                    </div>
                </div>

                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Description</div>
                    <p class="editorial-narrative" style="margin: 0; font-size: 0.95rem; line-height: 1.6; color: #1E293B;">
                        {active_ev['event']}
                    </p>
                </div>

                <div style="background: #FFFBEB; border-left: 3px solid #F59E0B; padding: 12px 14px; border-radius: 4px; margin-bottom: 14px;">
                    <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #B45309; margin-bottom: 4px;">Discrepancy</div>
                    <div style="font-size: 0.87rem; color: #1E293B; line-height: 1.5;">
                        {active_ev.get('discrepancy', 'No discrepancy logged at this milestone.')}
                    </div>
                </div>

                <div style="background: #FFF7ED; border-left: 3px solid #FF7A30; padding: 12px 14px; border-radius: 4px; margin-bottom: 14px;">
                    <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: #C2410C; margin-bottom: 4px;">Commercial Implication</div>
                    <div style="font-size: 0.87rem; color: #1E293B; line-height: 1.5;">
                        {active_ev.get('implication', 'Governing commercial record for subsequent audit.')}
                    </div>
                </div>

                <div style="margin-top: 10px;">
                    <div style="font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; font-weight: 700; margin-bottom: 6px;">Source Excerpt</div>
                    <pre style="margin: 0; padding: 12px; font-size: 0.82rem; white-space: pre-wrap; background: #F8FAFC; border: 1px solid #CBD5E1; color: #0F172A;">{active_ev.get('doc_excerpt', active_ev['event'])}</pre>
                </div>
            </div>
            """)

        st.divider()

        with st.expander("Timeline Table", expanded=False):
            st.markdown("""
            | Step # | Date & Time (IST) | Ref ID | Entity / Custodian | Signatory | Declared Count | Verified Physical Count | Status Flag |
            | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
            """ + "\n".join([
                f"| **{i+1}** | `{ev['date']} {ev['time']}` | `{ev['id']}` | {ev['party']} | {ev.get('signatory', 'N/A')} | {ev.get('declared_qty', 'N/A')} | {ev.get('verified_qty', 'N/A')} | **{ev.get('status_flag', 'STANDARD')}** |"
                for i, ev in enumerate(timeline)
            ]))

    # ==============================================================================
    # TAB 3: EVIDENCE REGISTER
    # ==============================================================================
    with tab_evidence:
        st.markdown("### Evidence Register")
        st.caption("Registered case documents and extracted records.")

        register = st.session_state.evidence_register
        eids = list(register.keys())

        selected_id = st.selectbox("Select Evidence Record for Inspection:", eids)
        doc = register[selected_id]

        c1, c2 = st.columns([1, 2])
        with c1:
            render_html(f"""
            <div class="space-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <span style="font-weight: 700; color: #0F172A; font-size: 1.1rem; font-family: var(--font-mono);">{doc['id']}</span>
                    <span class="badge badge-neutral">{doc.get('status', 'Accessible')}</span>
                </div>
                <div style="font-size: 0.86rem; margin-bottom: 6px; color: #1E293B;"><strong>Type:</strong> <span style="color: #0F172A; font-weight: 600;">{doc['doc_type']}</span></div>
                <div style="font-size: 0.86rem; margin-bottom: 6px; color: #1E293B;"><strong>File:</strong> <code>{doc['filename']}</code></div>
                <div style="font-size: 0.86rem; margin-bottom: 6px; color: #1E293B;"><strong>Date:</strong> {doc.get('date', 'Unknown')}</div>
                <div style="font-size: 0.86rem; margin-bottom: 6px; color: #1E293B;"><strong>Originator:</strong> {doc.get('author', 'Unknown')}</div>
                <div style="font-size: 0.86rem; margin-bottom: 6px; color: #1E293B;"><strong>Parties:</strong> {doc.get('parties', 'Unknown')}</div>
                <div style="font-size: 0.86rem; margin-bottom: 12px; color: #1E293B;"><strong>Declared Qty:</strong> {doc.get('quantity_claimed', 'N/A')}</div>
                <div style="padding: 12px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; font-size: 0.85rem; color: #334155; line-height: 1.5;">
                    {doc.get('key_claim', '')}
                </div>
            </div>
            """)
        with c2:
            st.markdown("#### Document Text Extract")
            st.text_area(
                label="Extracted Text Content",
                value=doc.get("raw_text", ""),
                height=340,
                disabled=True,
                label_visibility="collapsed"
            )

        st.divider()
        with st.expander("Upload Supporting External Document"):
            uploaded_file = st.file_uploader("Upload business document (PDF, EML, TXT):", type=["pdf", "eml", "txt"])
            if uploaded_file:
                fname = uploaded_file.name
                if fname.endswith(".pdf"):
                    extracted = read_pdf(uploaded_file)
                elif fname.endswith(".eml"):
                    extracted = read_email(uploaded_file)
                else:
                    extracted = uploaded_file.read().decode("utf-8", errors="replace")
                st.success(f"File '{fname}' processed successfully.")
                st.text_area("Parsed Text Preview", extracted, height=140)
                custom_title = st.text_input("Document Reference Title:", value=fname.replace("_", " ").rsplit(".", 1)[0].title())
                if st.button("Register Document to Active Case", type="primary"):
                    ext_count = len([k for k in st.session_state.evidence_register if k.startswith("EVD-EXT")]) + 1
                    new_id = f"EVD-EXT-{ext_count:03d}"
                    st.session_state.evidence_register[new_id] = {
                        "id": new_id,
                        "filename": fname,
                        "doc_type": custom_title,
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "author": "External Inward Document",
                        "parties": "Third-Party Supporting Record",
                        "quantity_claimed": "Declared in Document",
                        "value_claimed": "Declared in Document",
                        "key_claim": f"Supplementary document uploaded for analysis: {fname}",
                        "raw_text": extracted,
                        "is_hidden": False,
                        "status": "External Supporting Evidence"
                    }
                    st.success(f"Document registered as '{new_id}' in active workspace.")
                    st.rerun()

    # ==============================================================================
    # TAB 4: CONTRADICTIONS MATRIX
    # ==============================================================================
    with tab_conflicts:
        st.markdown("### Contradictions & Discrepancies")
        st.caption("Discrepancies identified across active case records.")

        conflicts = detect_conflicts(st.session_state.evidence_register)

        for idx, c in enumerate(conflicts, start=1):
            is_resolved = "RESOLVED" in c["title"]
            badge_class = "badge-green" if is_resolved else "badge-red"
            status_label = "Resolved by Audit" if is_resolved else "Active Contradiction"

            with st.expander(f"Conflict {idx}: {c['title']} [{', '.join(c['evidence_ids'])}]", expanded=not is_resolved):
                render_html(f"""
                <div style="margin-bottom: 12px;">
                    <span class="badge {badge_class}">{status_label}</span>
                    <span style="font-size: 0.85rem; color: #94A3B8; margin-left: 8px;">Involved Records: {c['sources']}</span>
                </div>
                """)
                col_x, col_y = st.columns(2)
                col_x.markdown(f"**Assertion A:**\n> {c['claim_a']}")
                col_y.markdown(f"**Assertion B:**\n> {c['claim_b']}")
                st.markdown(f"**Conflict:** {c['why_conflicts']}")
                st.markdown(f"**Uncertainty:** {c['uncertainty']}")
                st.info(f"Resolution Path: {c['resolution_path']}")

    # ==============================================================================
    # TAB 5: CASE INQUIRY (AI ASSISTANT)
    # ==============================================================================
    with tab_assistant:
        st.markdown("### Case Inquiry")
        st.caption("Query registered case documents and cross-examine evidence.")

        preset_q = st.selectbox(
            "Sample Questions:",
            [
                "Select a question or type below...",
                "What do the records prove about whether all 500 units were delivered?",
                "Does the courier delivery tracking prove that all 500 units arrived?",
                "What discrepancies exist between the supplier dispatch note and warehouse GRN?",
                "What is suspicious about the address-change email?",
                "What evidence is missing before a reliable final decision can be made?"
            ]
        )

        user_query = st.text_area(
            "Question:",
            value="" if preset_q.startswith("Select") else preset_q,
            height=90,
            placeholder="Enter specific factual questions regarding dates, quantities, carriers, or authorizations..."
        )

        if st.button("Run Query", type="primary"):
            if not user_query.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Analyzing records..."):
                    answer = ask_investigation_assistant(
                        user_query,
                        st.session_state.evidence_register
                    )
                    st.session_state.chat_history.append({"query": user_query, "answer": answer})

        if st.session_state.chat_history:
            st.divider()
            st.markdown("#### Prior Questions")
            for chat in reversed(st.session_state.chat_history):
                st.markdown(f"**Inquiry:** *{chat['query']}*")
                st.markdown(chat["answer"])
                st.divider()

    # ==============================================================================
    # TAB 6: CONFIDENTIAL VAULT (CONTROLLED RECORDS)
    # ==============================================================================
    with tab_hidden:
        st.markdown("### Confidential Records Vault")
        st.caption("Restricted records. Provide an investigative justification to unlock.")

        catalogue = get_hidden_catalogue()

        for hid, info in catalogue.items():
            is_unlocked = hid in st.session_state.evidence_register
            badge_html = '<span class="badge badge-green">UNLOCKED</span>' if is_unlocked else '<span class="badge badge-neutral">RESTRICTED</span>'

            render_html(f"""
            <div class="space-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #0F172A; font-size: 1rem; font-family: var(--font-mono);">{hid}: {info['title']}</span>
                    {badge_html}
                </div>
                <div style="font-size: 0.82rem; color: #64748B; margin-bottom: 6px;"><strong>Custodian:</strong> <span style="color: #0F172A;">{info['custodian']}</span></div>
                <p style="margin: 0 0 6px 0; font-size: 0.88rem; color: #334155;">{info['description']}</p>
                <div style="font-size: 0.84rem; color: #1E293B;"><strong>Relevance:</strong> {info['relevance']}</div>
            </div>
            """)

        st.markdown("#### Submit Access Request")
        with st.form("confidential_access_form"):
            req_id = st.selectbox("Select Confidential Record ID:", ["HID-001", "HID-002", "HID-003"])
            req_reason = st.text_area("Justification (min. 15 characters):", height=70, placeholder="Explain why accessing this record is critical to resolving the investigation...")
            req_question = st.text_input("Target Question (min. 10 characters):", placeholder="What specific ambiguity will this record resolve?")
            submit_req = st.form_submit_button("Submit Access Request", type="primary")

            if submit_req:
                success, msg = request_hidden_evidence(
                    req_id,
                    req_reason,
                    req_question,
                    st.session_state.evidence_register,
                    st.session_state.release_history
                )
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        if st.session_state.release_history:
            st.divider()
            st.markdown("#### Access Audit Log")
            for rel in st.session_state.release_history:
                render_html(f"""
                <div style="font-size: 0.86rem; color: #334155; margin-bottom: 6px;">
                    <span class="badge badge-green">APPROVED</span> <strong>{rel['evidence_id']}</strong> &bull; {rel['title']} &bull; <code>{rel['timestamp']}</code><br>
                    <em>Justification:</em> {rel['reason']}
                </div>
                """)

    # ==============================================================================
    # TAB 7: FORENSIC DETERMINATION (DECISION & EVALUATION)
    # ==============================================================================
    with tab_decision:
        st.markdown("### Forensic Determination")
        st.caption("Submit your findings and evidence citations for evaluation.")

        accessible_ids = list(st.session_state.evidence_register.keys())

        with st.form("decision_submission_form"):
            st.markdown("#### Assessment & Citations")
            conclusion = st.text_area(
                "Determination Summary:",
                height=120,
                placeholder="Summarize your findings, addressing the shortage, transit records, and supplier liability..."
            )

            col1, col2 = st.columns(2)
            with col1:
                supporting_ids = st.multiselect(
                    "Supporting Evidence:",
                    options=accessible_ids,
                    default=[eid for eid in ["EVD-001", "EVD-004"] if eid in accessible_ids]
                )
            with col2:
                counter_ids = st.multiselect(
                    "Counterevidence / Discrepant Records:",
                    options=accessible_ids,
                    default=[eid for eid in ["EVD-002", "EVD-003"] if eid in accessible_ids]
                )

            col3, col4 = st.columns(2)
            with col3:
                confidence = st.selectbox("Confidence Level:", ["Low", "Medium", "High"])
            with col4:
                uncertainties = st.text_input("Remaining Uncertainties:", placeholder="What elements remain unproven?")

            recommended_action = st.text_area(
                "Recommended Actions:",
                height=75,
                placeholder="Commercial, legal, or audit remedies..."
            )

            submit_decision = st.form_submit_button("Submit Determination", type="primary")

            if submit_decision:
                raw_sub = {
                    "conclusion": conclusion,
                    "supporting_evidence_ids": list(supporting_ids),
                    "counterevidence_ids": list(counter_ids),
                    "confidence_level": confidence,
                    "unresolved_uncertainties": uncertainties,
                    "recommended_action": recommended_action
                }

                is_valid, validation_errors, validated_data = validate_submission_inputs(
                    raw_sub,
                    st.session_state.evidence_register
                )

                if not is_valid:
                    for err in validation_errors:
                        st.error(f"Input Validation: {err}")
                else:
                    with st.spinner("Evaluating submission..."):
                        try:
                            eval_result = evaluate_decision_with_llm(
                                validated_data,
                                st.session_state.evidence_register
                            )
                            attempt = record_submission_attempt(
                                st.session_state.attempt_history,
                                validated_data,
                                eval_result,
                                st.session_state.evidence_register
                            )
                            st.session_state.latest_evaluation = attempt
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Live Gemini Evaluation Notice: {exc}")

        # Scorecard Display
        if "latest_evaluation" in st.session_state:
            latest = st.session_state.latest_evaluation
            st.divider()
            st.success("Determination evaluated. Your formal Investigation Report (.txt) is now generated and available in the Report tab.")
            st.markdown(f"### Scorecard: Attempt {latest['attempt_number']}")

            c_score1, c_score2 = st.columns([1, 2])
            with c_score1:
                total = latest['total_score']
                st.metric("Total Evaluation Score", f"{total} / 100")
                if total >= 80:
                    badge_desc = "High Quality Determination"
                    b_color = "badge-green"
                elif total >= 60:
                    badge_desc = "Satisfactory / Minor Revisions"
                    b_color = "badge-amber"
                else:
                    badge_desc = "Needs Revision"
                    b_color = "badge-red"
                render_html(f"<span class='badge {b_color}'>{badge_desc}</span>")

            with c_score2:
                st.markdown("#### Criterion Breakdown")
                crit_scores = latest["criterion_scores"]
                for crit_key, spec in RUBRIC_CRITERIA.items():
                    pts = crit_scores.get(crit_key, 0)
                    max_pts = spec["max_points"]
                    col_k, col_v = st.columns([3, 1])
                    col_k.write(spec["title"])
                    col_v.write(f"{pts} / {max_pts}")
                    st.progress(min(1.0, pts / max_pts))

            st.markdown("#### Qualitative Feedback")
            fb = latest["evaluation_feedback"]

            col_s, col_i = st.columns(2)
            with col_s:
                st.markdown("**Demonstrated Strengths:**")
                for s in fb.get("strengths", []):
                    st.write(f"- {s}")
            with col_i:
                st.markdown("**Areas for Revision:**")
                for imp in fb.get("improvements", []):
                    st.write(f"- {imp}")

            if fb.get("investigator_tip"):
                st.info(f"Tip: {fb['investigator_tip']}")

        # Revision Comparison
        if len(st.session_state.attempt_history) > 1:
            st.divider()
            st.markdown("### Revision History")
            history = st.session_state.attempt_history

            comp_cols = st.columns(len(history))
            for idx, att in enumerate(history):
                with comp_cols[idx]:
                    st.markdown(f"#### Attempt {att['attempt_number']}")
                    st.caption(f"{att['timestamp']}")
                    delta_val = f"{att['total_score'] - history[idx-1]['total_score']:+.1f} pts" if idx > 0 else None
                    st.metric("Score", f"{att['total_score']} / 100", delta=delta_val)
                    st.write(f"**Confidence:** {att['submission']['confidence_level']}")
                    st.write(f"**Citations:** {', '.join(att['submission']['valid_supporting_ids'])}")
                    with st.expander("Submitted Conclusion"):
                        st.write(att['submission']['conclusion'])

    # ==============================================================================
    # TAB 8: FINAL REPORT (DELIVERED AS PLAIN TEXT .TXT)
    # ==============================================================================
    with tab_report:
        st.markdown("### Investigation Report")
        st.caption("Complete case report compiled from verified evidence, timeline events, and evaluated determination.")

        if not st.session_state.attempt_history:
            render_html("""
            <div class="space-card" style="border-left: 3px solid #FF7A30; padding: 22px;">
                <h4 style="margin: 0 0 8px 0; color: #0F172A; font-size: 1.05rem; font-weight: 700;">Determination Required</h4>
                <p style="margin: 0 0 14px 0; color: #334155; font-size: 0.92rem; line-height: 1.6;">
                    The formal audit report is generated once an investigative determination has been submitted and evaluated. Please complete your analysis and submit your findings in the <strong>Determination</strong> tab.
                </p>
                <div style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <span class="badge badge-amber">STATUS: AWAITING DETERMINATION</span>
                    <span class="badge badge-neutral">EXPORT FORMAT: PLAIN TEXT (.TXT)</span>
                </div>
            </div>
            """)
        else:
            latest = st.session_state.attempt_history[-1]
            render_html(f"""
            <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 12px; flex-wrap: wrap;">
                <span class="badge badge-green">REPORT READY</span>
                <span class="badge badge-papaya">Attempt #{latest['attempt_number']}</span>
                <span class="badge badge-dark">Evaluation Score: {latest['total_score']} / 100</span>
            </div>
            """)

            # Generate Plain Text Report (.txt)
            report_txt = generate_investigation_report_txt(
                case_summary="PO-88421 Missing Consignment Forensic Audit",
                accessible_register=st.session_state.evidence_register,
                timeline=build_timeline(st.session_state.evidence_register),
                conflicts=detect_conflicts(st.session_state.evidence_register),
                release_history=st.session_state.release_history,
                attempt_history=st.session_state.attempt_history
            )

            st.download_button(
                label="Download Report (.txt)",
                data=report_txt,
                file_name="investigation_report_PO88421.txt",
                mime="text/plain",
                type="primary",
                use_container_width=True
            )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            st.markdown("#### Report Preview")
            st.text_area(
                label="Report Preview",
                value=report_txt,
                height=620,
                disabled=True,
                label_visibility="collapsed"
            )

# ==============================================================================
# RIGHT SIDE: UNIVERSAL CONTEXT-AWARE FORENSIC COPILOT
# ==============================================================================
with col_copilot:
    with st.container(border=True):
        render_html("""
        <div style="border-left: 4px solid #FF7A30; padding-left: 10px; margin-bottom: 8px;">
            <span style="font-family: var(--font-sans); font-size: 1.12rem; font-weight: 700; color: #0F172A;">
                Copilot
            </span>
        </div>
        """)
        
        # Quick Action Prompt Buttons
        st.caption("Quick Inquiries:")
        qc1, qc2 = st.columns(2)
        with qc1:
            if st.button("Shortage Summary", key="qp_shortage", use_container_width=True):
                st.session_state.pending_copilot_query = "Explain the 150-unit shortage and commercial baseline under contract PO-88421."
                st.rerun()
            if st.button("Vault Access", key="qp_vault", use_container_width=True):
                st.session_state.pending_copilot_query = "How do I unlock confidential vault records in Tab 6 and what is required?"
                st.rerun()
        with qc2:
            if st.button("Weight Analysis", key="qp_weight", use_container_width=True):
                st.session_state.pending_copilot_query = "Analyze the weighbridge scale records and prove why the 12 kg drop matters."
                st.rerun()
            if st.button("Breach & Liability", key="qp_liability", use_container_width=True):
                st.session_state.pending_copilot_query = "Analyze the contractual breach under PO-88421, carrier custody under Waybill SLX-904821, and legal entitlement to the INR 5,40,000 credit note."
                st.rerun()

        # Handle pending query from quick action buttons
        if st.session_state.get("pending_copilot_query"):
            q = st.session_state.pop("pending_copilot_query")
            with st.spinner("Consulting Gemini..."):
                ans = ask_copilot(
                    q,
                    st.session_state.evidence_register,
                    st.session_state.release_history,
                    st.session_state.attempt_history,
                    st.session_state.get("latest_evaluation"),
                    st.session_state.copilot_messages
                )
                st.session_state.copilot_messages.append({"role": "user", "content": q})
                st.session_state.copilot_messages.append({"role": "assistant", "content": ans})
            st.rerun()

        # Chat messages history view
        with st.container(height=480):
            for msg in st.session_state.copilot_messages:
                if msg["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(f"**Investigator:** {msg['content']}")
                else:
                    with st.chat_message("assistant"):
                        st.markdown(msg["content"])

        # Chat input form
        with st.form(key="copilot_chat_form", clear_on_submit=True):
            user_text = st.text_input(
                "Ask Copilot:",
                placeholder="Ask anything about case facts, evidence, or site...",
                label_visibility="collapsed"
            )
            c_btn_send, c_btn_reset = st.columns([3, 1])
            submitted = c_btn_send.form_submit_button("Send", use_container_width=True)
            reset_chat = c_btn_reset.form_submit_button("Reset", use_container_width=True)

        if submitted and user_text.strip():
            with st.spinner("Consulting Gemini..."):
                ans = ask_copilot(
                    user_text.strip(),
                    st.session_state.evidence_register,
                    st.session_state.release_history,
                    st.session_state.attempt_history,
                    st.session_state.get("latest_evaluation"),
                    st.session_state.copilot_messages
                )
                st.session_state.copilot_messages.append({"role": "user", "content": user_text.strip()})
                st.session_state.copilot_messages.append({"role": "assistant", "content": ans})
            st.rerun()

        if reset_chat:
            st.session_state.copilot_messages = [
                {
                    "role": "assistant",
                    "content": "Ask questions about case evidence, timeline events, vault records, or findings."
                }
            ]
            st.rerun()

