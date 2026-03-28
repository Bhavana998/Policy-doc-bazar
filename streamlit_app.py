import streamlit as st
import pkg_resources

st.write([pkg.key for pkg in pkg_resources.working_set])

# your existing imports BELOW
from app.utils import extract_text_from_pdf, chunk_text
from app.retriever import store_documents
import streamlit as st
import os
import time

# Import backend functions directly (Bypassing FastAPI)
from app.utils import extract_text_from_pdf, chunk_text
from app.retriever import store_documents
from app.rag_pipeline import ask_rag, extract_key_clauses, summarize_policies

# ─── Configuration ───────────────────────────────────────────────────────────
# Color Palette
PRIMARY   = "#2563EB"
SECONDARY = "#7C3AED"
BG_LIGHT  = "#F9FAFB"
BG_DARK   = "#0F172A"
CARD_LIGHT = "#FFFFFF"
CARD_DARK  = "#1E293B"
TEXT_LIGHT = "#1E293B"
TEXT_DARK  = "#E2E8F0"
MUTED_LIGHT = "#64748B"
MUTED_DARK  = "#94A3B8"

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PolicyBazaar AI Analyst",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Session State Defaults ──────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "ask"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "uploaded_filename" not in st.session_state:
    st.session_state.uploaded_filename = None
if "clauses_data" not in st.session_state:
    st.session_state.clauses_data = None
if "summary_data" not in st.session_state:
    st.session_state.summary_data = None

dark = st.session_state.dark_mode
bg      = BG_DARK if dark else BG_LIGHT
card_bg = CARD_DARK if dark else CARD_LIGHT
text_c  = TEXT_DARK if dark else TEXT_LIGHT
muted_c = MUTED_DARK if dark else MUTED_LIGHT
border_c = "#334155" if dark else "#E2E8F0"
input_bg = "#1E293B" if dark else "#F1F5F9"
sidebar_bg = "#1E293B" if dark else CARD_LIGHT

