import streamlit as st
import pandas as pd
import json
import sqlite3
from src.agent import query_netfix, reset_conversation
from src.topology_viz import show_topology
from src.predictor import predict_failures

st.set_page_config(
    page_title="NetFix AI",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Syne:wght@400;500;600;700&display=swap');

    :root {
        --bg:         #0d0d0f;
        --surface:    #13131a;
        --card:       #17171f;
        --border:     #1f1f2e;
        --border-hi:  #2a2a40;
        --accent1:    #7c3aed;
        --accent2:    #4f46e5;
        --accent3:    #2563eb;
        --glow:       rgba(124, 58, 237, 0.18);
        --glow-blue:  rgba(37, 99, 235, 0.14);
        --red:        #ef4444;
        --amber:      #f59e0b;
        --green:      #22c55e;
        --red-dim:    rgba(239,68,68,0.1);
        --amber-dim:  rgba(245,158,11,0.1);
        --green-dim:  rgba(34,197,94,0.1);
        --text-1:     #f0f0f8;
        --text-2:     #9090b0;
        --text-3:     #4a4a6a;
        --mono:       'IBM Plex Mono', monospace;
        --sans:       'Outfit', sans-serif;
        --display:    'Syne', sans-serif;
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

    .block-container { padding: 1.5rem 2rem !important; max-width: 100% !important; }

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
        padding: 18px 18px 6px;
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
        line-height: 1.4 !important;
        width: 100% !important;
        margin: 1px 0 !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--border) !important;
        color: var(--text-1) !important;
    }
    [data-testid="stSidebar"] .stPageLink a {
        background: transparent !important;
        color: var(--text-2) !important;
        border: none !important;
        border-radius: 8px !important;
        font-family: var(--sans) !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        padding: 7px 12px !important;
        display: block !important;
        text-decoration: none !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stSidebar"] .stPageLink a:hover {
        background: var(--border) !important;
        color: var(--text-1) !important;
    }

    .alert-item {
        display: flex; align-items: center; gap: 10px;
        padding: 6px 18px; font-size: 12px;
    }
    .adot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
    .adot-r { background: var(--red); box-shadow: 0 0 6px rgba(239,68,68,0.5); }
    .adot-a { background: var(--amber); box-shadow: 0 0 6px rgba(245,158,11,0.4); }
    .alert-name { color: var(--text-2); flex: 1; }
    .badge-r { font-family: var(--mono); font-size: 9px; color: var(--red); background: var(--red-dim); padding: 2px 7px; border-radius: 4px; letter-spacing: 0.04em; }
    .badge-a { font-family: var(--mono); font-size: 9px; color: var(--amber); background: var(--amber-dim); padding: 2px 7px; border-radius: 4px; letter-spacing: 0.04em; }

    /* ── DASHBOARD HEADER ─────────────────────── */
    .dash-topbar {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 14px 24px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .dash-title {
        font-family: var(--display);
        font-size: 17px; font-weight: 600; color: var(--text-1);
        letter-spacing: -0.02em;
    }
    .live-dot {
        display: inline-block; width: 7px; height: 7px;
        background: var(--green); border-radius: 50%;
        animation: pulse 2s infinite; margin-right: 6px;
        box-shadow: 0 0 8px rgba(34,197,94,0.6);
    }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.25} }
    .dash-meta { font-size: 12px; color: var(--text-3); display: flex; align-items: center; gap: 16px; font-family: var(--mono); }
    .stat-r { color: var(--red); }
    .stat-a { color: var(--amber); }

    /* ── METRIC CARDS ─────────────────────────── */
    .metric-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px 22px 18px;
        position: relative;
        overflow: hidden;
        transition: border-color 0.2s ease, box-shadow 0.2s ease;
        height: 110px;
    }
    .metric-card:hover {
        border-color: var(--border-hi);
        box-shadow: 0 0 24px var(--glow);
    }
    .metric-card::before {
        content: '';
        position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, var(--accent1), var(--accent3));
        opacity: 0;
        transition: opacity 0.2s ease;
    }
    .metric-card:hover::before { opacity: 1; }
    .m-label {
        font-family: var(--mono); font-size: 9.5px; font-weight: 500;
        letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-3);
        margin-bottom: 10px;
    }
    .m-value { font-family: var(--display); font-size: 36px; font-weight: 700; color: var(--text-1); line-height: 1; }
    .m-value-r { color: var(--red); text-shadow: 0 0 20px rgba(239,68,68,0.3); }
    .m-value-a { color: var(--amber); text-shadow: 0 0 20px rgba(245,158,11,0.25); }

    /* ── SECTION HEADERS ──────────────────────── */
    .sec-head {
        font-family: var(--mono); font-size: 10px; font-weight: 500;
        letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-3);
        margin: 28px 0 12px;
        display: flex; align-items: center; gap: 10px;
    }
    .sec-head::after {
        content: ''; flex: 1; height: 1px; background: var(--border);
    }

    /* ── PREDICTIVE ALERT BANNERS ─────────────── */
    .pred-alert {
        background: rgba(245,158,11,0.07);
        border: 1px solid rgba(245,158,11,0.22);
        border-left: 3px solid var(--amber);
        border-radius: 10px;
        padding: 11px 16px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #fcd34d;
        display: flex; align-items: center; gap: 10px;
    }

    /* ── TOPOLOGY CONTAINER ───────────────────── */
    .topo-wrap {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }
    .topo-ctrl {
        padding: 12px 16px;
        border-bottom: 1px solid var(--border);
        display: flex; align-items: center; gap: 12px;
    }

    /* ── BOTTOM PANEL CARDS ───────────────────── */
    .panel-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
        height: 360px;
    }
    .panel-head {
        padding: 12px 16px;
        border-bottom: 1px solid var(--border);
        font-family: var(--mono); font-size: 10px; font-weight: 500;
        letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-3);
        display: flex; align-items: center; justify-content: space-between;
    }
    .panel-body { padding: 10px 12px; overflow-y: auto; max-height: 310px; }
    .panel-body::-webkit-scrollbar { width: 3px; }
    .panel-body::-webkit-scrollbar-track { background: transparent; }
    .panel-body::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 10px; }

    /* Device rows */
    [data-testid="stVerticalBlock"] .stButton > button.device-btn {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        color: var(--text-2) !important;
        font-family: var(--sans) !important;
        font-size: 12.5px !important;
        text-align: left !important;
        padding: 8px 10px !important;
        width: 100% !important;
        margin: 2px 0 !important;
        transition: all 0.15s ease !important;
    }

    /* Live metric row */
    .metric-row {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 9px;
        padding: 10px 14px;
        margin-bottom: 7px;
        display: flex; flex-direction: column; gap: 3px;
    }
    .metric-row:last-child { margin-bottom: 0; }
    .mr-device { font-family: var(--mono); font-size: 10px; color: var(--text-3); }
    .mr-name   { font-size: 13px; font-weight: 500; color: var(--text-2); }
    .mr-val-r  { color: var(--red);   font-family: var(--mono); font-size: 15px; font-weight: 500; }
    .mr-val-a  { color: var(--amber); font-family: var(--mono); font-size: 15px; font-weight: 500; }
    .mr-thresh { font-family: var(--mono); font-size: 10px; color: var(--text-3); }

    /* Incident row */
    .inc-row {
        background: var(--surface);
        border: 1px solid var(--border);
        border-left: 3px solid var(--red);
        border-radius: 9px;
        padding: 10px 14px;
        margin-bottom: 7px;
        cursor: pointer;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .inc-row:hover { border-color: var(--accent1); box-shadow: 0 0 12px var(--glow); }
    .inc-row-p2 { border-left-color: var(--amber); }
    .inc-title  { font-size: 12.5px; color: var(--text-2); margin-top: 2px; }
    .inc-meta   { display: flex; align-items: center; gap: 8px; margin-top: 5px; }
    .sev-badge  {
        font-family: var(--mono); font-size: 9px; font-weight: 500;
        padding: 2px 7px; border-radius: 4px; letter-spacing: 0.05em;
    }
    .sev-p1 { color: var(--red);   background: var(--red-dim); }
    .sev-p2 { color: var(--amber); background: var(--amber-dim); }
    .status-open  { font-family: var(--mono); font-size: 9px; color: var(--amber); }
    .status-close { font-family: var(--mono); font-size: 9px; color: var(--green); }

    /* Streamlit selectbox override */
    .stSelectbox > div > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 9px !important;
        color: var(--text-2) !important;
        font-family: var(--sans) !important;
        font-size: 13px !important;
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── DATA ────────────────────────────────────────────────────────────────────────
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

# ── SIDEBAR ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-header">
        <div class="sb-logo-row">
            <div class="sb-logo">⬡</div>
            <div>
                <div class="sb-name">NetFix AI</div>
                <div class="sb-tag">NOC · v2.4.1</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:2px 10px;">', unsafe_allow_html=True)
    st.page_link("app.py",        label="◈  Dashboard",    use_container_width=True)
    st.page_link("pages/chat.py", label="◎  Chat Analyst", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Active Alerts</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-item"><span class="adot adot-r"></span><span class="alert-name">ROUTER-LAB-01</span><span class="badge-r">DEGRADED</span></div>
    <div class="alert-item"><span class="adot adot-r"></span><span class="alert-name">SW-LAB-02</span><span class="badge-r">DOWN</span></div>
    <div class="alert-item"><span class="adot adot-r"></span><span class="alert-name">5G-UPF-01</span><span class="badge-r">ERROR</span></div>
    <div class="alert-item"><span class="adot adot-a"></span><span class="alert-name">5G-AMF-01</span><span class="badge-a">WARNING</span></div>
    <div class="alert-item"><span class="adot adot-a"></span><span class="alert-name">5G-SMF-01</span><span class="badge-a">WARNING</span></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Quick Queries</div>', unsafe_allow_html=True)
    quick_queries = [
        "What happened to ROUTER-LAB-01 between 08:10 and 08:20?",
        "What is the blast radius of the 5G UPF crash?",
        "Has this BGP drop happened before?",
        "Give me a summary of all open P1 incidents",
    ]
    for i, q in enumerate(quick_queries):
        if st.button(q[:46] + "…", key=f"sb_q_{i}", use_container_width=True):
            st.session_state["dashboard_query"] = q
            st.switch_page("pages/chat.py")

# ── DASHBOARD HEADER ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="dash-topbar">
    <span class="dash-title">⬡ NetFix AI — Network Operations Center</span>
    <span class="dash-meta">
        <span><span class="live-dot"></span>Live</span>
        <span class="stat-r">▲ {down_count} DOWN</span>
        <span class="stat-a">▲ {warning_count} WARNING</span>
        <span class="stat-r">⚑ {open_p1} P1 OPEN</span>
    </span>
</div>
""", unsafe_allow_html=True)

# ── METRIC CARDS ─────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="m-label">Critical Devices</div>
        <div class="m-value m-value-r">{critical_count}</div>
    </div>""", unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="m-label">Warnings</div>
        <div class="m-value m-value-a">{warning_count}</div>
    </div>""", unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="m-label">Down Devices</div>
        <div class="m-value m-value-r">{down_count}</div>
    </div>""", unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="m-label">Open P1 Incidents</div>
        <div class="m-value m-value-r">{open_p1}</div>
    </div>""", unsafe_allow_html=True)

# ── PREDICTIVE ALERTS ────────────────────────────────────────────────────────────
try:
    predictions = predict_failures()
    if predictions:
        st.markdown('<div class="sec-head">Predictive Alerts</div>', unsafe_allow_html=True)
        for pred in predictions:
            st.markdown(f'<div class="pred-alert">⚠ {pred["message"]}</div>', unsafe_allow_html=True)
except:
    pass

# ── NETWORK TOPOLOGY ──────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">Network Topology</div>', unsafe_allow_html=True)
st.markdown('<div class="topo-wrap">', unsafe_allow_html=True)
topo_network = st.selectbox(
    "Network", ["ALL", "NET-LAB-ALPHA", "NET-LAB-BETA", "NET-LAB-5G"],
    key="topo_select", label_visibility="collapsed"
)
show_topology(topo_network)
st.markdown('</div>', unsafe_allow_html=True)

# ── BOTTOM PANELS ─────────────────────────────────────────────────────────────────
st.markdown('<div class="sec-head">Live Monitoring</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])

# ── Device Status ──────────────────────────────────────────────────────────────
with col1:
    st.markdown("""
    <div class="panel-card">
        <div class="panel-head">
            <span>Device Status</span>
        </div>
    """, unsafe_allow_html=True)

    net_filter = st.selectbox(
        "Filter", ["ALL", "NET-LAB-ALPHA", "NET-LAB-BETA", "NET-LAB-5G"],
        key="dev_filter", label_visibility="collapsed"
    )
    filtered = inventory if net_filter == "ALL" else inventory[inventory["lab_network"] == net_filter]

    st.markdown('<div class="panel-body">', unsafe_allow_html=True)
    for _, device in filtered.iterrows():
        status = device["status"]
        if status in ["CRITICAL", "ERROR", "DOWN"]:
            dot = "🔴"
        elif status in ["WARNING", "DEGRADED"]:
            dot = "🟠"
        else:
            dot = "🟢"

        if st.button(
            f"{dot}  {device['device_name']}  —  {status}",
            key=f"dev_{device['device_id']}",
            use_container_width=True
        ):
            st.session_state["dashboard_query"] = f"What is the current status of {device['device_name']}? Any issues?"
            st.switch_page("pages/chat.py")
    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Live Metrics ───────────────────────────────────────────────────────────────
with col2:
    st.markdown("""
    <div class="panel-card">
        <div class="panel-head"><span>Live Metrics</span><span style="color:var(--green);font-size:8px;">● STREAMING</span></div>
        <div class="panel-body">
    """, unsafe_allow_html=True)

    latest   = metrics.sort_values("timestamp").groupby(["device_name", "metric_name"]).last().reset_index()
    critical_m = latest[latest["status"].isin(["CRITICAL", "WARNING"])]

    if critical_m.empty:
        st.markdown('<div style="text-align:center;color:var(--green);padding:40px 0;font-size:13px;">✓ All metrics nominal</div>', unsafe_allow_html=True)
    else:
        for _, row in critical_m.iterrows():
            val_cls  = "mr-val-r" if row["status"] == "CRITICAL" else "mr-val-a"
            bar_col  = "#ef4444" if row["status"] == "CRITICAL" else "#f59e0b"
            st.markdown(f"""
            <div class="metric-row" style="border-left: 3px solid {bar_col};">
                <div class="mr-device">{row['device_name']}</div>
                <div style="display:flex;align-items:baseline;justify-content:space-between;">
                    <div class="mr-name">{row['metric_name']}</div>
                    <div class="{val_cls}">{row['value']}{row['unit']}</div>
                </div>
                <div class="mr-thresh">crit threshold → {row['crit_threshold']}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div></div>', unsafe_allow_html=True)

# ── Incident Feed ─────────────────────────────────────────────────────────────
with col3:
    st.markdown("""
    <div class="panel-card">
        <div class="panel-head"><span>Incident Feed</span></div>
        <div class="panel-body">
    """, unsafe_allow_html=True)

    for incident in incidents["incidents"]:
        sev_cls  = "sev-p1" if incident["severity"] == "P1" else "sev-p2"
        row_cls  = "inc-row" if incident["severity"] == "P1" else "inc-row inc-row-p2"
        stat_cls = "status-open" if incident["status"] == "OPEN" else "status-close"

        if st.button(
            f"[{incident['severity']}] {incident['incident_id']} — {incident['title'][:36]}…",
            key=f"inc_{incident['incident_id']}",
            use_container_width=True
        ):
            st.session_state["dashboard_query"] = f"Tell me about incident {incident['incident_id']} and its current status"
            st.switch_page("pages/chat.py")

    st.markdown('</div></div>', unsafe_allow_html=True)