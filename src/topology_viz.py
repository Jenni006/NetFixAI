import json
from pyvis.network import Network
import streamlit.components.v1 as components

def build_topology_map(selected_network="ALL"):
    with open("data/network_topology.json") as f:
        topology = json.load(f)

    import pandas as pd
    inventory = pd.read_csv("data/device_inventory.csv")
    status_map = dict(zip(inventory["device_name"], inventory["status"]))

    net = Network(height="500px", width="100%", bgcolor="#0e1117", font_color="white")
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=150)

    def get_color(status):
        if status in ["CRITICAL", "ERROR"]:
            return "#ff4b4b"
        elif status in ["WARNING", "DEGRADED"]:
            return "#ffa500"
        elif status == "DOWN":
            return "#ff0000"
        else:
            return "#00cc44"

    def get_size(device_type):
        if "Router" in device_type:
            return 30
        elif "Switch" in device_type:
            return 25
        elif "5G" in device_type:
            return 22
        else:
            return 18

    added_nodes = set()

    for network in topology["lab_networks"]:
        if selected_network != "ALL" and network["network_id"] != selected_network:
            continue

        for device in network["devices"]:
            name = device["device_name"]
            if name not in added_nodes:
                status = status_map.get(name, "UP")
                color = get_color(status)
                inv_row = inventory[inventory["device_name"] == name]
                device_type = inv_row["device_type"].values[0] if not inv_row.empty else "Device"
                size = get_size(device_type)
                label = f"{name}\n{status}"
                net.add_node(
                    name,
                    label=label,
                    color=color,
                    size=size,
                    title=f"{name}\nStatus: {status}\nType: {device_type}\nNetwork: {network['network_id']}",
                    borderWidth=3 if status not in ["UP"] else 1
                )
                added_nodes.add(name)

        for link in network["links"]:
            source = link["source"]
            target = link["target"]
            if source not in added_nodes or target not in added_nodes:
                continue
            if link["status"] == "DOWN":
                color = "#ff4b4b"
                dashes = True
                width = 2
            elif link["status"] == "WARNING":
                color = "#ffa500"
                dashes = False
                width = 2
            else:
                color = "#00cc44"
                dashes = False
                width = 1

            net.add_edge(
                source,
                target,
                color=color,
                dashes=dashes,
                width=width,
                title=f"{link['link_type']} | {link['bandwidth']} | {link['status']}"
            )

    net.set_options("""
    {
        "nodes": {
            "font": {"size": 11, "color": "white"},
            "shape": "dot"
        },
        "edges": {
            "smooth": {"type": "continuous"}
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100
        },
        "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
        }
    }
    """)

    html = net.generate_html()
    return html

def show_topology(selected_network="ALL"):
    html = build_topology_map(selected_network)
    components.html(html, height=520, scrolling=False)