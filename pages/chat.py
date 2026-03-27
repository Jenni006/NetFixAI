import streamlit as st
from src.agent import query_netfix, reset_conversation
from src.knowledge_base import save_to_kb, search_kb, get_all_kb
from src.runbook_generator import create_runbook_pdf
import os
from datetime import datetime

st.set_page_config(
    page_title="NetFix AI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── DARK BASE ───────────────────────────── */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main {
        background-color: #171717 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #ececec;
    }

    /* kill all streamlit chrome + page nav */
    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"],
    [data-testid="stSidebarNav"],
    [data-testid="stStatusWidget"] { display: none !important; }

    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* ── SIDEBAR ─────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: #0f0f0f !important;
        border-right: 1px solid #222 !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

    .sb-logo-row {
        display: flex; align-items: center; gap: 12px;
        padding: 20px 18px 16px;
        border-bottom: 1px solid #222;
    }
    .sb-logo {
        width: 36px; height: 36px; background: linear-gradient(135deg, #d4714a, #c96442);
        border-radius: 10px; display: flex; align-items: center;
        justify-content: center; font-size: 18px; flex-shrink: 0;
    }
    .sb-name  { font-size: 14px; font-weight: 600; color: #ececec; letter-spacing: -0.01em; }
    .sb-tag   { font-size: 11px; color: #555; margin-top: 2px; }

    .sb-sec {
        padding: 16px 18px 6px;
        font-size: 10px; font-weight: 600;
        letter-spacing: 0.08em; text-transform: uppercase; color: #444;
    }

    /* sidebar text input (search) */
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background: #1a1a1a !important;
        border: 1px solid #282828 !important;
        border-radius: 10px !important;
        color: #ececec !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        padding: 8px 14px !important;
    }
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder { color: #444 !important; }
    [data-testid="stSidebar"] .stTextInput > div > div { border: none !important; box-shadow: none !important; background: transparent !important; }
    [data-testid="stSidebar"] .stTextInput > div { border: none !important; }
    [data-testid="stSidebar"] .stTextInput label { display: none !important; }

    /* alert chips */
    .ac {
        display: flex; align-items: center; gap: 10px;
        padding: 7px 18px; font-size: 12.5px;
    }
    .adot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .adot-c { background: #e05252; }
    .adot-w { background: #e0943a; }
    .an  { color: #999; }
    .as-c { color: #e05252; font-size: 10px; margin-left: auto; font-weight: 500; }
    .as-w { color: #e0943a; font-size: 10px; margin-left: auto; font-weight: 500; }

    /* sidebar all buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #888 !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        text-align: left !important;
        height: auto !important;
        padding: 8px 12px !important;
        white-space: normal !important;
        line-height: 1.45 !important;
        width: 100% !important;
        margin: 1px 0 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1a1a1a !important;
        color: #ececec !important;
    }
    /* new chat accent */
    [data-testid="stSidebar"] div:nth-child(3) .stButton > button {
        background: linear-gradient(135deg, #d4714a, #c96442) !important;
        color: white !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 10px 16px !important;
        margin-bottom: 4px !important;
    }
    [data-testid="stSidebar"] div:nth-child(3) .stButton > button:hover {
        background: linear-gradient(135deg, #c96442, #b5573a) !important;
        color: white !important;
    }

    /* ── MAIN / CHAT ─────────────────────────── */
    .topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 16px 0 14px;
        border-bottom: 1px solid #222;
        max-width: 1000px; margin: 0 auto; padding-left: 24px; padding-right: 24px;
    }
    .topbar-t { font-size: 14px; font-weight: 500; color: #ececec; letter-spacing: -0.01em; }
    .topbar-r { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #555; }
    .live { width: 7px; height: 7px; background: #3da05e; border-radius: 50%; animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

    /* ── SIDEBAR TOGGLE ───────────────────────── */
    .sb-toggle-wrap .stButton > button {
        background: transparent !important;
        border: 1px solid #282828 !important;
        border-radius: 10px !important;
        color: #666 !important;
        font-size: 18px !important;
        padding: 4px 10px !important;
        height: 36px !important;
        width: 36px !important;
        min-width: 36px !important;
        line-height: 1 !important;
        transition: all 0.15s ease !important;
    }
    .sb-toggle-wrap .stButton > button:hover {
        background: #1e1e1e !important;
        border-color: #444 !important;
        color: #ececec !important;
    }

    /* ── EMPTY STATE ──────────────────────────── */
    .empty-wrap {
        display: flex; flex-direction: column; align-items: center;
        text-align: center; padding: 120px 24px 40px; max-width: 1000px;
        margin: 0 auto;
    }
    .empty-ic {
        width: 56px; height: 56px;
        background: linear-gradient(135deg, #d4714a, #c96442);
        border-radius: 16px;
        display: flex; align-items: center; justify-content: center;
        font-size: 28px; margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(201,100,66,0.2);
    }
    .empty-t {
        font-size: 26px; font-weight: 600; color: #ececec;
        letter-spacing: -0.03em; margin-bottom: 12px;
    }
    .empty-s {
        font-size: 15px; color: #666; max-width: 420px;
        line-height: 1.7; margin-bottom: 48px;
    }

    /* suggestion buttons in main area */
    .sug-wrap { max-width: 700px; margin: 0 auto; padding: 0 24px; width: 100%; }
    .sug-wrap .stButton > button {
        background: #1c1c1c !important;
        border: 1px solid #282828 !important;
        border-radius: 14px !important;
        color: #999 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13.5px !important;
        font-weight: 400 !important;
        text-align: left !important;
        height: auto !important;
        padding: 16px 20px !important;
        white-space: normal !important;
        line-height: 1.5 !important;
        transition: all 0.2s ease !important;
    }
    .sug-wrap .stButton > button:hover {
        background: #222 !important;
        border-color: #c96442 !important;
        color: #ececec !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    }

    /* ── MESSAGES ─────────────────────────────── */
    .msg-row {
        display: flex; gap: 16px; margin-bottom: 32px;
        align-items: flex-start;
    }
    .av {
        width: 32px; height: 32px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 12px; flex-shrink: 0; margin-top: 3px;
    }
    .av-u { background: #282828; color: #999; font-weight: 600; }
    .av-a { background: linear-gradient(135deg, #d4714a, #c96442); color: white; font-size: 14px; }
    .mb   { flex: 1; min-width: 0; }
    .ms   { font-size: 12px; font-weight: 500; color: #555; margin-bottom: 6px; }
    .mt   { font-size: 15.5px; line-height: 1.75; color: #d4d4d4; word-break: break-word; }
    .mt p { margin: 0 0 10px; }
    .mt p:last-child { margin: 0; }
    .mt code {
        background: #222; padding: 2px 6px; border-radius: 5px;
        font-family: 'JetBrains Mono', monospace; font-size: 13px; color: #d4714a;
    }
    .mt pre {
        background: #0e0e0e; color: #d4d4d4; padding: 16px 18px; border-radius: 12px;
        overflow-x: auto; font-family: 'JetBrains Mono', monospace; font-size: 13px;
        line-height: 1.65; margin: 12px 0; border: 1px solid #222;
    }
    .mt pre code { background: transparent; color: inherit; padding: 0; }

    /* ── INPUT BAR ────────────────────────────── */
    .inp-outer {
        max-width: 1000px; margin: 0 auto;
        padding: 16px 24px 24px; box-sizing: border-box;
    }
    .inp-outer .stTextInput > div > div > input {
        background: #1c1c1c !important; border: 1px solid #282828 !important;
        border-radius: 22px !important;
        outline: none !important; box-shadow: none !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14.5px !important; color: #ececec !important;
        padding: 14px 22px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .inp-outer .stTextInput > div > div > input:focus {
        border-color: #c96442 !important;
        box-shadow: 0 0 0 3px rgba(201,100,66,0.12) !important;
    }
    .inp-outer .stTextInput > div > div > input::placeholder { color: #555 !important; }
    .inp-outer .stTextInput > div > div { border: none !important; background: transparent !important; box-shadow: none !important; }
    .inp-outer .stTextInput > div { border: none !important; }
    .inp-outer .stTextInput label { display: none !important; }
    .inp-outer .stButton > button {
        background: linear-gradient(135deg, #d4714a, #c96442) !important;
        color: white !important;
        border: none !important; border-radius: 22px !important;
        padding: 10px 24px !important; font-family: 'Inter', sans-serif !important;
        font-size: 14px !important; font-weight: 500 !important;
        height: 44px !important; white-space: nowrap !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(201,100,66,0.2) !important;
    }
    .inp-outer .stButton > button:hover {
        background: linear-gradient(135deg, #c96442, #b5573a) !important;
        box-shadow: 0 4px 16px rgba(201,100,66,0.3) !important;
    }

    .footer-note {
        text-align: center; font-size: 11.5px; color: #444;
        margin-top: 8px; letter-spacing: 0.01em;
    }

    /* scrollable chat container */
    [data-testid="stVerticalBlockBorderWrapper"] > div {
        background: transparent !important;
        border: none !important;
    }

    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #282828; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #333; }

    .sb-toggle-wrap {
        position: fixed;
        top: 14px;
        left: 14px;
        z-index: 999;
    }

    /* smooth sidebar animation */
    [data-testid="stSidebar"] {
        transition: transform 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state ───────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []  # list of {"title": str, "messages": list}

if "sidebar_open" not in st.session_state:
    st.session_state.sidebar_open = True

if "last_rca" not in st.session_state:
    st.session_state.last_rca = ""
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

# ── SIDEBAR ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo-row">
        <div class="sb-logo">🔧</div>
        <div>
            <div class="sb-name">NetFix AI</div>
            <div class="sb-tag">Network Troubleshooting Analyst</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Navigation</div>', unsafe_allow_html=True)

    if st.button("Dashboard", use_container_width=True):
        st.session_state.page = "dashboard"
        st.rerun()

    if st.button("Chat", use_container_width=True):
        st.session_state.page = "chat"
        st.rerun()

    # New conversation
    st.markdown('<div style="padding:10px 14px 4px;">', unsafe_allow_html=True)
    if st.button("＋  New conversation", key="new_chat", use_container_width=True):
        if st.session_state.chat_messages:
            first = st.session_state.chat_messages[0]["content"]
            title = (first[:44] + "…") if len(first) > 44 else first
            st.session_state.chat_sessions.insert(0, {
                "title": title,
                "messages": st.session_state.chat_messages.copy()
            })
        st.session_state.chat_messages = []
        reset_conversation()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Chat history with search
    if st.session_state.chat_sessions:
        st.markdown('<div class="sb-sec">Chat History</div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:0 12px 6px;">', unsafe_allow_html=True)
        search_q = st.text_input("s", placeholder="🔍  Search conversations…", key="hist_search", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        sessions_to_show = [
            s for s in st.session_state.chat_sessions
            if not search_q or search_q.lower() in s["title"].lower()
        ][:15]

        for idx, sess in enumerate(sessions_to_show):
            if st.button(f"💬  {sess['title']}", key=f"hs_{idx}", use_container_width=True):
                if st.session_state.chat_messages:
                    first = st.session_state.chat_messages[0]["content"]
                    title = (first[:44] + "…") if len(first) > 44 else first
                    st.session_state.chat_sessions.insert(0, {
                        "title": title,
                        "messages": st.session_state.chat_messages.copy()
                    })
                st.session_state.chat_messages = sess["messages"].copy()
                st.rerun()

    # Actions
    st.markdown('<div class="sb-sec" style="margin-top:10px;">Actions</div>', unsafe_allow_html=True)

    if st.session_state.get("last_rca"):
        if st.button("💾 Save to Knowledge Base", use_container_width=True, key="save_kb"):
            st.session_state.show_kb_form = True

        if st.button("📄 Generate Runbook PDF", use_container_width=True, key="gen_runbook"):
            with st.spinner("Generating runbook PDF..."):
                try:
                    filepath = create_runbook_pdf(
                        incident_id=f"INC-{datetime.now().strftime('%Y%m%d-%H%M')}",
                        incident_description=st.session_state.last_query,
                        rca_response=st.session_state.last_rca
                    )
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="⬇ Download Runbook",
                            data=f,
                            file_name=os.path.basename(filepath),
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.get("show_kb_form"):
        with st.form("kb_form"):
            st.markdown('<div style="padding:0 10px;">', unsafe_allow_html=True)
            device = st.text_input("Device", placeholder="e.g. ROUTER-LAB-01")
            symptoms = st.text_input("Symptoms", placeholder="e.g. BGP drop, CPU spike")
            resolution = st.text_area("Resolution", placeholder="What fixed it?", height=80)
            submitted = st.form_submit_button("Save", use_container_width=True)
            if submitted and device and symptoms and resolution:
                kb_id = save_to_kb(
                    device=device,
                    symptoms=symptoms,
                    root_cause=st.session_state.last_rca[:300],
                    resolution=resolution
                )
                st.success(f"Saved as {kb_id}")
                st.session_state.show_kb_form = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    kb_entries = get_all_kb()
    if kb_entries:
        st.markdown('<div class="sb-sec" style="margin-top:10px;">Knowledge Base</div>', unsafe_allow_html=True)
        for entry in kb_entries[-3:]:
            st.markdown(f"""
            <div style='padding:6px 16px; font-size:11px; color:#888;'>
                <b style='color:#c96442;'>{entry['id']}</b> — {entry['device']}<br>
                <span style='color:#555;'>{entry['symptoms'][:50]}...</span>
            </div>
            """, unsafe_allow_html=True)

    # Active Alerts
    st.markdown('<div class="sb-sec" style="margin-top:10px;">Active Alerts</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ac"><span class="adot adot-c"></span><span class="an">ROUTER-LAB-01</span><span class="as-c">DEGRADED</span></div>
    <div class="ac"><span class="adot adot-c"></span><span class="an">SW-LAB-02</span><span class="as-c">DOWN</span></div>
    <div class="ac"><span class="adot adot-c"></span><span class="an">5G-UPF-01</span><span class="as-c">ERROR</span></div>
    <div class="ac"><span class="adot adot-w"></span><span class="an">5G-AMF-01</span><span class="as-w">WARNING</span></div>
    <div class="ac"><span class="adot adot-w"></span><span class="an">5G-SMF-01</span><span class="as-w">WARNING</span></div>
    """, unsafe_allow_html=True)


# ── MAIN AREA ───────────────────────────────────────────────────────────────────

# Top bar with sidebar toggle

tb_left, tb_right = st.columns([1, 20])

with tb_left:
    st.markdown('<div class="sb-toggle-wrap">', unsafe_allow_html=True)

    arrow = "❮" if st.session_state.sidebar_open else "❯"

    if st.button(arrow, key="sb_toggle"):
        st.session_state.sidebar_open = not st.session_state.sidebar_open

    st.markdown('</div>', unsafe_allow_html=True)

sidebar_style = f"""
<style>
[data-testid="stSidebar"] {{
    transition: transform 0.3s ease;
    transform: translateX({'0%' if st.session_state.sidebar_open else '-100%'});
    position: relative;
    z-index: 999;
}}
</style>
"""
st.markdown(sidebar_style, unsafe_allow_html=True)

st.markdown("""
<div class="topbar">
    <span class="topbar-t">Network Troubleshooting</span>
    <span class="topbar-r"><span class="live"></span>Live data</span>
</div>
""", unsafe_allow_html=True)

# ── Empty state (with 4 suggestion cards) ──────────────────────────────────────
if not st.session_state.chat_messages:
    st.markdown("""
    <div class="empty-wrap">
        <div class="empty-ic">🔧</div>
        <div class="empty-t">How can I help your network?</div>
        <div class="empty-s">I've analysed all syslogs, SNMP metrics, topology, and incident tickets. Ask anything about your lab.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="sug-wrap">', unsafe_allow_html=True)
        suggestions = [
            "What happened to ROUTER-LAB-01 between 08:10 and 08:20?",
            "What is the blast radius of the 5G UPF crash?",
            "Has this BGP drop happened before in this network?",
            "Give me a summary of all open P1 incidents",
        ]
        c1, c2 = st.columns(2)
        for i, s in enumerate(suggestions):
            with (c1 if i % 2 == 0 else c2):
                if st.button(s, key=f"sug_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": s})
                    with st.spinner("Analysing…"):
                        resp = query_netfix(s)
                    st.session_state.chat_messages.append({"role": "assistant", "content": resp})
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # ── Conversation ────────────────────────────────────────────────────────────
    msgs = st.container(height=520, border=False)
    with msgs:
        st.markdown('<div style="max-width:1000px; margin:0 auto; padding:28px 24px 8px;">', unsafe_allow_html=True)
        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="msg-row">
                    <div class="av av-u">Y</div>
                    <div class="mb">
                        <div class="ms">You</div>
                        <div class="mt"><p>{message['content']}</p></div>
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="msg-row">
                    <div class="av av-a">🔧</div>
                    <div class="mb">
                        <div class="ms">NetFix AI</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                st.markdown(message['content'])
        st.markdown('</div>', unsafe_allow_html=True)

# ── Input bar ───────────────────────────────────────────────────────────────────
st.markdown('<div class="inp-outer">', unsafe_allow_html=True)
ic, bc = st.columns([7, 1])
with ic:
    user_input = st.text_input(
        "i", placeholder="Ask about any device, incident, or network issue…",
        label_visibility="collapsed", key="chat_input"
    )
with bc:
    send = st.button("Send ↑", type="primary", use_container_width=True)
st.markdown(
    '<p class="footer-note">NetFix AI can make mistakes. Always verify critical changes before applying.</p>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

if send and user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.spinner("NetFix AI is analysing…"):
        response = query_netfix(user_input)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.session_state.last_rca = response
    st.session_state.last_query = user_input
    st.rerun()