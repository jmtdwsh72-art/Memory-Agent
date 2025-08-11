import os, uuid, asyncio
from dotenv import load_dotenv
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message

load_dotenv()
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_API_URL = os.getenv("ZEP_API_URL")

if not ZEP_API_KEY:
    raise RuntimeError("Missing ZEP_API_KEY in .env")

zep = AsyncZep(api_key=ZEP_API_KEY) if not ZEP_API_URL else AsyncZep(api_key=ZEP_API_KEY, api_url=ZEP_API_URL)

async def main():
    session_id = str(uuid.uuid4())
    print(f"[session] {session_id}")

    # Step 1 — Add a fact
    fact = "My favourite sport is MMA and I live in Leeds."
    await zep.memory.add(
        session_id=session_id,
        messages=[Message(role="User", role_type="user", content=fact)]
    )
    print(f"[zep] Added fact: {fact}")

    # Step 2 — Retrieve context
    mem = await zep.memory.get(session_id=session_id)
    print("\n[ZEP CONTEXT OUTPUT]")
    print(mem.context if mem and mem.context else "(no context returned)")

if __name__ == "__main__":
    asyncio.run(main())