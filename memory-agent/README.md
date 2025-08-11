# Simple Memory Agent (Claude Code + Zep Cloud)

## What this does
A tiny REPL-style agent that:
- Logs each turn of chat to **Zep Memory**
- Retrieves a **context string** from Zep each turn
- Feeds that context into your LLM call (Anthropic optional)
- Prints the retrieved memory so you can see what Zep "remembers"

This lets you quickly verify whether personal facts you share (name, gym, city, preferences) are recalled in later turns.

---

## Stack
- **Python 3.10+**
- **zep-cloud** SDK (official)
- (Optional) **Anthropic** Python SDK for live model responses

**Zep Cloud:** you only need an API key. (If a tool insists on a URL, use `https://api.getzep.com`.)  
**Self-hosted Zep:** set `ZEP_API_URL` in `.env` (e.g., `http://localhost:8000`).

---

## Project structure
memory-agent/
  ├─ README.md
  ├─ .env                   # ZEP_API_KEY=..., optional ANTHROPIC_API_KEY=...
  ├─ agent.py               # Interactive REPL agent using zep-cloud
  ├─ memory_test.py         # Scripted probe (no Anthropic required)
  └─ requirements.txt

---

## Environment & keys
Create a `.env` with:
ZEP_API_KEY=your_zep_key_here
# Optional if you want real model replies:
ANTHROPIC_API_KEY=your_anthropic_key_here
# If you're self-hosting Zep OS, uncomment and set:
# ZEP_API_URL=http://localhost:8000

---

## How memory flows (one loop)
1) You type a user message.  
2) Agent calls `memory.get(session_id)` to fetch a **context string** relevant to the session.  
3) (Optional) It calls your LLM with a system prompt + **MEMORY_CONTEXT** + a tiny recent window.  
4) After the reply, it calls `memory.add(session_id, messages=[user_msg, assistant_msg])` to store both turns in Zep (recommended single call).  
5) It prints the retrieved context so you can observe Zep's "recall."

**Notes**
- `memory.get` returns a prompt-ready context string; you can still append a short rolling window of raw messages for extra freshness.
- To exclude assistant messages from ingestion, use `ignore_roles=["assistant"]` in `memory.add(...)`.

---

## Run it
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python memory_test.py   # scripted probe
python agent.py         # interactive REPL

---

## Expected outcome
- Early runs: context is sparse.
- After adding facts: context string will reflect them in later turns.
- Demonstrates Zep's recall over multiple turns.