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
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&family=DM+Mono:wght@400;500&display=swap');

    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"], .main {
        background-color: #1a1a1a !important;
        font-family: 'DM Sans', sans-serif;
        color: #e8e6e0;
    }

    #MainMenu, footer, header,
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stHeader"],
    [data-testid="stSidebarNav"],
    [data-testid="stStatusWidget"] { display: none !important; }

    .block-container { padding: 1rem 2rem !important; max-width: 100% !important; }

    [data-testid="stSidebar"] {
        background-color: #111 !important;
        border-right: 1px solid #252525 !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding: 0 !important; }

    .sb-logo-row {
        display: flex; align-items: center; gap: 10px;
        padding: 18px 16px 14px;
        border-bottom: 1px solid #252525;
    }
    .sb-logo {
        width: 34px; height: 34px; background: #c96442;
        border-radius: 9px; display: flex; align-items: center;
        justify-content: center; font-size: 17px; flex-shrink: 0;
    }
    .sb-name  { font-size: 14px; font-weight: 500; color: #e8e6e0; }
    .sb-tag   { font-size: 11px; color: #4a4a4a; margin-top: 1px; }
    .sb-sec {
        padding: 14px 16px 5px;
        font-size: 10px; font-weight: 500;
        letter-spacing: 0.1em; text-transform: uppercase; color: #3a3a3a;
    }
    .ac {
        display: flex; align-items: center; gap: 9px;
        padding: 6px 16px; font-size: 12px;
    }
    .adot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .adot-c { background: #e05252; }
    .adot-w { background: #e0943a; }
    .an  { color: #bbb; }
    .as-c { color: #e05252; font-size: 10px; margin-left: auto; }
    .as-w { color: #e0943a; font-size: 10px; margin-left: auto; }

    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        color: #777 !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-weight: 400 !important;
        text-align: left !important;
        height: auto !important;
        padding: 6px 10px !important;
        white-space: normal !important;
        line-height: 1.4 !important;
        width: 100% !important;
        margin: 1px 0 !important;
        transition: all 0.12s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1c1c1c !important;
        color: #e8e6e0 !important;
    }

    [data-testid="stSidebar"] .stPageLink a {
        background: transparent !important;
        color: #777 !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        padding: 8px 12px !important;
        display: block !important;
        text-decoration: none !important;
        transition: all 0.12s !important;
    }
    [data-testid="stSidebar"] .stPageLink a:hover {
        background: #1c1c1c !important;
        color: #e8e6e0 !important;
    }

    .dash-header {
        background: #161616;
        border: 1px solid #252525;
        border-radius: 12px;
        padding: 14px 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .dash-title { font-size: 16px; font-weight: 500; color: #e8e6e0; }
    .live { width: 6px; height: 6px; background: #3da05e; border-radius: 50%; display: inline-block; animation: pulse 2s infinite; margin-right: 5px; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

    .metric-card {
        background: #161616;
        border: 1px solid #252525;
        border-radius: 10px;
        padding: 16px 20px;
    }
    .metric-label { font-size: 11px; color: #444; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
    .metric-value { font-size: 28px; font-weight: 500; color: #e8e6e0; }
    .metric-value-c { color: #e05252; }
    .metric-value-w { color: #e0943a; }

    .section-title {
        font-size: 13px; font-weight: 500; color: #888;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin: 20px 0 10px;
    }

    .device-card {
        background: #161616;
        border: 1px solid #252525;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 10px;
        cursor: pointer;
        transition: border-color 0.15s;
    }
    .device-card:hover { border-color: #c96442; }

    .incident-card {
        background: #161616;
        border: 1px solid #252525;
        border-left: 3px solid #e05252;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 6px;
    }

    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

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

inventory = load_inventory()
metrics = load_metrics()
incidents = load_incidents()

down_count = len(inventory[inventory["status"] == "DOWN"])
warning_count = len(inventory[inventory["status"].isin(["WARNING", "DEGRADED"])])
critical_count = len(inventory[inventory["status"].isin(["CRITICAL", "ERROR"])])
open_p1 = len([i for i in incidents["incidents"] if i["severity"] == "P1" and i["status"] == "OPEN"])

# ── SIDEBAR ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-logo-row">
        <div class="sb-logo">🔧</div>
        <div>
            <div class="sb-name">NetFix AI</div>
            <div class="sb-tag">Network Operations Center</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec">Navigation</div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:4px 10px;">', unsafe_allow_html=True)
    st.page_link("app.py", label="📊  Dashboard", use_container_width=True)
    st.page_link("pages/chat.py", label="💬  Chat Analyst", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="sb-sec" style="margin-top:8px;">Active Alerts</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="ac"><span class="adot adot-c"></span><span class="an">ROUTER-LAB-01</span><span class="as-c">DEGRADED</span></div>
    <div class="ac"><span class="adot adot-c"></span><span class="an">SW-LAB-02</span><span class="as-c">DOWN</span></div>
    <div class="ac"><span class="adot adot-c"></span><span class="an">5G-UPF-01</span><span class="as-c">ERROR</span></div>
    <div class="ac"><span class="adot adot-w"></span><span class="an">5G-AMF-01</span><span class="as-w">WARNING</span></div>
    <div class="ac"><span class="adot adot-w"></span><span class="an">5G-SMF-01</span><span class="as-w">WARNING</span></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-sec" style="margin-top:8px;">Quick Actions</div>', unsafe_allow_html=True)
    quick_queries = [
        "What happened to ROUTER-LAB-01 between 08:10 and 08:20?",
        "What is the blast radius of the 5G UPF crash?",
        "Has this BGP drop happened before?",
        "Give me a summary of all open P1 incidents",
    ]
    for i, q in enumerate(quick_queries):
        if st.button(q[:45] + "...", key=f"sb_q_{i}", use_container_width=True):
            st.session_state["dashboard_query"] = q
            st.switch_page("pages/chat.py")

# ── HEADER ──────────────────────────────────────────────
st.markdown(f"""
<div class="dash-header">
    <span class="dash-title">🔧 NetFix AI — Network Operations Center</span>
    <span style="font-size:12px; color:#444;">
        <span class="live"></span>Live
        &nbsp;&nbsp;
        <span style="color:#e05252;">● {down_count} DOWN</span>
        &nbsp;&nbsp;
        <span style="color:#e0943a;">● {warning_count} WARNING</span>
        &nbsp;&nbsp;
        <span style="color:#e05252;">⚠ {open_p1} P1 OPEN</span>
    </span>
</div>
""", unsafe_allow_html=True)

# ── METRIC CARDS ────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Critical Devices</div>
        <div class="metric-value metric-value-c">{critical_count}</div>
    </div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Warnings</div>
        <div class="metric-value metric-value-w">{warning_count}</div>
    </div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Down Devices</div>
        <div class="metric-value metric-value-c">{down_count}</div>
    </div>""", unsafe_allow_html=True)
with m4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Open P1 Incidents</div>
        <div class="metric-value metric-value-c">{open_p1}</div>
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
topo_network = st.selectbox("Select Network", ["ALL", "NET-LAB-ALPHA", "NET-LAB-BETA", "NET-LAB-5G"], key="topo_select", label_visibility="collapsed")
show_topology(topo_network)

# ── BOTTOM PANELS ───────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown('<div class="section-title">Device Status</div>', unsafe_allow_html=True)
    selected_network = st.selectbox("Filter", ["ALL", "NET-LAB-ALPHA", "NET-LAB-BETA", "NET-LAB-5G"], key="dev_filter", label_visibility="collapsed")
    filtered = inventory if selected_network == "ALL" else inventory[inventory["lab_network"] == selected_network]

    for _, device in filtered.iterrows():
        status = device["status"]
        if status in ["CRITICAL", "ERROR"]:
            dot = "🔴"
        elif status in ["WARNING", "DEGRADED"]:
            dot = "🟠"
        elif status == "DOWN":
            dot = "🔴"
        else:
            dot = "🟢"

        if st.button(
            f"{dot} {device['device_name']} — {status}",
            key=f"dev_{device['device_id']}",
            use_container_width=True
        ):
            st.session_state["dashboard_query"] = f"What is the current status of {device['device_name']}? Any issues?"
            st.switch_page("pages/chat.py")

with col2:
    st.markdown('<div class="section-title">Live Metrics</div>', unsafe_allow_html=True)
    latest = metrics.sort_values("timestamp").groupby(["device_name", "metric_name"]).last().reset_index()
    critical_m = latest[latest["status"].isin(["CRITICAL", "WARNING"])]

    if critical_m.empty:
        st.success("All metrics normal")
    else:
        for _, row in critical_m.iterrows():
            color = "#e05252" if row["status"] == "CRITICAL" else "#e0943a"
            st.markdown(f"""
            <div style='background:#161616; border-left:3px solid {color}; padding:10px 14px; margin:5px 0; border-radius:6px;'>
                <div style='font-size:11px; color:#444;'>{row['device_name']}</div>
                <div style='font-size:13px; color:#ccc;'>{row['metric_name']}: <b style='color:{color}'>{row['value']}{row['unit']}</b></div>
                <div style='font-size:10px; color:#333; margin-top:2px;'>{row['status']} — crit threshold: {row['crit_threshold']}</div>
            </div>
            """, unsafe_allow_html=True)

with col3:
    st.markdown('<div class="section-title">Incident Feed</div>', unsafe_allow_html=True)
    for incident in incidents["incidents"]:
        border = "#e05252" if incident["severity"] == "P1" else "#e0943a"
        status_color = "#e0943a" if incident["status"] == "OPEN" else "#3da05e"

        if st.button(
            f"[{incident['severity']}] {incident['incident_id']}",
            key=f"inc_{incident['incident_id']}",
            use_container_width=True
        ):
            st.session_state["dashboard_query"] = f"Tell me about incident {incident['incident_id']} and its current status"
            st.switch_page("pages/chat.py")

        st.markdown(f"""
        <div style='font-size:11px; color:#444; margin:-6px 0 6px 4px;'>
            {incident['title'][:50]}...
            <span style='color:{status_color}; margin-left:6px;'>{incident['status']}</span>
        </div>
        """, unsafe_allow_html=True)