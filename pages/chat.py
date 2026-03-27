import streamlit as st
from src.agent import query_netfix, reset_conversation

st.set_page_config(
    page_title="NetFix AI — Chat",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;600;700&display=swap');

    :root {
        --bg:        #0d0d0f;
        --surface:   #13131a;
        --card:      #17171f;
        --border:    #1f1f2e;
        --border-hi: #2a2a40;
        --accent1:   #7c3aed;
        --accent2:   #4f46e5;
        --accent3:   #2563eb;
        --grad:      linear-gradient(135deg, #7c3aed, #4f46e5, #2563eb);
        --glow:      rgba(124, 58, 237, 0.18);
        --red:       #ef4444;
        --amber:     #f59e0b;
        --green:     #22c55e;
        --red-dim:   rgba(239,68,68,0.1);
        --amber-dim: rgba(245,158,11,0.1);
        --text-1:    #f0f0f8;
        --text-2:    #9090b0;
        --text-3:    #4a4a6a;
        --mono:      'IBM Plex Mono', monospace;
        --sans:      'Outfit', sans-serif;
        --display:   'Syne', sans-serif;
    }

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main {
        background-color: var(--bg) !important;
        font-family: var(--sans);
        color: var(--text-1);
    }

    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"],
    [data-testid="stSidebarNav"],
    [data-testid="stStatusWidget"] { display: none !important; }

    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* ── SIDEBAR ──────────────────────────────── */
    [data-testid="stSidebar"] {
        background-color: var(--surface) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

    .sb-header {
        padding: 20px 18px 16px;
        border-bottom: 1px solid var(--border);
    }
    .sb-logo-row { display: flex; align-items: center; gap: 12px; }
    .sb-logo {
        width: 38px; height: 38px;
        background: linear-gradient(135deg, var(--accent1), var(--accent3));
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 18px; flex-shrink: 0;
        box-shadow: 0 0 16px var(--glow);
    }
    .sb-name { font-family: var(--display); font-size: 15px; font-weight: 700; color: var(--text-1); letter-spacing: -0.01em; }
    .sb-tag  { font-size: 10px; color: var(--text-3); margin-top: 2px; font-family: var(--mono); letter-spacing: 0.06em; text-transform: uppercase; }

    .sb-sec {
        padding: 16px 18px 6px;
        font-size: 9.5px; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-3);
        font-family: var(--mono);
    }

    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: var(--text-2) !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: var(--sans) !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        text-align: left !important;
        height: auto !important;
        padding: 7px 12px !important;
        white-space: normal !important;
        line-height: 1.45 !important;
        width: 100% !important;
        margin: 1px 0 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--border) !important;
        color: var(--text-1) !important;
    }

    /* New chat button — gradient accent */
    .new-chat-btn .stButton > button {
        background: var(--grad) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        border-radius: 10px !important;
        box-shadow: 0 0 20px var(--glow) !important;
        font-size: 13px !important;
        margin-bottom: 2px !important;
    }
    .new-chat-btn .stButton > button:hover {
        box-shadow: 0 0 28px var(--glow) !important;
        transform: translateY(-1px);
    }

    /* Sidebar text search */
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-1) !important;
        font-family: var(--sans) !important;
        font-size: 12.5px !important;
        padding: 7px 12px !important;
    }
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder { color: var(--text-3) !important; }
    [data-testid="stSidebar"] .stTextInput > div > div,
    [data-testid="stSidebar"] .stTextInput > div { border: none !important; background: transparent !important; box-shadow: none !important; }
    [data-testid="stSidebar"] .stTextInput label { display: none !important; }

    /* Alerts */
    .alert-item { display: flex; align-items: center; gap: 10px; padding: 6px 18px; font-size: 12px; }
    .adot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
    .adot-r { background: var(--red); box-shadow: 0 0 6px rgba(239,68,68,0.5); }
    .adot-a { background: var(--amber); box-shadow: 0 0 6px rgba(245,158,11,0.4); }
    .alert-name { color: var(--text-2); flex: 1; }
    .badge-r { font-family: var(--mono); font-size: 9px; color: var(--red); background: var(--red-dim); padding: 2px 7px; border-radius: 4px; }
    .badge-a { font-family: var(--mono); font-size: 9px; color: var(--amber); background: var(--amber-dim); padding: 2px 7px; border-radius: 4px; }

    /* ── TOP BAR ──────────────────────────────── */
    .topbar {
        max-width: 900px; margin: 0 auto;
        padding: 18px 24px 14px;
        border-bottom: 1px solid var(--border);
        display: flex; align-items: center; justify-content: space-between;
    }
    .topbar-title { font-family: var(--display); font-size: 15px; font-weight: 600; color: var(--text-1); letter-spacing: -0.02em; }
    .topbar-meta  { font-family: var(--mono); font-size: 11px; color: var(--text-3); display: flex; align-items: center; gap: 6px; }
    .live-dot {
        display: inline-block; width: 6px; height: 6px;
        background: var(--green); border-radius: 50%;
        animation: pulse 2s infinite;
        box-shadow: 0 0 8px rgba(34,197,94,0.6);
    }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.2} }

    /* ── EMPTY STATE ──────────────────────────── */
    .empty-state {
        max-width: 900px; margin: 0 auto;
        padding: 80px 24px 40px;
        display: flex; flex-direction: column; align-items: center; text-align: center;
    }
    .empty-icon {
        width: 60px; height: 60px;
        background: var(--grad);
        border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        font-size: 28px; margin-bottom: 24px;
        box-shadow: 0 8px 32px var(--glow);
    }
    .empty-title {
        font-family: var(--display);
        font-size: 28px; font-weight: 700; color: var(--text-1);
        letter-spacing: -0.03em; margin-bottom: 12px;
    }
    .empty-sub {
        font-size: 15px; color: var(--text-2); max-width: 440px;
        line-height: 1.75; margin-bottom: 48px;
    }

    /* Suggestion cards */
    .sug-grid { max-width: 720px; margin: 0 auto; padding: 0 24px; width: 100%; }
    .sug-grid .stButton > button {
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
        color: var(--text-2) !important;
        font-family: var(--sans) !important;
        font-size: 13.5px !important;
        font-weight: 400 !important;
        text-align: left !important;
        height: auto !important;
        padding: 18px 20px !important;
        white-space: normal !important;
        line-height: 1.6 !important;
        transition: all 0.2s ease !important;
    }
    .sug-grid .stButton > button:hover {
        background: var(--surface) !important;
        border-color: var(--accent1) !important;
        color: var(--text-1) !important;
        box-shadow: 0 0 20px var(--glow) !important;
        transform: translateY(-2px);
    }

    /* ── MESSAGES ─────────────────────────────── */
    .chat-outer { max-width: 900px; margin: 0 auto; padding: 28px 24px 12px; }

    .msg-user {
        display: flex; justify-content: flex-end; margin-bottom: 24px;
    }
    .msg-ai {
        display: flex; justify-content: flex-start; gap: 14px; margin-bottom: 24px; align-items: flex-start;
    }
    .bubble-user {
        background: linear-gradient(135deg, var(--accent1) 0%, var(--accent2) 100%);
        color: #fff;
        padding: 13px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 72%;
        font-size: 14.5px; line-height: 1.7;
        box-shadow: 0 4px 20px var(--glow);
    }
    .bubble-ai {
        background: var(--card);
        border: 1px solid var(--border);
        color: var(--text-1);
        padding: 15px 20px;
        border-radius: 4px 18px 18px 18px;
        max-width: 80%;
        font-size: 14.5px; line-height: 1.8;
        word-break: break-word;
    }
    .bubble-ai p { margin: 0 0 10px; }
    .bubble-ai p:last-child { margin: 0; }
    .bubble-ai code {
        background: var(--surface);
        border: 1px solid var(--border);
        padding: 2px 7px; border-radius: 5px;
        font-family: var(--mono); font-size: 13px; color: #a78bfa;
    }
    .bubble-ai pre {
        background: #0a0a10;
        border: 1px solid var(--border);
        color: var(--text-2); padding: 16px 18px; border-radius: 10px;
        overflow-x: auto; font-family: var(--mono); font-size: 13px;
        line-height: 1.7; margin: 12px 0;
    }
    .bubble-ai pre code { background: transparent; border: none; color: inherit; padding: 0; }
    .bubble-ai ul, .bubble-ai ol { padding-left: 20px; margin: 8px 0; }
    .bubble-ai li { margin-bottom: 4px; color: var(--text-2); }
    .bubble-ai strong { color: var(--text-1); font-weight: 600; }
    .bubble-ai h1,.bubble-ai h2,.bubble-ai h3 { color: var(--text-1); font-family: var(--display); margin: 16px 0 8px; }

    .ai-avatar {
        width: 34px; height: 34px; flex-shrink: 0; margin-top: 2px;
        background: var(--grad);
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 15px;
        box-shadow: 0 0 12px var(--glow);
    }
    .msg-sender { font-family: var(--mono); font-size: 10px; color: var(--text-3); margin-bottom: 5px; letter-spacing: 0.06em; }

    /* ── INPUT BAR ────────────────────────────── */
    .inp-wrap {
        max-width: 900px; margin: 0 auto;
        padding: 14px 24px 28px;
    }
    .inp-wrap .stTextInput > div > div > input {
        background: var(--card) !important;
        border: 1px solid var(--border-hi) !important;
        border-radius: 24px !important;
        outline: none !important; box-shadow: none !important;
        font-family: var(--sans) !important;
        font-size: 14.5px !important; color: var(--text-1) !important;
        padding: 14px 24px !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    .inp-wrap .stTextInput > div > div > input:focus {
        border-color: var(--accent1) !important;
        box-shadow: 0 0 0 3px var(--glow) !important;
    }
    .inp-wrap .stTextInput > div > div > input::placeholder { color: var(--text-3) !important; }
    .inp-wrap .stTextInput > div > div,
    .inp-wrap .stTextInput > div { border: none !important; background: transparent !important; box-shadow: none !important; }
    .inp-wrap .stTextInput label { display: none !important; }
    .inp-wrap .stButton > button {
        background: var(--grad) !important;
        color: white !important; border: none !important;
        border-radius: 24px !important; padding: 12px 28px !important;
        font-family: var(--sans) !important; font-size: 14px !important; font-weight: 600 !important;
        height: 52px !important; white-space: nowrap !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 16px var(--glow) !important;
        letter-spacing: 0.01em !important;
    }
    .inp-wrap .stButton > button:hover {
        box-shadow: 0 4px 28px var(--glow) !important;
        transform: translateY(-1px) !important;
    }
    .footer-hint {
        text-align: center; font-family: var(--mono); font-size: 10.5px; color: var(--text-3);
        margin-top: 8px; letter-spacing: 0.04em;
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #333350; }
</style>
""", unsafe_allow_html=True)

# ── Session state ────────────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []

# Pre-fill from dashboard quick actions
if "dashboard_query" in st.session_state and st.session_state["dashboard_query"]:
    dq = st.session_state.pop("dashboard_query")
    st.session_state.chat_messages.append({"role": "user", "content": dq})
    with st.spinner("Analysing…"):
        resp = query_netfix(dq)
    st.session_state.chat_messages.append({"role": "assistant", "content": resp})

# ── SIDEBAR ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-header">
        <div class="sb-logo-row">
            <div class="sb-logo">⬡</div>
            <div>
                <div class="sb-name">NetFix AI</div>
                <div class="sb-tag">Chat Analyst</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:2px 10px;">', unsafe_allow_html=True)
    st.page_link("app.py",        label="◈  Dashboard",    use_container_width=True)
    st.page_link("pages/chat.py", label="◎  Chat Analyst", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="padding:8px 12px 4px;">', unsafe_allow_html=True)
    st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
    if st.button("＋  New Conversation", key="new_chat", use_container_width=True):
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
    st.markdown('</div></div>', unsafe_allow_html=True)

    if st.session_state.chat_sessions:
        st.markdown('<div class="sb-sec">History</div>', unsafe_allow_html=True)
        st.markdown('<div style="padding:0 12px 6px;">', unsafe_allow_html=True)
        search_q = st.text_input("s", placeholder="🔍 Search conversations…", key="hist_search", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        sessions_to_show = [
            s for s in st.session_state.chat_sessions
            if not search_q or search_q.lower() in s["title"].lower()
        ][:15]

        for idx, sess in enumerate(sessions_to_show):
            if st.button(f"◌  {sess['title']}", key=f"hs_{idx}", use_container_width=True):
                if st.session_state.chat_messages:
                    first = st.session_state.chat_messages[0]["content"]
                    title = (first[:44] + "…") if len(first) > 44 else first
                    st.session_state.chat_sessions.insert(0, {
                        "title": title,
                        "messages": st.session_state.chat_messages.copy()
                    })
                st.session_state.chat_messages = sess["messages"].copy()
                st.rerun()

    st.markdown('<div class="sb-sec" style="margin-top:8px;">Active Alerts</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-item"><span class="adot adot-r"></span><span class="alert-name">ROUTER-LAB-01</span><span class="badge-r">DEGRADED</span></div>
    <div class="alert-item"><span class="adot adot-r"></span><span class="alert-name">SW-LAB-02</span><span class="badge-r">DOWN</span></div>
    <div class="alert-item"><span class="adot adot-r"></span><span class="alert-name">5G-UPF-01</span><span class="badge-r">ERROR</span></div>
    <div class="alert-item"><span class="adot adot-a"></span><span class="alert-name">5G-AMF-01</span><span class="badge-a">WARNING</span></div>
    <div class="alert-item"><span class="adot adot-a"></span><span class="alert-name">5G-SMF-01</span><span class="badge-a">WARNING</span></div>
    """, unsafe_allow_html=True)

# ── TOP BAR ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <span class="topbar-title">Network Troubleshooting Analyst</span>
    <span class="topbar-meta"><span class="live-dot"></span>Live data</span>
</div>
""", unsafe_allow_html=True)

# ── EMPTY STATE ───────────────────────────────────────────────────────────────────
if not st.session_state.chat_messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">⬡</div>
        <div class="empty-title">How can I help your network?</div>
        <div class="empty-sub">
            I've analysed all syslogs, SNMP metrics, topology data,
            and incident tickets. Ask anything about your lab infrastructure.
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="sug-grid">', unsafe_allow_html=True)
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
    # ── CONVERSATION ────────────────────────────────────────────────────────────
    msgs_container = st.container(height=540, border=False)
    with msgs_container:
        st.markdown('<div class="chat-outer">', unsafe_allow_html=True)

        for message in st.session_state.chat_messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                    <div>
                        <div class="msg-sender" style="text-align:right; margin-bottom:5px; margin-right:4px;">You</div>
                        <div class="bubble-user">{message['content']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Use st.markdown for AI messages to get proper markdown rendering
                st.markdown("""
                <div class="msg-ai">
                    <div class="ai-avatar">⬡</div>
                    <div style="flex:1; min-width:0;">
                        <div class="msg-sender">NetFix AI</div>
                """, unsafe_allow_html=True)
                st.markdown(
                    f'<div class="bubble-ai">{message["content"]}</div>',
                    unsafe_allow_html=True
                )
                st.markdown('</div></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ── INPUT BAR ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="inp-wrap">', unsafe_allow_html=True)
ic, bc = st.columns([8, 1])
with ic:
    user_input = st.text_input(
        "i", placeholder="Ask about any device, incident, or network anomaly…",
        label_visibility="collapsed", key="chat_input"
    )
with bc:
    send = st.button("Send ↑", type="primary", use_container_width=True)
st.markdown('<p class="footer-hint">NetFix AI may make mistakes · always verify before applying changes</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

if send and user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.spinner("NetFix AI is analysing…"):
        response = query_netfix(user_input)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()