# ─── Massive Custom CSS ─────────────────────────────────────────────────────
st.markdown(f"""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global Reset ── */
*, *::before, *::after {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    box-sizing: border-box;
}}

/* ── Root App Background ── */
.stApp, .main, [data-testid="stAppViewContainer"] {{
    background: {bg} !important;
}}
[data-testid="stHeader"] {{
    background: transparent !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {MUTED_LIGHT}; border-radius: 3px; }}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {sidebar_bg} !important;
    border-right: 1px solid {border_c} !important;
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    padding-top: 1rem;
}}

/* ── Hide default Streamlit elements ── */
#MainMenu, footer, header {{
    visibility: hidden;
}}

/* ── Typography ── */
h1, h2, h3, h4, h5, h6, p, span, div, label {{
    color: {text_c} !important;
}}

/* ── Streamlit Buttons (default) ── */
.stButton > button {{
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY}) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.02em !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 15px rgba(37, 99, 235, 0.25) !important;
}}
.stButton > button:hover {{
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 25px rgba(37, 99, 235, 0.35) !important;
}}
.stButton > button:active {{
    transform: translateY(0px) scale(0.98) !important;
}}

/* ── Text Input Styling ── */
.stTextInput > div > div > input {{
    background: {input_bg} !important;
    border: 2px solid {border_c} !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
    color: {text_c} !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: {PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.15) !important;
}}
.stTextInput label {{
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    color: {muted_c} !important;
}}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {{
    background: {input_bg} !important;
    border: 2px dashed {border_c} !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    transition: all 0.3s ease !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: {PRIMARY} !important;
    background: {"rgba(37,99,235,0.05)" if not dark else "rgba(37,99,235,0.1)"} !important;
}}
[data-testid="stFileUploader"] section {{
    padding: 0 !important;
}}
[data-testid="stFileUploader"] label {{
    font-weight: 600 !important;
    color: {muted_c} !important;
}}

/* ── Tabs (pill style) ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px !important;
    background: {input_bg} !important;
    padding: 6px !important;
    border-radius: 14px !important;
    border: 1px solid {border_c} !important;
}}
.stTabs [data-baseweb="tab"] {{
    height: auto !important;
    padding: 10px 20px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: {muted_c} !important;
    background: transparent !important;
    border-bottom: none !important;
    transition: all 0.25s ease !important;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY}) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
}}
.stTabs [data-baseweb="tab-border"] {{
    display: none !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    display: none !important;
}}

/* ── Spinner ── */
.stSpinner > div {{
    border-top-color: {PRIMARY} !important;
}}

/* ── Card Classes ── */
.glass-card {{
    background: {"rgba(30,41,59,0.7)" if dark else "rgba(255,255,255,0.75)"};
    backdrop-filter: blur(16px);
    border: 1px solid {"rgba(255,255,255,0.08)" if dark else "rgba(255,255,255,0.5)"};
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: 0 8px 32px rgba(0,0,0,{"0.25" if dark else "0.06"});
    margin-bottom: 1rem;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}}
.glass-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(0,0,0,{"0.3" if dark else "0.1"});
}}

.solid-card {{
    background: {card_bg};
    border: 1px solid {border_c};
    border-radius: 16px;
    padding: 1.75rem;
    box-shadow: 0 4px 20px rgba(0,0,0,{"0.2" if dark else "0.04"});
    margin-bottom: 1rem;
}}

/* ── Hero Section ── */
.hero-section {{
    text-align: center;
    padding: 2.5rem 1rem 1.5rem;
    animation: fadeInDown 0.8s ease-out;
}}
.hero-title {{
    font-size: 2.5rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem !important;
    line-height: 1.2 !important;
}}
.hero-subtitle {{
    font-size: 1.1rem !important;
    color: {muted_c} !important;
    font-weight: 400 !important;
    line-height: 1.6 !important;
    max-width: 600px;
    margin: 0 auto;
}}

/* ── Chat Bubbles ── */
.chat-container {{
    max-height: 500px;
    overflow-y: auto;
    padding: 1rem 0;
}}
.chat-bubble-user {{
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    color: white !important;
    padding: 1rem 1.25rem;
    border-radius: 16px 16px 4px 16px;
    margin: 0.75rem 0;
    max-width: 85%;
    margin-left: auto;
    font-size: 0.95rem;
    line-height: 1.5;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    animation: fadeInUp 0.4s ease-out;
}}
.chat-bubble-user * {{ color: white !important; -webkit-text-fill-color: white !important; }}

.chat-bubble-ai {{
    background: {input_bg};
    color: {text_c} !important;
    padding: 1rem 1.25rem;
    border-radius: 16px 16px 16px 4px;
    margin: 0.75rem 0;
    max-width: 85%;
    font-size: 0.95rem;
    line-height: 1.7;
    border: 1px solid {border_c};
    animation: fadeInUp 0.4s ease-out;
}}

/* ── Clause Cards ── */
.clause-card {{
    background: {card_bg};
    border-radius: 14px;
    padding: 1.5rem;
    margin: 0.75rem 0;
    border-left: 4px solid;
    box-shadow: 0 4px 16px rgba(0,0,0,{"0.15" if dark else "0.05"});
    transition: transform 0.25s ease;
}}
.clause-card:hover {{
    transform: translateX(4px);
}}
.clause-coverage {{ border-left-color: #10B981; }}
.clause-exclusion {{ border-left-color: #EF4444; }}
.clause-premium {{ border-left-color: #F59E0B; }}
.clause-label {{
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.5rem;
}}
.clause-label-green {{ color: #10B981 !important; -webkit-text-fill-color: #10B981 !important; }}
.clause-label-red {{ color: #EF4444 !important; -webkit-text-fill-color: #EF4444 !important; }}
.clause-label-amber {{ color: #F59E0B !important; -webkit-text-fill-color: #F59E0B !important; }}

/* ── Sidebar Branding ── */
.sidebar-brand {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 0.5rem;
    margin-bottom: 0.5rem;
}}
.sidebar-brand-icon {{
    width: 42px;
    height: 42px;
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}}
.sidebar-brand-text {{
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

.sidebar-divider {{
    height: 1px;
    background: {border_c};
    margin: 1rem 0;
}}

/* ── Stat Badge ── */
.stat-badge {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: {"rgba(37,99,235,0.12)" if dark else "rgba(37,99,235,0.08)"};
    color: {PRIMARY} !important;
    padding: 0.35rem 0.85rem;
    border-radius: 50px;
    font-size: 0.78rem;
    font-weight: 600;
}}

/* ── Top Navbar ── */
.top-navbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.5rem;
    background: {"rgba(30,41,59,0.6)" if dark else "rgba(255,255,255,0.7)"};
    backdrop-filter: blur(12px);
    border-bottom: 1px solid {border_c};
    border-radius: 0 0 16px 16px;
    margin: -1rem -1rem 1.5rem -1rem;
}}
.navbar-title {{
    font-weight: 700;
    font-size: 1rem;
    color: {text_c} !important;
}}
.navbar-avatar {{
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white !important;
    font-weight: 700;
    font-size: 0.85rem;
}}

/* ── Empty State ── */
.empty-state {{
    text-align: center;
    padding: 3rem 1rem;
    color: {muted_c} !important;
}}
.empty-state-icon {{
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
}}
.empty-state-text {{
    font-size: 1rem;
    font-weight: 500;
    color: {muted_c} !important;
}}

/* ── Tip Box ── */
.tip-box {{
    background: {"rgba(37,99,235,0.08)" if dark else "rgba(37,99,235,0.04)"};
    border: 1px solid {"rgba(37,99,235,0.2)" if dark else "rgba(37,99,235,0.12)"};
    border-radius: 12px;
    padding: 1rem;
    font-size: 0.85rem;
    color: {muted_c} !important;
    line-height: 1.6;
}}

/* ── Animations ── */
@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

.fade-in {{
    animation: fadeIn 0.6s ease-out;
}}
.fade-in-up {{
    animation: fadeInUp 0.5s ease-out;
}}

/* ── Upload Area ── */
.upload-zone {{
    text-align: center;
    padding: 2rem 1rem;
}}
.upload-icon {{
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    opacity: 0.7;
}}
.upload-text {{
    font-size: 0.95rem;
    font-weight: 500;
    color: {muted_c} !important;
}}
.upload-hint {{
    font-size: 0.8rem;
    color: {muted_c} !important;
    opacity: 0.7;
    margin-top: 0.25rem;
}}
.file-preview {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    background: {"rgba(16,185,129,0.08)" if dark else "rgba(16,185,129,0.06)"};
    border: 1px solid {"rgba(16,185,129,0.25)" if dark else "rgba(16,185,129,0.15)"};
    border-radius: 10px;
    margin-top: 0.75rem;
}}
.file-name {{
    font-weight: 600;
    font-size: 0.88rem;
    color: #10B981 !important;
    -webkit-text-fill-color: #10B981 !important;
}}

/* ── Metric Card ── */
.metric-card {{
    background: {card_bg};
    border: 1px solid {border_c};
    border-radius: 14px;
    padding: 1.25rem;
    text-align: center;
    transition: transform 0.2s ease;
}}
.metric-card:hover {{ transform: translateY(-2px); }}
.metric-value {{
    font-size: 1.75rem !important;
    font-weight: 800 !important;
    background: linear-gradient(135deg, {PRIMARY}, {SECONDARY});
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.metric-label {{
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: {muted_c} !important;
    -webkit-text-fill-color: {muted_c} !important;
    margin-top: 0.25rem;
}}

/* ── Section label ── */
.section-label {{
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {muted_c} !important;
    -webkit-text-fill-color: {muted_c} !important;
    margin-bottom: 0.75rem;
    padding-left: 0.25rem;
}}

/* ── Footer ── */
.footer {{
    text-align: center;
    padding: 2rem 0 1rem;
    font-size: 0.8rem;
    color: {muted_c} !important;
    opacity: 0.7;
}}
</style>
""", unsafe_allow_html=True)


