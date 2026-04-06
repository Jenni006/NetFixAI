import os
import sqlite3
import chromadb

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CHROMA_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "chroma_db")
)

DB_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "netfix_metrics.db")
)

# ---------- Chroma ----------
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

try:
    collection = chroma_client.get_collection("netfix")
except Exception as e:
    raise RuntimeError(
        f"ChromaDB collection not found at {CHROMA_PATH}"
    ) from e

# ---------- Lazy Load Model ----------
embedder = None

def get_embedder():
    global embedder
    if embedder is None:
        from sentence_transformers import SentenceTransformer
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
    return embedder


# ---------- Semantic Search ----------
def semantic_search(query: str, n_results: int = 5) -> str:
    query_embedding = get_embedder().encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    if not results["documents"][0]:
        return "No relevant data found."

    output = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        source = meta.get("source", "unknown")
        device = meta.get("device", "unknown")
        timestamp = meta.get("timestamp", "unknown")

        output.append(f"[{source.upper()} | {device} | {timestamp}]: {doc}")

    return "\n\n".join(output)


# ---------- Metrics Query ----------
def metrics_query(
    device_name: str = None,
    metric_name: str = None,
    status: str = None,
    start_time: str = None,
    end_time: str = None,
) -> str:

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT timestamp, device_name, metric_name,
               value, unit, warn_threshold, crit_threshold, status
        FROM metrics
        WHERE 1=1
    """

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

    if start_time:
        query += " AND timestamp >= ?"
        params.append(start_time)

    if end_time:
        query += " AND timestamp <= ?"
        params.append(end_time)

    query += " ORDER BY timestamp ASC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "No metrics found."

    output = []
    for row in rows:
        ts, dev, metric, val, unit, warn, crit, st = row

        output.append(
            f"[{ts}] {dev} | {metric}: {val}{unit} "
            f"(WARN>{warn}, CRIT>{crit}) — {st}"
        )

    return "\n".join(output)


# ---------- Critical Events ----------
def get_all_critical_events(device_name=None, start_time=None, end_time=None):
    return metrics_query(
        device_name=device_name,
        status="CRITICAL",
        start_time=start_time,
        end_time=end_time,
    )


# ---------- Device Status ----------
def get_device_status(device_name=None) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
        SELECT device_name, metric_name, MAX(value), unit,
               warn_threshold, crit_threshold, status
        FROM metrics
        WHERE status IN ('WARNING', 'CRITICAL')
    """

    params = []

    if device_name:
        query += " AND device_name LIKE ?"
        params.append(f"%{device_name}%")

    query += " GROUP BY device_name, metric_name"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "All devices are operating normally."

    from collections import defaultdict
    by_device = defaultdict(list)

    for dev, metric, peak, unit, warn, crit, st in rows:
        by_device[dev].append(
            f"{st} | {metric}: {peak}{unit}"
        )

    output = []
    for dev, lines in by_device.items():
        output.append(f"{dev}:")
        output.extend(lines)

    return "\n".join(output)