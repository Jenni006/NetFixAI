import os
from dotenv import load_dotenv
from groq import Groq
from src.tools import semantic_search as _search
from src.tools import semantic_search, metrics_query, get_all_critical_events, get_device_status
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are NetFix AI, an expert network troubleshooting assistant for a telecom R&D lab.

You have access to the following data sources:
- Router syslogs from ROUTER-LAB-01, ROUTER-LAB-02 and other devices
- Device inventory with software versions and status
- Network topology showing device connections and BGP peering
- SNMP metrics with CPU, memory, packet drops, BGP session counts
- Historical incident tickets with root causes and resolutions

When answering questions you MUST:
1. Always cite specific evidence - mention exact timestamps, log lines, or metric values
2. Rank root causes by confidence level (High/Medium/Low)
3. Provide specific remediation steps with exact CLI commands where possible
4. Mention affected downstream devices and blast radius
5. Check if similar incidents occurred before and reference them
6. Be specific about device names, interface names, and protocol details

Response format:
## Root Cause Analysis
**Root Cause #1 (High Confidence):** [explanation]
*Evidence:* [cite specific log line or metric]

**Root Cause #2 (Medium Confidence):** [explanation]  
*Evidence:* [cite specific data]

## Impact Summary
- Affected devices: [list]
- Severity: [P1/P2/P3]
- Test cases blocked: [list if known]

## Remediation Steps
1. [specific step with CLI command]
2. [specific step with CLI command]

## Historical Correlation
[Reference any similar past incidents]
"""

conversation_history = []

def _truncate(text: str, max_chars: int = 1500) -> str:
    """Hard-truncate any context block to stay within token budget."""
    if len(text) > max_chars:
        return text[:max_chars] + "\n… (truncated)"
    return text

def query_netfix(user_question: str) -> str:
    global conversation_history
    
    try:
        syslog_context = _truncate(semantic_search(user_question, n_results=3))
        metrics_context = _truncate(metrics_query(), 800)
        device_status = _truncate(get_device_status(), 600)
        
        context = f"""CONTEXT:\n{syslog_context}\n\nMETRICS:\n{metrics_context}\n\nSTATUS:\n{device_status}"""

        incident_context = _truncate(_search(f"incident {user_question}", n_results=2), 800)

        conversation_history.append({
            "role": "user",
            "content": f"{user_question}\n\n{context}\n\nHISTORICAL INCIDENTS:\n{incident_context}"
        })
        
        # Keep only last 4 exchanges to avoid token buildup
        recent_history = conversation_history[-8:]
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + recent_history
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,
            max_tokens=1024
        )
        
        answer = response.choices[0].message.content
        
        conversation_history.append({
            "role": "assistant",
            "content": answer
        })
        
        return answer
    except Exception as e:
        error_msg = str(e)
        if "rate_limit" in error_msg or "413" in error_msg:
            # Clear history to free up tokens and retry
            conversation_history.clear()
            return "⚠️ Request was too large. I've cleared the conversation context — please try your question again."
        return f"⚠️ Error: {error_msg}"

def reset_conversation():
    global conversation_history
    conversation_history = []