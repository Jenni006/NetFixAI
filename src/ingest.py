import os
import json
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
import sqlite3

print("Loading embedding model...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

chroma_client = chromadb.PersistentClient(path="./chroma_db")

try:
    chroma_client.delete_collection("netfix")
except:
    pass

collection = chroma_client.create_collection("netfix")

documents = []
metadatas = []
ids = []

print("Ingesting syslog...")
with open("data/router_syslog.log", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    line = line.strip()
    if not line:
        continue
    parts = line.split("|")
    if len(parts) >= 3:
        timestamp = parts[0].strip().split(" ")[0]
        severity = parts[0].strip().split("[")[1].replace("]", "").strip() if "[" in parts[0] else "INFO"
        device = parts[1].strip()
        event = parts[2].strip()
        extra = parts[3].strip() if len(parts) > 3 else ""
        text = f"At {timestamp}, device {device} had a {severity} event: {event}. {extra}"
        documents.append(text)
        metadatas.append({"source": "syslog", "device": device, "severity": severity, "timestamp": timestamp})
        ids.append(f"syslog_{i}")

print("Ingesting device inventory...")
df_inventory = pd.read_csv("data/device_inventory.csv")
for i, row in df_inventory.iterrows():
    text = f"Device {row['device_name']} is a {row['device_type']} made by {row['vendor']}, model {row['model']}, running software version {row['sw_version']}. IP address is {row['ip_address']}. Current status is {row['status']}. Located in {row['rack_location']} on network {row['lab_network']}. Last seen at {row['last_seen']}."
    documents.append(text)
    metadatas.append({"source": "inventory", "device": row['device_name'], "status": row['status'], "lab_network": row['lab_network']})
    ids.append(f"inventory_{i}")

print("Ingesting network topology...")
with open("data/network_topology.json", "r") as f:
    topology = json.load(f)

for network in topology["lab_networks"]:
    network_id = network["network_id"]
    desc = network["description"]
    text = f"Network {network_id}: {desc}. Contains devices: {', '.join([d['device_name'] for d in network['devices']])}."
    documents.append(text)
    metadatas.append({"source": "topology", "network": network_id, "device": "ALL"})
    ids.append(f"topology_network_{network_id}")

    for link in network["links"]:
        text = f"In {network_id}, {link['source']} connects to {link['target']} via {link['link_type']} link. Source interface: {link['interface_source']}, Target interface: {link['interface_target']}. Bandwidth: {link['bandwidth']}. Protocols: {', '.join(link['protocols']) if link['protocols'] else 'none'}. Link status: {link['status']}."
        documents.append(text)
        metadatas.append({"source": "topology", "network": network_id, "device": link['source']})
        ids.append(f"topology_link_{link['link_id']}")

    if "bgp_peers" in network:
        for peer in network["bgp_peers"]:
            text = f"BGP peering in {network_id}: {peer['device']} peers with {peer['peer_device']} at IP {peer['peer_ip']}. Local ASN: {peer['asn_local']}, Peer ASN: {peer['asn_peer']}. Hold timer: {peer['hold_timer']}s. Status: {peer['status']}."
            documents.append(text)
            metadatas.append({"source": "topology", "network": network_id, "device": peer['device']})
            ids.append(f"topology_bgp_{peer['device']}_{peer['peer_device']}")

print("Ingesting incident tickets...")
with open("data/incident_tickets.json", "r") as f:
    tickets = json.load(f)

for i, incident in enumerate(tickets["incidents"]):
    timeline_text = " | ".join([f"{e['time']}: {e['event']}" for e in incident.get("timeline", [])])
    alerts_text   = ", ".join(incident.get("alerts_triggered", []))
    similar_text  = ", ".join(incident.get("similar_incidents", [])) or "none"
    devices_text  = ", ".join(incident.get("affected_devices", []))
    blocked_text  = ", ".join(incident.get("test_cases_blocked", [])) or "none"
    commands_text = ", ".join(incident.get("resolution_commands", [])) or "none"

    text = (
        f"Incident {incident['incident_id']}: {incident['title']}. "
        f"Severity: {incident['severity']}. Status: {incident['status']}. "
        f"Network: {incident['lab_network']}. "
        f"Affected devices: {devices_text}. "
        f"Symptoms: {incident['symptom_description']}. "
        f"Root cause: {incident['root_cause']}. "
        f"Resolution: {incident.get('resolution') or 'Not yet resolved'}. "
        f"Resolution commands: {commands_text}. "
        f"Alerts triggered: {alerts_text}. "
        f"Test cases blocked: {blocked_text}. "
        f"Similar incidents: {similar_text}. "
        f"Timeline: {timeline_text}."
    )

    documents.append(text)
    metadatas.append({
        "source":      "incident",
        "incident_id": incident["incident_id"],
        "severity":    incident["severity"],
        "status":      incident["status"],
        "device":      incident["affected_devices"][0] if incident["affected_devices"] else "unknown"
    })
    ids.append(f"incident_{i}")

print(f"Embedding {len(documents)} documents...")
embeddings = embedder.encode(documents).tolist()

print("Storing in ChromaDB...")
batch_size = 50
for i in range(0, len(documents), batch_size):
    collection.add(
        documents=documents[i:i+batch_size],
        embeddings=embeddings[i:i+batch_size],
        metadatas=metadatas[i:i+batch_size],
        ids=ids[i:i+batch_size]
    )

print("Setting up SQLite for SNMP metrics...")
conn = sqlite3.connect("netfix_metrics.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        device_id TEXT,
        device_name TEXT,
        metric_name TEXT,
        value REAL,
        unit TEXT,
        warn_threshold REAL,
        crit_threshold REAL,
        status TEXT
    )
''')

df_metrics = pd.read_csv("data/snmp_metrics.csv")
df_metrics.to_sql("metrics", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print("Done! All data ingested successfully.")
print(f"Total documents in ChromaDB: {collection.count()}")