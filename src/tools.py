import os
import sqlite3
import chromadb
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer('all-MiniLM-L6-v2')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "..", "chroma_db")

chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    collection = chroma_client.get_collection("netfix")
except Exception as e:
    raise RuntimeError("ChromaDB collection not found. Ensure chroma_db is committed and path is correct.") from e

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
        meta      = results["metadatas"][0][i]
        source    = meta.get("source",    "unknown")
        device    = meta.get("device",    "unknown")
        timestamp = meta.get("timestamp", "unknown")   # <-- was missing
        output.append(f"[{source.upper()} | {device} | {timestamp}]: {doc}")

    return "\n\n".join(output)


def metrics_query(
    device_name: str = None,
    metric_name: str = None,
    status:      str = None,
    start_time:  str = None,   # <-- added
    end_time:    str = None,   # <-- added
) -> str:
    conn   = sqlite3.connect("netfix_metrics.db")
    cursor = conn.cursor()

    query  = """
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

    # Time filter — works for both "HH:MM" and full "YYYY-MM-DD HH:MM:SS" timestamps
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
        return f"No metrics found — device={device_name}, status={status}, window={start_time}→{end_time}"

    output = []
    for row in rows:
        ts, dev, metric, val, unit, warn, crit, st = row
        # Format so LLM can read each line and reason about thresholds
        breach = ""
        if st == "CRITICAL" and crit is not None:
            try:
                diff = round(float(val) - float(crit), 2)
                breach = f" ← EXCEEDS CRIT by {diff}{unit}" if diff >= 0 else " ← RECOVERING (still flagged CRIT)"
            except (ValueError, TypeError):
                breach = " ← CRITICAL"
        elif st == "WARNING" and warn is not None:
            try:
                diff = round(float(val) - float(warn), 2)
                breach = f" ← EXCEEDS WARN by {diff}{unit}" if diff >= 0 else " ← RECOVERING (still flagged WARN)"
            except (ValueError, TypeError):
                breach = " ← WARNING"

        output.append(
            f"[{ts}] {dev} | {metric}: {val}{unit} "
            f"(WARN>{warn}, CRIT>{crit}) — {st}{breach}"
        )

    return "\n".join(output)


def get_all_critical_events(
    device_name: str = None,   # <-- added
    start_time:  str = None,   # <-- added
    end_time:    str = None,   # <-- added
) -> str:
    return metrics_query(
        device_name=device_name,
        status="CRITICAL",
        start_time=start_time,
        end_time=end_time,
    )


def get_device_status(device_name: str = None) -> str:
    """
    Returns per-device summary of which metrics are in WARNING/CRITICAL,
    with the actual metric names and peak values — not just a count.
    """
    conn   = sqlite3.connect("netfix_metrics.db")
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

    query += " GROUP BY device_name, metric_name ORDER BY device_name, status DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return "All devices are operating normally."

    # Group by device so output is readable
    from collections import defaultdict
    by_device = defaultdict(list)
    for dev, metric, peak, unit, warn, crit, st in rows:
        by_device[dev].append(
            f"  {st:8s} | {metric}: peak={peak}{unit} (WARN>{warn}, CRIT>{crit})"
        )

    output = []
    for dev, lines in by_device.items():
        output.append(f"{dev} — {len(lines)} metric(s) in alert:")
        output.extend(lines)

    return "\n".join(output)
