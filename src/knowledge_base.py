import json
import os
from datetime import datetime

KB_FILE = "data/knowledge_base.json"

def load_kb():
    if not os.path.exists(KB_FILE):
        return {"entries": []}
    with open(KB_FILE) as f:
        return json.load(f)

def save_to_kb(device: str, symptoms: str, root_cause: str, resolution: str, commands: list = []):
    kb = load_kb()
    entry = {
        "id": f"KB-{len(kb['entries'])+1:03d}",
        "timestamp": datetime.now().isoformat(),
        "device": device,
        "symptoms": symptoms,
        "root_cause": root_cause,
        "resolution": resolution,
        "commands": commands
    }
    kb["entries"].append(entry)
    with open(KB_FILE, "w") as f:
        json.dump(kb, f, indent=2)
    return entry["id"]

def search_kb(query: str):
    kb = load_kb()
    query_lower = query.lower()
    matches = []
    for entry in kb["entries"]:
        if (query_lower in entry["symptoms"].lower() or
            query_lower in entry["root_cause"].lower() or
            query_lower in entry["device"].lower()):
            matches.append(entry)
    return matches

def get_all_kb():
    return load_kb()["entries"]