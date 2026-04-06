import os
import re
import sqlite3
from dotenv import load_dotenv
from groq import Groq
from src.tools import semantic_search as _search
from src.tools import semantic_search, metrics_query, get_all_critical_events, get_device_status

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are NetFix AI, an expert network troubleshooting assistant for a telecom R&D lab.

You have access to syslogs, SNMP metrics, device inventory, network topology, and incident tickets.

STRICT RULES:
- Never say "unknown" or "no data" if metrics are provided in context
- Every remediation step MUST reference the exact metric value and timestamp from context
- Write for a network engineer who needs to act fast — be direct, no filler sentences
- Output must use markdown: **bold** for all labels, fenced ``` code blocks for ALL CLI commands, > blockquotes for metric lines

Use EXACTLY this format (do not add ━━━ lines or any other dividers):

---
# Root Cause Analysis

**1 · High Confidence**
[One sentence: what failed and why]
> **Metric** : [metric_name]
> **At**     : [timestamp]
> **Value**  : [value] / Threshold [crit_threshold]
> **Evidence**: [exact metric line]

**2 · Medium Confidence**
[One sentence: what failed and why]
> **Metric** : [metric_name]
> **At**     : [timestamp]
> **Value**  : [value] / Threshold [crit_threshold]
> **Evidence**: [exact metric line]

---
# Impact

> **Severity**         : [P1 / P2 / P3]
> **Affected devices** : [comma separated]
> **Blast radius**     : [downstream impact]

---
# Remediation

**STEP 1 · [metric_name]: [value] exceeded [threshold] at [timestamp]**

▶ [Why this step — one sentence]
```
[exact CLI command]
```
✓ Good: [what healthy output looks like]

✗ Bad:  [what a problem looks like]

**STEP 2 · [metric_name]: [value] exceeded [threshold] at [timestamp]**

▶ [Why this step — one sentence]
```
[exact CLI command]
```
✓ Good: [what healthy output looks like]

✗ Bad:  [what a problem looks like]

---
# Historical Correlation

> **Incident**  : [incident_id] — [date] — [RESOLVED/OPEN]
> **Matched**   : [exact symptom that matched]
> **Root cause**: [root cause from that incident]

**Fix that worked:**
```
[resolution command 1]
[resolution command 2]
[resolution command 3]
```

If no match found: "No historical match — open a P1 ticket immediately."

---
"""

conversation_history = []


def _truncate(text: str, max_chars: int = 1500) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + "\n… (truncated)"
    return text


def _extract_device(question: str) -> str:
    match = re.search(r'(ROUTER-LAB-\d+|SW-LAB-\d+|5G-\w+-\d+)', question.upper())
    return match.group(0) if match else None


def _extract_time_range(question: str):
    matches = re.findall(r'\b(\d{2}:\d{2})\b', question)
    if len(matches) >= 2:
        conn = sqlite3.connect("netfix_metrics.db")
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp FROM metrics ORDER BY timestamp LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        date_prefix = row[0][:10] if row else "2024-03-15"
        return f"{date_prefix}T{matches[0]}:00Z", f"{date_prefix}T{matches[1]}:00Z"
    return None, None


def query_netfix(user_question: str) -> str:
    global conversation_history

    try:
        device = _extract_device(user_question)
        t_start, t_end = _extract_time_range(user_question)

        syslog_context = _truncate(
            semantic_search(user_question, n_results=8),
            max_chars=3000
        )
        metrics_context = _truncate(
            metrics_query(device_name=device, start_time=t_start, end_time=t_end),
            max_chars=2000
        )
        device_status = _truncate(
            get_device_status(device_name=device),
            max_chars=800
        )
        critical_events = _truncate(
            get_all_critical_events(device_name=device, start_time=t_start, end_time=t_end),
            max_chars=1500
        )
        incident_context = _truncate(
            _search(f"incident {user_question}", n_results=3),
            max_chars=1200
        )

        context_block = f"""--- RETRIEVED CONTEXT ---
DEVICE FILTER : {device or 'all devices'}
TIME WINDOW   : {t_start or 'none'} → {t_end or 'none'}

SYSLOGS:
{syslog_context}

METRICS (time-filtered):
{metrics_context}

CRITICAL EVENTS:
{critical_events}

DEVICE STATUS:
{device_status}

HISTORICAL INCIDENTS:
{incident_context}
--- END CONTEXT ---"""

        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
          + [{"role": "system", "content": context_block}]
          + conversation_history[-6:]
          + [{"role": "user", "content": user_question}]
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,
            max_tokens=1500
        )

        answer = response.choices[0].message.content
        conversation_history.append({"role": "user",      "content": user_question})
        conversation_history.append({"role": "assistant", "content": answer})
        return answer

    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg or "413" in error_msg:
            conversation_history.clear()
            return "⚠️ Request too large — context cleared. Please retry."
        return f"⚠️ Error: {error_msg}"


def reset_conversation():
    global conversation_history
    conversation_history = []