# ─── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-icon">🛡️</div>
        <span class="sidebar-brand-text">PolicyBazaar AI</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # Document Upload Section
    st.markdown('<div class="section-label">📁 Document Upload</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="upload-zone">
        <div class="upload-icon">📄</div>
        <div class="upload-text">Drop your policy document</div>
        <div class="upload-hint">Supports PDF files</div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload PDF", type=['pdf'], label_visibility="collapsed")
    
    if uploaded_file:
        st.session_state.uploaded_filename = uploaded_file.name
        st.markdown(f"""
        <div class="file-preview">
            <span class="file-icon">📎</span>
            <span class="file-name">{uploaded_file.name}</span>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("🚀 Process Document", use_container_width=True):
        if uploaded_file:
            with st.spinner("Indexing document..."):
                os.makedirs("data", exist_ok=True)
                os.makedirs("vector_store", exist_ok=True)
                
                file_path = os.path.join("data", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                try:
                    text = extract_text_from_pdf(file_path)
                    if not text.strip():
                        st.error("Could not extract text from the PDF.")
                    else:
                        chunks = chunk_text(text, metadata={"source": uploaded_file.name})
                        store_documents(chunks)
                        
                        st.success(f"✅ **{uploaded_file.name}** indexed successfully!")
                        st.markdown(f'<div class="stat-badge">📦 {len(chunks)} chunks stored</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error indexing document: {e}")
        else:
            st.warning("⚠️ Please upload a file first.")
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # Dark Mode Toggle
    st.markdown('<div class="section-label">⚙️ Settings</div>', unsafe_allow_html=True)
    dark_toggle = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_toggle")
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="tip-box">
        💡 <strong>Pro Tip</strong><br/>
        Our AI can identify hidden clauses, coverage gaps, and ambiguous language across multi-page legal documents.
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN CONTENT ────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="top-navbar">
    <span class="navbar-title">🛡️ PolicyBazaar AI Dashboard</span>
    <div style="display: flex; align-items: center; gap: 1rem;">
        <div class="stat-badge">{"🌙 Dark" if dark else "☀️ Light"}</div>
        <div class="navbar-avatar">U</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-section">
    <div class="hero-title">Policy Document Intelligence</div>
    <div class="hero-subtitle">
        Gain instant clarity on your insurance coverage with RAG-powered deep analysis.
        Upload documents, ask questions, and extract critical insights in seconds.
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Stats
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-value">⚡</div><div class="metric-label">Instant AI Analysis</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-value">🔍</div><div class="metric-label">Clause Extraction</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-value">📄</div><div class="metric-label">Smart Summaries</div></div>', unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["💬  Ask AI Analyst", "🔍  Key Clauses", "📝  Document Summary"])

# ─── TAB 1: Chat with AI ────────────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 style="margin-top:0; font-weight:700;">💬 Ask AI Analyst</h3>
        <p style="font-size: 0.9rem; opacity: 0.7; margin-bottom: 0;">
            Ask any question about your policy coverage, limits, claims process, or exclusions.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="chat-bubble-user">🧑 {msg["content"]}</div>'
            else:
                chat_html += f'<div class="chat-bubble-ai">🤖 {msg["content"]}</div>'
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="empty-state fade-in">
            <div class="empty-state-icon">💭</div>
            <div class="empty-state-text">No conversations yet.<br/>Ask a question to get started!</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br/>", unsafe_allow_html=True)
    user_query = st.text_input("YOUR QUESTION", placeholder="e.g. Is there a waiting period for pre-existing diseases?", label_visibility="visible")
    
    if st.button("✨ Analyze with AI", key="analyze_btn", use_container_width=True):
        if user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            with st.spinner("🧠 AI is thinking..."):
                try:
                    # DIRECT METHOD CALL
                    answer = ask_rag(user_query)
                    st.session_state.chat_history.append({"role": "ai", "content": answer})
                    st.rerun()
                except Exception as e:
                    st.error(f"Error querying AI backend: {e}")
                    st.session_state.chat_history.pop()
        else:
            st.warning("⚠️ Please type a question first.")
    
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

# ─── TAB 2: Key Clauses ─────────────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 style="margin-top:0; font-weight:700;">🔍 Key Clause Extraction</h3>
        <p style="font-size: 0.9rem; opacity: 0.7; margin-bottom: 0;">
            Automatically extract Coverage, Exclusions, and Premium details from your indexed documents.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ Auto-Extract Clauses", key="extract_btn", use_container_width=True):
        with st.spinner("🔬 Scanning document for structured data..."):
            try:
                # DIRECT METHOD CALL
                data = extract_key_clauses()
                st.session_state.clauses_data = data
                st.rerun()
            except Exception as e:
                st.error(f"Error extracting clauses: {e}")
    
    if st.session_state.clauses_data:
        data = st.session_state.clauses_data
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="clause-card clause-coverage fade-in-up"><div class="clause-label clause-label-green">✅ Coverage</div><div style="font-size:0.92rem; line-height:1.7;">{data.get("Coverage", "N/A")}</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="clause-card clause-exclusion fade-in-up"><div class="clause-label clause-label-red">⚠️ Exclusions</div><div style="font-size:0.92rem; line-height:1.7;">{data.get("Exclusions", "N/A")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="clause-card clause-premium fade-in-up"><div class="clause-label clause-label-amber">💰 Premium & Deductibles</div><div style="font-size:0.92rem; line-height:1.7;">{data.get("Premium", "N/A")}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state fade-in"><div class="empty-state-icon">📋</div><div class="empty-state-text">No clauses extracted yet.<br/>Click the button above to begin.</div></div>', unsafe_allow_html=True)

# ─── TAB 3: Document Summary ────────────────────────────────────────────────
with tab3:
    st.markdown("""
    <div class="glass-card fade-in">
        <h3 style="margin-top:0; font-weight:700;">📝 Executive Summary</h3>
        <p style="font-size: 0.9rem; opacity: 0.7; margin-bottom: 0;">
            Generate a comprehensive executive summary of all indexed policy documents.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📄 Generate Summary", key="summary_btn", use_container_width=True):
        with st.spinner("📊 Synthesizing comprehensive summary..."):
            try:
                # DIRECT METHOD CALL
                summary = summarize_policies()
                st.session_state.summary_data = summary
                st.rerun()
            except Exception as e:
                st.error(f"Error summarizing document: {e}")
    
    if st.session_state.summary_data:
        st.markdown(f'<div class="solid-card fade-in-up" style="border-left: 4px solid #10B981;"><div class="clause-label clause-label-green">📖 Policy Summary</div><div style="font-size: 0.95rem; line-height: 1.8; margin-top: 0.5rem;">{st.session_state.summary_data}</div></div>', unsafe_allow_html=True)
        st.download_button("⬇️ Download Summary", st.session_state.summary_data, file_name="policy_summary.txt", use_container_width=True)
    else:
        st.markdown('<div class="empty-state fade-in"><div class="empty-state-icon">📝</div><div class="empty-state-text">No summary generated yet.<br/>Click the button above to create one.</div></div>', unsafe_allow_html=True)

st.markdown('<div class="footer">Powered by <strong>Antigravity RAG</strong> · Built for PolicyBazaar Document Analysis<br/><span style="opacity: 0.5; font-size: 0.75rem;">© 2026 PolicyBazaar AI. All rights reserved.</span></div>', unsafe_allow_html=True)
