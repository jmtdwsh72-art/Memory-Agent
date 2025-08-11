import os, uuid, asyncio
from dotenv import load_dotenv
from zep_cloud.client import AsyncZep
from zep_cloud.types import Message

load_dotenv()
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_API_URL = os.getenv("ZEP_API_URL")

zep = AsyncZep(api_key=ZEP_API_KEY) if not ZEP_API_URL else AsyncZep(api_key=ZEP_API_KEY, api_url=ZEP_API_URL)

async def run():
    session_id = str(uuid.uuid4())
    print(f"[session] {session_id}")

    turn1 = [
        Message(role="User", role_type="user", content="My name is James. I train MMA in Leeds."),
        Message(role="Assistant", role_type="assistant", content="Nice to meet you James! Noted that you train MMA in Leeds."),
    ]
    await zep.memory.add(session_id=session_id, messages=turn1)
    print("[zep] added turn1")

    turn2 = [
        Message(role="User", role_type="user", content="I run Immortal Martial Arts and like Thai food."),
        Message(role="Assistant", role_type="assistant", content="Logged: you run Immortal Martial Arts and enjoy Thai food."),
    ]
    await zep.memory.add(session_id=session_id, messages=turn2)
    print("[zep] added turn2")

    print("\n[probe] Asking about dinner suggestions in my city...")
    await zep.memory.add(session_id=session_id, messages=[
        Message(role="User", role_type="user", content="Any good dinner suggestions in my city?")
    ])

    mem = await zep.memory.get(session_id=session_id)
    print("\n[ZEP CONTEXT]\n" + (mem.context or ""))
    print("\n(done)")

if __name__ == "__main__":
    asyncio.run(run())