import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection("netfix")

def semantic_search(query: str, n_results: int = 5) -> str:
    query_embedding = embedder.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    if not results["documents"][0]:
        return "No relevant data found."
    output = []
    for i, doc in enumerate(results["documents"][0]):
        source = results["metadatas"][0][i].get("source", "unknown")
        device = results["metadatas"][0][i].get("device", "unknown")
        output.append(f"[{source.upper()} | {device}]: {doc}")
    return "\n\n".join(output)

def metrics_query(device_name: str = None, metric_name: str = None, status: str = None) -> str:
    conn = sqlite3.connect("netfix_metrics.db")
    cursor = conn.cursor()
    query = "SELECT timestamp, device_name, metric_name, value, unit, warn_threshold, crit_threshold, status FROM metrics WHERE 1=1"
    params = []
    if device_name:
        query += " AND device_name LIKE ?"
        params.append(f"%{device_name}%")
    if metric_name:
        query += " AND metric_name LIKE ?"
        params.append(f"%{metric_name}%")
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY timestamp ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return "No metrics found for the given query."
    output = []
    for row in rows:
        output.append(f"[{row[0]}] {row[1]} | {row[2]}: {row[3]}{row[4]} (WARN>{row[5]}, CRIT>{row[6]}) — {row[7]}")
    return "\n".join(output)

def get_all_critical_events() -> str:
    return metrics_query(status="CRITICAL")

def get_device_status() -> str:
    conn = sqlite3.connect("netfix_metrics.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT device_name, status, COUNT(*) as count 
        FROM metrics 
        WHERE status IN ('WARNING', 'CRITICAL')
        GROUP BY device_name, status
        ORDER BY device_name
    """)
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        return "All devices are operating normally."
    output = []
    for row in rows:
        output.append(f"{row[0]}: {row[1]} ({row[2]} metrics affected)")
    return "\n".join(output)