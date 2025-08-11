import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from zep_cloud.client import Zep, AsyncZep
from zep_cloud.types import Message
from openai import OpenAI

# ── Config ─────────────────────────────────────────────────────────────
USER_ID = "james-user"
SYSTEM_PROMPT = (
    "You are a helpful assistant. Use MEMORY_CONTEXT to stay consistent "
    "with what the user has told you previously."
)

load_dotenv()
ZEP_API_KEY = os.getenv("ZEP_API_KEY")
ZEP_API_URL = os.getenv("ZEP_API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not ZEP_API_KEY:
    raise RuntimeError("Missing ZEP_API_KEY in .env")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")

zep = Zep(api_key=ZEP_API_KEY) if not ZEP_API_URL else Zep(api_key=ZEP_API_KEY, api_url=ZEP_API_URL)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__, static_folder="static")
CORS(app)

# ── Helpers ─────────────────────────────────────────────────────────────
def ensure_user():
    """Create or update the user profile in Zep."""
    try:
        zep.user.add(
            user_id=USER_ID,
            email="james@bottomley.com",
            first_name="James",
            last_name="Bottomley"
        )
    except Exception as e:
        # User might already exist, that's okay
        print(f"User creation note: {e}")
        pass

def create_thread():
    """Create a new thread for this user."""
    thread_id = str(uuid.uuid4())
    try:
        # First ensure user exists
        ensure_user()
        print(f"Creating thread {thread_id} for user {USER_ID}")
        result = zep.thread.create(thread_id=thread_id, user_id=USER_ID)
        print(f"Thread created successfully: {result}")
        return thread_id
    except Exception as e:
        print(f"Thread creation error: {e}")
        import traceback
        traceback.print_exc()
        raise

def get_context(thread_id: str):
    try:
        mem = zep.thread.get_user_context(thread_id=thread_id)
        return mem.context if mem and getattr(mem, "context", "") else ""
    except Exception as e:
        print(f"Context retrieval error: {e}")
        return ""

def add_messages(thread_id: str, user_text: str, assistant_text: str):
    messages = [
        Message(name="James", content=user_text, role="user"),
        Message(name="AI Assistant", content=assistant_text, role="assistant"),
    ]
    zep.thread.add_messages(thread_id=thread_id, messages=messages)

def call_openai_with_context(context: str, user_text: str) -> str:
    full_system = f"{SYSTEM_PROMPT}\n\nMEMORY_CONTEXT:\n{context}"
    resp = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": full_system},
            {"role": "user", "content": user_text}
        ],
        max_tokens=300,
    )
    return resp.choices[0].message.content

# ── Routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/start", methods=["POST"])
def api_start():
    try:
        ensure_user()
        thread_id = create_thread()
        return jsonify({"user_id": USER_ID, "thread_id": thread_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/message", methods=["POST"])
def api_message():
    try:
        data = request.json
        print(f"Received data: {data}")
        
        thread_id = data.get("thread_id")
        text = data.get("text")
        if not thread_id or not text:
            print(f"Missing data - thread_id: {thread_id}, text: {text}")
            return jsonify({"error": "Missing thread_id or text"}), 400

        print(f"Getting context for thread: {thread_id}")
        context = get_context(thread_id)
        print(f"Context retrieved: {context[:100] if context else 'None'}...")
        
        print(f"Calling OpenAI with text: {text}")
        assistant_text = call_openai_with_context(context, text)
        print(f"OpenAI response: {assistant_text}")
        
        print(f"Adding messages to Zep...")
        add_messages(thread_id, text, assistant_text)
        print(f"Messages added successfully")

        return jsonify({"assistant": assistant_text, "context": context})
    except Exception as e:
        print(f"ERROR in api_message: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/context", methods=["GET"])
def api_context():
    try:
        thread_id = request.args.get("thread_id")
        if not thread_id:
            return jsonify({"error": "Missing thread_id"}), 400
        context = get_context(thread_id)
        return jsonify({"thread_id": thread_id, "context": context})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

#

# Additional setup:
# 1) Ensure your folder structure:
#    memory-agent/
#      app/
#        static/
#          index.html   <-- your modern frontend file
#        server.py      <-- this Flask backend
# 2) In terminal:
#    pip install flask flask-cors python-dotenv openai zep-cloud
# 3) Run:
#    flask --app app/server.py run
# 4) Visit:
#    http://127.0.0.1:5000
#    Chat, and watch the context panel update with Zep memory.