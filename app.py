import streamlit as st
import pandas as pd
import json
import sqlite3
from src.agent import query_netfix, reset_conversation
from src.topology_viz import show_topology
from src.predictor import predict_failures

st.set_page_config(
    page_title="NetFix AI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

    /* ── RESET & BASE ── */
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

    .block-container { padding: 0 2rem 2rem !important; max-width: 100% !important; }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid #1e1e1e !important;
        width: 240px !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

    /* ── SIDEBAR LOGO ── */
    .sb-logo-row {
        display: flex; align-items: center; gap: 12px;
        padding: 22px 18px 18px;
        border-bottom: 1px solid #1e1e1e;
        margin-bottom: 8px;
    }
    .sb-logo {
        width: 36px; height: 36px;
        background: #bf5c38;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; flex-shrink: 0;
    }
    .sb-name  { font-size: 13px; font-weight: 600; color: #e0ddd8; letter-spacing: -0.01em; }
    .sb-tag   { font-size: 11px; color: #444; margin-top: 1px; font-family: 'IBM Plex Mono', monospace; }

    /* ── SIDEBAR SECTION LABEL ── */
    .sb-sec {
        padding: 14px 18px 6px;
        font-size: 10px; font-weight: 600;
        letter-spacing: 0.12em; text-transform: uppercase; color: #333;
        font-family: 'IBM Plex Mono', monospace;
    }

    /* ── SIDEBAR NAV BUTTONS ── */
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
        background: #161616 !important;
        color: #e0ddd8 !important;
    }

    [data-testid="stSidebar"] .stPageLink a {
        background: transparent !important;
        color: #666 !important;
        border: none !important;
        border-radius: 6px !important;
        font-size: 13px !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        padding: 7px 12px !important;
        display: block !important;
        text-decoration: none !important;
        transition: all 0.1s !important;
        margin: 1px 0 !important;
    }
    [data-testid="stSidebar"] .stPageLink a:hover {
        background: #161616 !important;
        color: #e0ddd8 !important;
    }

    /* ── ALERT CHIPS ── */
    .alert-item {
        display: flex; align-items: center; gap: 10px;
        padding: 6px 18px; font-size: 12px;
        border-left: 2px solid transparent;
        transition: border-color 0.15s;
    }
    .alert-item:hover { border-left-color: #333; }
    .adot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .adot-c { background: #e05252; }
    .adot-w { background: #d4943a; }
    .aname  { color: #888; flex: 1; font-family: 'IBM Plex Mono', monospace; font-size: 11px; }
    .astatus-c { color: #e05252; font-size: 10px; font-family: 'IBM Plex Mono', monospace; font-weight: 500; }
    .astatus-w { color: #d4943a; font-size: 10px; font-family: 'IBM Plex Mono', monospace; font-weight: 500; }

    /* ── MAIN HEADER ── */
    .dash-header {
        background: #0d0d0d;
        border-bottom: 1px solid #1e1e1e;
        padding: 16px 0 14px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .dash-title {
        font-size: 14px; font-weight: 500; color: #e0ddd8;
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .dash-status { display: flex; align-items: center; gap: 16px; font-size: 12px; font-family: 'IBM Plex Mono', monospace; }
    .live-dot { width: 6px; height: 6px; background: #3da05e; border-radius: 50%;
        display: inline-block; animation: blink 2s infinite; margin-right: 4px; }
    @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

    /* ── METRIC CARDS ── */
    .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 28px; }
    .metric-card {
        background: #111;
        border: 1px solid #1e1e1e;
        border-radius: 8px;
        padding: 18px 20px;
    }
    .metric-label {
        font-size: 10px; color: #3a3a3a; text-transform: uppercase;
        letter-spacing: 0.1em; margin-bottom: 8px;
        font-family: 'IBM Plex Mono', monospace;
    }
    .metric-value { font-size: 32px; font-weight: 300; color: #e0ddd8; line-height: 1; }
    .metric-value.red { color: #e05252; }
    .metric-value.amber { color: #d4943a; }
    .metric-sub { font-size: 11px; color: #333; margin-top: 6px; font-family: 'IBM Plex Mono', monospace; }

    /* ── SECTION TITLES ── */
    .section-title {
        font-size: 10px; font-weight: 600; color: #333;
        text-transform: uppercase; letter-spacing: 0.12em;
        margin: 20px 0 10px;
        font-family: 'IBM Plex Mono', monospace;
        padding-bottom: 6px;
        border-bottom: 1px solid #1a1a1a;
    }

    /* ── DEVICE LIST ── */
    [data-testid="stVerticalBlock"] .stButton > button {
        background: #111 !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 6px !important;
        color: #999 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 12px !important;
        text-align: left !important;
        padding: 8px 12px !important;
        height: auto !important;
        line-height: 1.4 !important;
        margin-bottom: 4px !important;
        transition: border-color 0.1s, color 0.1s !important;
    }
    [data-testid="stVerticalBlock"] .stButton > button:hover {
        border-color: #bf5c38 !important;
        color: #e0ddd8 !important;
        background: #131313 !important;
    }

    /* ── METRIC ROW (live) ── */
    .live-metric {
        background: #111;
        border: 1px solid #1e1e1e;
        border-left: 2px solid #e05252;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 5px;
    }
    .live-metric.amber { border-left-color: #d4943a; }
    .lm-device { font-size: 10px; color: #333; font-family: 'IBM Plex Mono', monospace; margin-bottom: 3px; }
    .lm-metric { font-size: 13px; color: #bbb; }
    .lm-val-r { color: #e05252; font-weight: 600; }
    .lm-val-w { color: #d4943a; font-weight: 600; }
    .lm-thresh { font-size: 10px; color: #2a2a2a; margin-top: 3px; font-family: 'IBM Plex Mono', monospace; }

    /* ── INCIDENT FEED ── */
    .inc-label {
        display: inline-block; padding: 2px 7px;
        border-radius: 4px; font-size: 10px; font-weight: 600;
        font-family: 'IBM Plex Mono', monospace;
        margin-right: 6px;
    }
    .inc-p1 { background: rgba(224,82,82,.15); color: #e05252; }
    .inc-p2 { background: rgba(212,148,58,.15); color: #d4943a; }
    .inc-title { font-size: 12px; color: #666; }
    .inc-status-open  { color: #e05252; font-size: 10px; font-family: 'IBM Plex Mono', monospace; }
    .inc-status-closed{ color: #3da05e; font-size: 10px; font-family: 'IBM Plex Mono', monospace; }

    /* ── SELECT BOXES ── */
    .stSelectbox > div > div {
        background: #111 !important;
        border: 1px solid #1e1e1e !important;
        border-radius: 6px !important;
        color: #888 !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 12px !important;
    }

    /* scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #222; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── DATA LOADERS ────────────────────────────────────────
@st.cache_data
def load_inventory():
    return pd.read_csv("data/device_inventory.csv")

@st.cache_data
def load_metrics():
    conn = sqlite3.connect("netfix_metrics.db")
    df = pd.read_sql("SELECT * FROM metrics", conn)
    conn.close()
    return df

@st.cache_data
def load_incidents():
    with open("data/incident_tickets.json") as f:
        return json.load(f)

inventory  = load_inventory()
metrics    = load_metrics()
incidents  = load_incidents()

down_count     = len(inventory[inventory["status"] == "DOWN"])
warning_count  = len(inventory[inventory["status"].isin(["WARNING", "DEGRADED"])])
critical_count = len(inventory[inventory["status"].isin(["CRITICAL", "ERROR"])])
open_p1        = len([i for i in incidents["incidents"] if i["severity"] == "P1" and i["status"] == "OPEN"])

# ── SIDEBAR ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo-row">
        <div class="sb-logo">🔧</div>
        <div>
            <div class="sb-name">NetFix AI</div>
            <div class="sb-tag">netfix v2.1</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Navigation</div>', unsafe_allow_html=True)
    with st.container():
        st.page_link("app.py",         label="Dashboard",     use_container_width=True)
        st.page_link("pages/chat.py",  label="Chat Analyst",  use_container_width=True)

    st.markdown('<div class="sb-sec" style="margin-top:10px;">Active Alerts</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-item"><span class="adot adot-c"></span><span class="aname">ROUTER-LAB-01</span><span class="astatus-c">DEGRADED</span></div>
    <div class="alert-item"><span class="adot adot-c"></span><span class="aname">SW-LAB-02</span><span class="astatus-c">DOWN</span></div>
    <div class="alert-item"><span class="adot adot-c"></span><span class="aname">5G-UPF-01</span><span class="astatus-c">ERROR</span></div>
    <div class="alert-item"><span class="adot adot-w"></span><span class="aname">5G-AMF-01</span><span class="astatus-w">WARNING</span></div>
    <div class="alert-item"><span class="adot adot-w"></span><span class="aname">5G-SMF-01</span><span class="astatus-w">WARNING</span></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec" style="margin-top:10px;">Quick Actions</div>', unsafe_allow_html=True)
    quick_queries = [
        "What happened to ROUTER-LAB-01 between 08:10 and 08:20?",
        "What is the blast radius of the 5G UPF crash?",
        "Has this BGP drop happened before?",
        "Give me a summary of all open P1 incidents",
    ]
    with st.container():
        for i, q in enumerate(quick_queries):
            if st.button(q[:45] + "…", key=f"sb_q_{i}", use_container_width=True):
                st.session_state["dashboard_query"] = q
                st.switch_page("pages/chat.py")

# ── HEADER ──────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <span class="dash-title">Network Operations Center</span>
    <span class="dash-status">
        <span class="live-dot"></span>Live
        &nbsp;&nbsp;|&nbsp;&nbsp;
        <span style="color:#e05252;">{down_count} DOWN</span>
        &nbsp;&nbsp;
        <span style="color:#d4943a;">{warning_count} WARN</span>
        &nbsp;&nbsp;
        <span style="color:#e05252;">⚠ {open_p1} P1</span>
    </span>
</div>
""", unsafe_allow_html=True)

# ── METRIC CARDS ────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
cards = [
    (m1, "Critical Devices", critical_count, "red",  "CRITICAL / ERROR"),
    (m2, "Warnings",         warning_count,  "amber", "WARNING / DEGRADED"),
    (m3, "Down Devices",     down_count,     "red",  "NO RESPONSE"),
    (m4, "Open P1 Incidents",open_p1,        "red",  "SEVERITY P1"),
]
for col, label, val, cls, sub in cards:
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value {cls}">{val}</div>
            <div class="metric-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

# ── PREDICTIVE ALERTS ───────────────────────────────────
try:
    predictions = predict_failures()
    if predictions:
        st.markdown('<div class="section-title">Predictive Alerts</div>', unsafe_allow_html=True)
        for pred in predictions:
            st.warning(f"⚠ {pred['message']}")
except:
    pass

# ── TOPOLOGY ────────────────────────────────────────────
st.markdown('<div class="section-title">Network Topology</div>', unsafe_allow_html=True)
topo_network = st.selectbox(
    "Network", ["ALL","NET-LAB-ALPHA","NET-LAB-BETA","NET-LAB-5G"],
    key="topo_select", label_visibility="collapsed"
)
show_topology(topo_network)

# ── BOTTOM PANELS ───────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown('<div class="section-title">Device Status</div>', unsafe_allow_html=True)
    selected_network = st.selectbox(
        "Filter", ["ALL","NET-LAB-ALPHA","NET-LAB-BETA","NET-LAB-5G"],
        key="dev_filter", label_visibility="collapsed"
    )
    filtered = inventory if selected_network == "ALL" else inventory[inventory["lab_network"] == selected_network]
    for _, device in filtered.iterrows():
        status = device["status"]
        dot = "●" if status in ["CRITICAL","ERROR","DOWN"] else "◉"
        color = "🔴" if status in ["CRITICAL","ERROR","DOWN"] else "🟠"
        if st.button(f"{color}  {device['device_name']}  —  {status}", key=f"dev_{device['device_id']}", use_container_width=True):
            st.session_state["dashboard_query"] = f"What is the current status of {device['device_name']}? Any issues?"
            st.switch_page("pages/chat.py")

with col2:
    st.markdown('<div class="section-title">Live Metrics</div>', unsafe_allow_html=True)
    latest   = metrics.sort_values("timestamp").groupby(["device_name","metric_name"]).last().reset_index()
    critical_m = latest[latest["status"].isin(["CRITICAL","WARNING"])]
    if critical_m.empty:
        st.markdown('<div style="font-size:13px; color:#3da05e; padding:10px 0;">✓ All metrics normal</div>', unsafe_allow_html=True)
    else:
        for _, row in critical_m.iterrows():
            is_crit = row["status"] == "CRITICAL"
            cls = "" if is_crit else " amber"
            val_cls = "lm-val-r" if is_crit else "lm-val-w"
            st.markdown(f"""
            <div class="live-metric{cls}">
                <div class="lm-device">{row['device_name']}</div>
                <div class="lm-metric">{row['metric_name']}: <span class="{val_cls}">{row['value']}{row['unit']}</span></div>
                <div class="lm-thresh">CRIT THRESH: {row['crit_threshold']}</div>
            </div>""", unsafe_allow_html=True)

with col3:
    st.markdown('<div class="section-title">Incident Feed</div>', unsafe_allow_html=True)
    for incident in incidents["incidents"]:
        sev   = incident["severity"]
        badge = f'<span class="inc-label inc-p1">{sev}</span>' if sev == "P1" else f'<span class="inc-label inc-p2">{sev}</span>'
        st_cls = "inc-status-open" if incident["status"] == "OPEN" else "inc-status-closed"
        if st.button(f"[{sev}] {incident['incident_id']}", key=f"inc_{incident['incident_id']}", use_container_width=True):
            st.session_state["dashboard_query"] = f"Tell me about incident {incident['incident_id']} and its current status"
            st.switch_page("pages/chat.py")
        st.markdown(f"""
        <div style="font-size:11px; color:#444; margin:-4px 0 8px 4px; line-height:1.5; font-family:'IBM Plex Mono',monospace;">
            {badge}
            <span class="inc-title">{incident['title'][:48]}…</span>
            <span class="{st_cls}" style="float:right;">{incident['status']}</span>
        </div>""", unsafe_allow_html=True)