import streamlit as st
from src.agent import query_netfix, reset_conversation

st.set_page_config(
    page_title="NetFix AI — Chat",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── SESSION STATE INIT ──────────────────────────────────
if "chat_messages"   not in st.session_state: st.session_state.chat_messages   = []
if "chat_sessions"   not in st.session_state: st.session_state.chat_sessions   = []
if "sidebar_visible" not in st.session_state: st.session_state.sidebar_visible = True

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    /* ── BASE ── */
    *, *::before, *::after { box-sizing: border-box; }

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main {
        background-color: #0d0d0d !important;
        font-family: 'IBM Plex Sans', sans-serif;
        color: #e0ddd8;
    }

    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"],
    [data-testid="stSidebarNav"],
    [data-testid="stStatusWidget"] { display: none !important; }

    .block-container { padding: 0 !important; max-width: 100% !important; }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #1a1a1a !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

    .sb-logo-row {
        display: flex; align-items: center; gap: 12px;
        padding: 22px 18px 18px;
        border-bottom: 1px solid #1a1a1a;
        margin-bottom: 4px;
    }
    .sb-logo {
        width: 36px; height: 36px; background: #bf5c38;
        border-radius: 8px; display: flex; align-items: center;
        justify-content: center; font-size: 16px; flex-shrink: 0;
    }
    .sb-name  { font-size: 13px; font-weight: 600; color: #e0ddd8; }
    .sb-tag   { font-size: 11px; color: #444; margin-top: 1px; font-family: 'IBM Plex Mono', monospace; }

    .sb-sec {
        padding: 14px 18px 6px;
        font-size: 10px; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase; color: #333;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* ── SIDEBAR BUTTONS ── */
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #666 !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        text-align: left !important;
        height: auto !important;
        padding: 7px 12px !important;
        white-space: normal !important;
        line-height: 1.4 !important;
        width: 100% !important;
        margin: 1px 0 !important;
        transition: background 0.1s, color 0.1s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #141414 !important;
        color: #e0ddd8 !important;
    }

    /* New Chat button - accent */
    .new-chat-btn .stButton > button {
        background: #bf5c38 !important;
        color: white !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 9px 14px !important;
        margin-bottom: 4px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
    }
    .new-chat-btn .stButton > button:hover {
        background: #a84f30 !important;
        color: white !important;
    }

    /* History buttons */
    .hist-btn .stButton > button {
        color: #555 !important;
        font-size: 12px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        padding: 6px 12px !important;
        border-left: 2px solid transparent !important;
        border-radius: 0 !important;
    }
    .hist-btn .stButton > button:hover {
        color: #e0ddd8 !important;
        border-left-color: #bf5c38 !important;
        background: #111 !important;
    }

    /* Sidebar page links */
    [data-testid="stSidebar"] .stPageLink a {
        color: #666 !important; font-size: 13px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        padding: 7px 12px !important; display: block !important;
        text-decoration: none !important; border-radius: 6px !important;
        transition: all 0.1s !important; margin: 1px 0 !important;
    }
    [data-testid="stSidebar"] .stPageLink a:hover {
        background: #141414 !important; color: #e0ddd8 !important;
    }

    /* Alert items */
    .alert-item {
        display: flex; align-items: center; gap: 10px;
        padding: 5px 18px; font-size: 11.5px;
    }
    .adot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
    .adot-c { background: #e05252; }
    .adot-w { background: #d4943a; }
    .aname  { color: #666; flex: 1; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
    .astatus-c { color: #e05252; font-size: 10px; font-family: 'IBM Plex Mono', monospace; }
    .astatus-w { color: #d4943a; font-size: 10px; font-family: 'IBM Plex Mono', monospace; }

    /* ── TOPBAR ── */
    .topbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 28px;
        border-bottom: 1px solid #1a1a1a;
        background: #0d0d0d;
    }
    .topbar-left { display: flex; align-items: center; gap: 14px; }
    .topbar-t { font-size: 13px; font-weight: 500; color: #e0ddd8; }
    .topbar-r { font-size: 11px; color: #444; font-family: 'IBM Plex Mono', monospace; display: flex; align-items: center; gap: 6px; }
    .live-dot { width: 6px; height: 6px; background: #3da05e; border-radius: 50%;
        display: inline-block; animation: blink 2s infinite; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

    /* Toggle button in topbar */
    .toggle-btn .stButton > button {
        background: transparent !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 6px !important;
        color: #555 !important;
        font-size: 14px !important;
        padding: 4px 9px !important;
        height: 30px !important;
        width: 32px !important;
        min-width: 32px !important;
        line-height: 1 !important;
        transition: all 0.1s !important;
    }
    .toggle-btn .stButton > button:hover {
        border-color: #333 !important;
        color: #e0ddd8 !important;
        background: #111 !important;
    }

    /* ── EMPTY STATE ── */
    .empty-wrap {
        display: flex; flex-direction: column; align-items: center;
        text-align: center; padding: 80px 24px 32px;
    }
    .empty-ic {
        width: 52px; height: 52px; background: #bf5c38;
        border-radius: 12px; display: flex; align-items: center;
        justify-content: center; font-size: 24px; margin-bottom: 20px;
    }
    .empty-t { font-size: 22px; font-weight: 500; color: #e0ddd8; letter-spacing: -0.02em; margin-bottom: 10px; }
    .empty-s { font-size: 14px; color: #555; max-width: 400px; line-height: 1.7; margin-bottom: 40px; }

    /* Suggestion cards */
    .sug-wrap .stButton > button {
        background: #111 !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 8px !important;
        color: #888 !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13.5px !important;
        font-weight: 400 !important;
        text-align: left !important;
        height: auto !important;
        padding: 14px 18px !important;
        white-space: normal !important;
        line-height: 1.5 !important;
        transition: all 0.15s !important;
    }
    .sug-wrap .stButton > button:hover {
        border-color: #bf5c38 !important;
        color: #e0ddd8 !important;
        background: #131313 !important;
    }

    /* ── CHAT MESSAGES ── */
    .chat-area {
        max-width: 860px;
        margin: 0 auto;
        padding: 28px 24px 12px;
    }

    /* User message */
    .msg-user {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 20px;
        gap: 12px;
        align-items: flex-end;
    }
    .bubble-user {
        background: #1d1d1d;
        border: 1px solid #2a2a2a;
        border-radius: 16px 16px 4px 16px;
        padding: 14px 18px;
        max-width: 70%;
        font-size: 15px;
        line-height: 1.65;
        color: #ddd;
        word-break: break-word;
    }
    .av-user {
        width: 30px; height: 30px; border-radius: 50%;
        background: #1e1e1e; border: 1px solid #2a2a2a;
        display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 600; color: #666;
        flex-shrink: 0;
    }

    /* Assistant message */
    .msg-ai {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 24px;
        gap: 12px;
        align-items: flex-start;
    }
    .av-ai {
        width: 30px; height: 30px; border-radius: 50%;
        background: #bf5c38;
        display: flex; align-items: center; justify-content: center;
        font-size: 14px;
        flex-shrink: 0;
        margin-top: 2px;
    }
    .bubble-ai-wrap { flex: 1; min-width: 0; }
    .bubble-ai-name { font-size: 11px; color: #444; margin-bottom: 8px; font-family: 'IBM Plex Mono', monospace; }

    /* AI bubble content rendered via st.markdown — override default styling */
    .bubble-ai-wrap .stMarkdown p {
        font-size: 15px !important;
        line-height: 1.75 !important;
        color: #ccc !important;
        margin: 0 0 10px !important;
    }
    .bubble-ai-wrap .stMarkdown p:last-child { margin: 0 !important; }
    .bubble-ai-wrap .stMarkdown code {
        background: #1a1a1a;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        color: #bf5c38;
    }
    .bubble-ai-wrap .stMarkdown pre {
        background: #0c0c0c;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 14px 16px;
        overflow-x: auto;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 13px;
        line-height: 1.6;
        color: #bbb;
        margin: 10px 0;
    }
    .bubble-ai-wrap .stMarkdown ul, .bubble-ai-wrap .stMarkdown ol {
        padding-left: 20px; color: #bbb;
        font-size: 15px; line-height: 1.7;
    }
    .bubble-ai-wrap .stMarkdown h3 {
        font-size: 14px; font-weight: 600; color: #e0ddd8;
        margin: 14px 0 6px; letter-spacing: -0.01em;
    }
    .bubble-ai-wrap .stMarkdown strong { color: #e0ddd8; }

    /* ── DIVIDER between msg groups ── */
    .msg-divider { border: none; border-top: 1px solid #141414; margin: 4px 0 20px; }

    /* ── INPUT BAR ── */
    .inp-outer {
        border-top: 1px solid #1a1a1a;
        padding: 16px 28px 20px;
        background: #0d0d0d;
        max-width: 860px;
        margin: 0 auto;
        box-sizing: border-box;
        width: 100%;
    }
    .inp-outer .stTextInput > div > div > input {
        background: #111 !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 8px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 14px !important;
        color: #e0ddd8 !important;
        padding: 12px 18px !important;
        transition: border-color 0.15s !important;
    }
    .inp-outer .stTextInput > div > div > input:focus {
        border-color: #bf5c38 !important;
        box-shadow: 0 0 0 3px rgba(191,92,56,.1) !important;
    }
    .inp-outer .stTextInput > div > div > input::placeholder { color: #444 !important; }
    .inp-outer .stTextInput > div > div { border: none !important; background: transparent !important; box-shadow: none !important; }
    .inp-outer .stTextInput > div { border: none !important; }
    .inp-outer .stTextInput label { display: none !important; }

    .inp-outer .stButton > button {
        background: #bf5c38 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0 22px !important;
        height: 46px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        white-space: nowrap !important;
        transition: background 0.1s !important;
    }
    .inp-outer .stButton > button:hover {
        background: #a84f30 !important;
    }

    .footer-note {
        text-align: center; font-size: 11px; color: #2e2e2e;
        margin-top: 8px; font-family: 'IBM Plex Mono', monospace;
    }

    /* Search input in sidebar */
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background: #111 !important; border: 1px solid #1e1e1e !important;
        border-radius: 6px !important; color: #888 !important;
        font-size: 12px !important; padding: 7px 12px !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
    [data-testid="stSidebar"] .stTextInput > div > div > input::placeholder { color: #333 !important; }
    [data-testid="stSidebar"] .stTextInput > div > div { border: none !important; box-shadow: none !important; background: transparent !important; }
    [data-testid="stSidebar"] .stTextInput > div { border: none !important; }
    [data-testid="stSidebar"] .stTextInput label { display: none !important; }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #1e1e1e; border-radius: 10px; }
            
    /* ── MARKDOWN RENDERING IN CHAT ── */
    .stMarkdown p {
        font-size: 15px !important;
        line-height: 1.75 !important;
        color: #ccc !important;
        margin: 0 0 8px !important;
    }
    .stMarkdown strong {
        color: #e0ddd8 !important;
        font-weight: 600 !important;
    }
    .stMarkdown code {
        background: #1a1a1a !important;
        padding: 2px 7px !important;
        border-radius: 4px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 13px !important;
        color: #bf5c38 !important;
    }
    .stMarkdown pre {
        background: #0c0c0c !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 8px !important;
        padding: 14px 16px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
        color: #bbb !important;
        margin: 10px 0 !important;
        overflow-x: auto !important;
    }
    .stMarkdown h2 {
        font-size: 11px !important;
        font-weight: 600 !important;
        color: #444 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        margin: 20px 0 8px !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
    .stMarkdown ul, .stMarkdown ol {
        color: #bbb !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
        padding-left: 20px !important;
    }
    .stMarkdown hr {
        border: none !important;
        border-top: 1px solid #1e1e1e !important;
        margin: 16px 0 !important;
    }
            
        /* Metric tables */
    .stMarkdown table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin: 8px 0 16px !important;
        font-size: 13px !important;
        font-family: 'IBM Plex Mono', monospace !important;
    }
    .stMarkdown th {
        display: none !important;
    }
    .stMarkdown td {
        padding: 6px 12px !important;
        border: none !important;
        border-bottom: 1px solid #1a1a1a !important;
        color: #888 !important;
        vertical-align: top !important;
    }
    .stMarkdown td:first-child {
        color: #555 !important;
        width: 120px !important;
        white-space: nowrap !important;
    }
    .stMarkdown td:last-child {
        color: #ccc !important;
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR VISIBILITY CONTROL ──────────────────────────
# Inject CSS to show/hide sidebar based on state
if not st.session_state.sidebar_visible:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    </style>
    """, unsafe_allow_html=True)

# ── SIDEBAR ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo-row">
        <div class="sb-logo">🔧</div>
        <div>
            <div class="sb-name">NetFix AI</div>
            <div class="sb-tag">chat analyst</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Navigation</div>', unsafe_allow_html=True)
    with st.container():
        st.page_link("app.py",        label="Dashboard",    use_container_width=True)
        st.page_link("pages/chat.py", label="Chat Analyst", use_container_width=True)

    # ── NEW CONVERSATION ─────────────────────────────────
    st.markdown('<div style="padding: 10px 14px 4px;">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="new-chat-btn">', unsafe_allow_html=True)
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
    st.markdown('</div>', unsafe_allow_html=True)

    # ── CHAT HISTORY ─────────────────────────────────────
    if st.session_state.chat_sessions:
        st.markdown('<div class="sb-sec">Chat History</div>', unsafe_allow_html=True)
        with st.container():
            search_q = st.text_input(
                "s", placeholder="Search conversations…",
                key="hist_search", label_visibility="collapsed"
            )
        sessions_to_show = [
            s for s in st.session_state.chat_sessions
            if not search_q or search_q.lower() in s["title"].lower()
        ][:15]
        for idx, sess in enumerate(sessions_to_show):
            with st.container():
                st.markdown('<div class="hist-btn">', unsafe_allow_html=True)
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
                st.markdown('</div>', unsafe_allow_html=True)

    # ── ACTIVE ALERTS ────────────────────────────────────
    st.markdown('<div class="sb-sec" style="margin-top:12px;">Active Alerts</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-item"><span class="adot adot-c"></span><span class="aname">ROUTER-LAB-01</span><span class="astatus-c">DEGRADED</span></div>
    <div class="alert-item"><span class="adot adot-c"></span><span class="aname">SW-LAB-02</span><span class="astatus-c">DOWN</span></div>
    <div class="alert-item"><span class="adot adot-c"></span><span class="aname">5G-UPF-01</span><span class="astatus-c">ERROR</span></div>
    <div class="alert-item"><span class="adot adot-w"></span><span class="aname">5G-AMF-01</span><span class="astatus-w">WARNING</span></div>
    <div class="alert-item"><span class="adot adot-w"></span><span class="aname">5G-SMF-01</span><span class="astatus-w">WARNING</span></div>
    """, unsafe_allow_html=True)

# ── TOPBAR ──────────────────────────────────────────────
tb_col, title_col, status_col = st.columns([0.4, 6, 2])

with tb_col:
    st.markdown('<div class="toggle-btn">', unsafe_allow_html=True)
    arrow = "◁" if st.session_state.sidebar_visible else "▷"
    if st.button(arrow, key="sb_toggle"):
        st.session_state.sidebar_visible = not st.session_state.sidebar_visible
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with title_col:
    st.markdown('<div style="padding:6px 0;"><span style="font-size:13px; font-weight:500; color:#e0ddd8;">Network Troubleshooting</span></div>', unsafe_allow_html=True)

with status_col:
    st.markdown('<div style="padding:6px 0; text-align:right;"><span style="font-size:11px; color:#444; font-family:\'IBM Plex Mono\',monospace;"><span style="display:inline-block; width:6px; height:6px; background:#3da05e; border-radius:50%; animation:blink 2s infinite;"></span> Live data</span></div>', unsafe_allow_html=True)

st.markdown('<hr style="border:none; border-top:1px solid #1a1a1a; margin:0 0 0;">', unsafe_allow_html=True)

# ── EMPTY STATE (suggestions) ────────────────────────────
if not st.session_state.chat_messages:
    _, center_col, _ = st.columns([1, 4, 1])
    with center_col:
        st.markdown("""
        <div class="empty-wrap">
            <div class="empty-ic">🔧</div>
            <div class="empty-t">How can I help your network?</div>
            <div class="empty-s">All syslogs, SNMP metrics, topology, and incident tickets are loaded. Ask anything about your lab.</div>
        </div>
        """, unsafe_allow_html=True)

        suggestions = [
            "What happened to ROUTER-LAB-01 between 08:10 and 08:20?",
            "What is the blast radius of the 5G UPF crash?",
            "Has this BGP drop happened before in this network?",
            "Give me a summary of all open P1 incidents",
        ]
        with st.container():
            st.markdown('<div class="sug-wrap">', unsafe_allow_html=True)
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

# ── CHAT CONVERSATION ────────────────────────────────────
else:
    _, chat_col, _ = st.columns([0.2, 8, 0.2])
    with chat_col:
        msgs_container = st.container(height=520, border=False)
        with msgs_container:
            st.markdown('<div class="chat-area">', unsafe_allow_html=True)

            for i, message in enumerate(st.session_state.chat_messages):
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="msg-user">
                        <div class="bubble-user">{message['content']}</div>
                        <div class="av-user">YOU</div>
                    </div>""", unsafe_allow_html=True)

                else:
                    # Two-column layout: avatar | content
                    av_col, content_col = st.columns([0.06, 0.94])
                    with av_col:
                        st.markdown('<div class="av-ai">🔧</div>', unsafe_allow_html=True)
                    with content_col:
                        st.markdown('<div class="bubble-ai-name">NetFix AI</div>', unsafe_allow_html=True)
                        st.markdown(message["content"])

                    if i < len(st.session_state.chat_messages) - 1:
                        st.markdown('<hr class="msg-divider">', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

# ── INPUT BAR ───────────────────────────────────────────
_, inp_col, _ = st.columns([0.2, 8, 0.2])
with inp_col:
    st.markdown('<div class="inp-outer">', unsafe_allow_html=True)
    ic, bc = st.columns([8, 1])
    with ic:
        # Pre-fill from dashboard if set
        default_val = st.session_state.pop("dashboard_query", "")
        user_input = st.text_input(
            "i",
            placeholder="Ask about any device, incident, or network issue…",
            label_visibility="collapsed",
            key="chat_input",
            value=default_val
        )
    with bc:
        send = st.button("Send ↑", use_container_width=True)

    st.markdown('<p class="footer-note">NetFix AI can make mistakes. Always verify before applying changes.</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if send and user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.spinner("NetFix AI is analysing…"):
        response = query_netfix(user_input)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()