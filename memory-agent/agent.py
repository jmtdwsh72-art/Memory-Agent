import os
import asyncio
import uuid
from dotenv import load_dotenv
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message
from openai import OpenAI

# ── Config ─────────────────────────────────────────────────────────────────────
# Choose a stable user & thread so you can see data in Zep's dashboard:
USER_ID = "james-user"                     # <-- change if you like
THREAD_ID = "demo-thread"                  # <-- change if you like

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use MEMORY_CONTEXT to stay consistent with what "
    "the user has told you previously."
)

# Batch messages for non-interactive (Claude Code) runs:
BATCH_MESSAGES = [
    "My name is James.",
    "I train MMA in Leeds.",
    "I run Immortal Martial Arts.",
    "What sport do I train?",
    "Where do I train?",
    "What's the name of my gym?"
]

# ── Init clients ───────────────────────────────────────────────────────────────
load_dotenv()
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_API_URL = os.getenv("ZEP_API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not ZEP_API_KEY:
    raise RuntimeError("Missing ZEP_API_KEY in .env")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

zep = AsyncZep(api_key=ZEP_API_KEY) if not ZEP_API_URL else AsyncZep(api_key=ZEP_API_KEY, api_url=ZEP_API_URL)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ── Helpers ────────────────────────────────────────────────────────────────────
async def ensure_user_and_thread():
    """
    Zep v3 requires an explicit user and thread.
    - Create/update the user with a real name if possible (improves graph construction).
    - Create the thread bound to that user.
    """
    # Create/update user
    await zep.user.add(
        user_id=USER_ID,
        email="james@bottomley.com",
        first_name="James",
        last_name="Bottomley"
    )
    # Create thread
    await zep.thread.create(
        thread_id=THREAD_ID,
        user_id=USER_ID,
    )

async def add_turns_and_get_context(user_text: str, recent_window: list[str]) -> tuple[str, str]:
    """
    - Add user+assistant messages to the thread (assistant is added after generation)
    - Return (assistant_text, context_block)
    """
    # 1) Get context before answering (v3: thread.get_user_context)
    mem = await zep.thread.get_user_context(thread_id=THREAD_ID)
    context = mem.context if mem and getattr(mem, "context", "") else ""

    # 2) Call OpenAI with system + context + short recent window
    recent_text = "\n".join(recent_window[-6:])
    full_system = f"{SYSTEM_PROMPT}\n\nMEMORY_CONTEXT:\n{context}"
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": full_system},
            {"role": "user", "content": f"{recent_text}\nUser: {user_text}".strip()}
        ],
        max_tokens=300
    )
    assistant_text = response.choices[0].message.content

    # 3) Add both messages to the thread (v3: thread.add_messages)
    messages = [
        Message(name="James", content=user_text, role="user"),
        Message(name="AI Assistant", content=assistant_text, role="assistant"),
    ]
    await zep.thread.add_messages(thread_id=THREAD_ID, messages=messages)

    return assistant_text, context

# ── Main (batch mode for Claude Code) ──────────────────────────────────────────
async def main():
    print(f"[user_id] {USER_ID}")
    print(f"[thread_id] {THREAD_ID}")

    # Ensure user + thread exist (idempotent)
    await ensure_user_and_thread()
    print("[zep] user + thread ready ✓")

    recent_window: list[str] = []

    for user_text in BATCH_MESSAGES:
        print(f"\nYou: {user_text}")

        assistant_text, context = await add_turns_and_get_context(user_text, recent_window)

        if context:
            print("\n[ZEP CONTEXT]\n" + context + "\n")

        print(f"Assistant: {assistant_text}")
        print("[zep] thread.add_messages ✓")

        # keep a tiny local text window
        recent_window.append(f"User: {user_text}")
        recent_window.append(f"Assistant: {assistant_text}")

if __name__ == "__main__":
    asyncio.run(main())

# ── How to run ─────────────────────────────────────────────────────────────────
# 1) Make sure your .env contains:
#    ZEP_API_KEY=...
#    OPENAI_API_KEY=...
# 2) Run:
#    python agent.py
# 3) View data in the Zep Dashboard:
#    - Go to https://app.getzep.com (Dashboard)
#    - Users ▸ james-user ▸ View Graph (and View Episodes)
#    You should now see memory being added for USER_ID and THREAD_ID.