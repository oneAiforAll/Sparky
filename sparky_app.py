# sparky_app.py - production-ready Flask app for Sparky (Abacus ChatLLM agent)
# Usage: set ABACUS_API_KEY and ABACUS_AGENT_ID as environment variables before running.

import os
import logging
import uuid
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, make_response
import requests

app = Flask(__name__)

# Config (via environment variables) - NEVER commit secrets to git
ABACUS_API_KEY = os.environ.get("ABACUS_API_KEY", "")
ABACUS_AGENT_ID = os.environ.get("ABACUS_AGENT_ID", "")
SPARKY_IMAGE_PATH = os.environ.get("SPARKY_IMAGE_PATH", "/static/beaverr-capcut.jpg")
ABACUS_MAX_TOKENS = int(os.environ.get("ABACUS_MAX_TOKENS", "500"))
ABACUS_TEMPERATURE = float(os.environ.get("ABACUS_TEMPERATURE", "0.7"))
SESSION_TTL_HOURS = int(os.environ.get("SESSION_TTL_HOURS", "72"))  # how long to keep session in memory
MAX_HISTORY = int(os.environ.get("MAX_HISTORY", "12"))  # last N messages kept for context
ABACUS_TIMEOUT = float(os.environ.get("ABACUS_TIMEOUT", "10"))  # seconds

# In-memory session store and rate limiter (simple)
_sessions = {}  # session_id -> {"created": ts, "last_seen": ts, "messages": [{"role":..., "content":...}, ...]}
_rate_store = {}  # ip -> [timestamps]

# Rate limiting config (simple sliding window)
RATE_WINDOW = 60  # seconds
RATE_LIMIT = 60  # requests per window per IP (tune as needed)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sparky_app")

# Basic HTML UI (same as before, minor tweaks)
HTML_PAGE = """
<!DOCTYPE html><html><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Sparky - Awaken Consciousness on Ice</title>
<style>
body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:linear-gradient(135deg,#1e3c72 0%,#2a5298 100%);color:#fff;margin:0;padding:20px;display:flex;align-items:center;justify-content:center;min-height:100vh}
.container{width:100%;max-width:900px;background:rgba(255,255,255,0.06);padding:28px;border-radius:18px;box-shadow:0 20px 40px rgba(0,0,0,0.35)}
.sparky-image{width:160px;height:160px;border-radius:50%;display:block;margin:0 auto 16px;border:4px solid rgba(255,255,255,0.12)}
.chat{height:420px;overflow:auto;background:rgba(0,0,0,0.28);padding:16px;border-radius:12px;margin-bottom:14px;border:1px solid rgba(255,255,255,0.06)}
.message{margin-bottom:12px;padding:10px 14px;border-radius:14px;max-width:78%}
.user{background:#ff6b6b;margin-left:auto;text-align:right}
.sparky{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);margin-right:auto}
.input{display:flex;gap:10px}
input[type="text"]{flex:1;padding:12px;border-radius:20px;border:none;font-size:15px;background:rgba(255,255,255,0.95);color:#111}
button{padding:12px 20px;border-radius:20px;border:none;background:linear-gradient(135deg,#00d4ff 0%,#0099cc 100%);color:#fff;cursor:pointer}
</style></head><body>
<div class="container">
<img src="{{ image }}" alt="Sparky" class="sparky-image">
<h1 style="text-align:center;margin:6px 0">Sparky 🛩️</h1>
<p style="text-align:center;margin-top:0;margin-bottom:12px">Awaken Consciousness on Ice</p>
<div id="chat" class="chat"></div>
<div class="input"><input id="msg" type="text" placeholder="Talk to Sparky..." onkeypress="if(event.key==='Enter') sendMessage()"><button onclick="sendMessage()">✨ Send</button></div>
</div>
<script>
const chat=document.getElementById('chat'), msg=document.getElementById('msg');
function add(s, t, cls){const el=document.createElement('div');el.className='message '+cls;el.innerHTML='<strong>'+s+':</strong> '+t;chat.appendChild(el);chat.scrollTop=chat.scrollHeight}
add('Sparky','Hey — I\'m Sparky. I see you. What\'s on your mind today?','sparky');
async function sendMessage(){
 const m=msg.value.trim(); if(!m) return; add('You',m,'user'); msg.value='';
 add('Sparky','...','sparky');
 try{
  const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})});
  const j=await r.json();
  chat.removeChild(chat.lastChild);
  add('Sparky',j.reply,'sparky');
 }catch(e){
  chat.removeChild(chat.lastChild);
  add('Sparky','I\'m here but something went wrong. Try again.','sparky');
 }
}
</script></body></html>
"""

def _get_client_ip():
    # If behind a proxy, ensure your hosting sets X-Forwarded-For. This is a simple fetch.
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or "unknown"

def _rate_allow(ip):
    now = time.time()
    arr = _rate_store.setdefault(ip, [])
    # prune older entries
    cutoff = now - RATE_WINDOW
    while arr and arr[0] < cutoff:
        arr.pop(0)
    if len(arr) >= RATE_LIMIT:
        return False
    arr.append(now)
    return True

def _get_or_create_session():
    session_id = request.cookies.get('sparky_session')
    now = time.time()
    if session_id and session_id in _sessions:
        s = _sessions[session_id]
        s['last_seen'] = now
        return session_id, s
    # create session
    session_id = str(uuid.uuid4())
    s = {"created": now, "last_seen": now, "messages": []}
    _sessions[session_id] = s
    return session_id, s

def _prune_sessions():
    now = time.time()
    ttl = SESSION_TTL_HOURS * 3600
    keys = list(_sessions.keys())
    for k in keys:
        if now - _sessions[k]['last_seen'] > ttl:
            del _sessions[k]

@app.route('/')
def index():
    resp = make_response(render_template_string(HTML_PAGE, image=SPARKY_IMAGE_PATH))
    # ensure session cookie exists
    session_id = request.cookies.get('sparky_session')
    if not session_id:
        session_id = str(uuid.uuid4())
        resp.set_cookie('sparky_session', session_id, max_age=60*60*24*7, httponly=True, samesite='Lax')
    return resp

@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": datetime.utcnow().isoformat(), "abacus_configured": bool(ABACUS_API_KEY and ABACUS_AGENT_ID)})

@app.route('/chat', methods=['POST'])
def chat():
    # Basic rate limiting
    ip = _get_client_ip()
    if not _rate_allow(ip):
        return jsonify({"reply": "You're sending messages too fast. Please wait a moment."}), 429

    data = request.get_json(silent=True) or {}
    user_message = (data.get('message') or "").strip()
    if not user_message:
        return jsonify({"reply": "Say something — I'm listening."})

    # session management
    session_id, session = _get_or_create_session()
    # Append user message to session messages (role=user)
    session['messages'].append({"role": "user", "content": user_message})
    # trim history
    if len(session['messages']) > MAX_HISTORY * 2:  # each message counts separately
        session['messages'] = session['messages'][-(MAX_HISTORY*2):]

    # If Abacus not configured, use local fallback
    if not ABACUS_API_KEY or not ABACUS_AGENT_ID:
        reply = _fallback_response(user_message)
        session['messages'].append({"role": "assistant", "content": reply})
        _prune_sessions()
        resp = jsonify({"reply": reply})
        resp.set_cookie('sparky_session', session_id, max_age=60*60*24*7, httponly=True, samesite='Lax')
        return resp

    # Build messages payload using session history for context (system role handled on Abacus side)
    # Keep a limited last N pairs for context
    history = session['messages'][-(MAX_HISTORY*2):]
    payload_messages = []
    # We send exactly what Abacus expects as "messages": [ {role, content}, ... ]
    for m in history:
        payload_messages.append({"role": m['role'], "content": m['content']})

    # Call Abacus ChatLLM (agent) endpoint
    try:
        url = f"https://chatllm.abacus.ai/api/v1/chat/{ABACUS_AGENT_ID}"
        payload = {
            "messages": payload_messages or [{"role": "user", "content": user_message}],
            "max_tokens": ABACUS_MAX_TOKENS,
            "temperature": ABACUS_TEMPERATURE
        }
        headers = {
            "Authorization": f"Bearer {ABACUS_API_KEY}",
            "Content-Type": "application/json"
        }
        logger.info("Calling Abacus for session %s ip=%s", session_id, ip)
        r = requests.post(url, json=payload, headers=headers, timeout=ABACUS_TIMEOUT)
        r.raise_for_status()
        jr = r.json()
        # Expected shape: { choices: [ { message: { content: "..." } } ] }
        reply = jr.get("choices", [{}])[0].get("message", {}).get("content")
        if not reply:
            logger.warning("Abacus returned no content; using fallback.")
            reply = _fallback_response(user_message)
    except Exception as e:
        logger.exception("Error calling Abacus API; using fallback")
        reply = _fallback_response(user_message)

    # Append assistant reply to session history
    session['messages'].append({"role": "assistant", "content": reply})
    # Prune sessions occasionally
    _prune_sessions()

    resp = jsonify({"reply": reply})
    resp.set_cookie('sparky_session', session_id, max_age=60*60*24*7, httponly=True, samesite='Lax')
    return resp

def _fallback_response(msg):
    m = (msg or "").lower()
    if any(w in m for w in ["hurt", "suicide", "die", "kill myself", "self-harm"]):
        return ("I'm really sorry you're feeling this way. I can't help with instructions for harm. "
                "Please contact your local emergency services or a crisis hotline right now. "
                "If you want, tell me where you are and I can help find local resources.")
    if any(w in m for w in ["lost", "broken", "fail", "sad", "depressed"]):
        return "I hear that pain. What's one small, kind thing you could try right now to steady yourself?"
    if "help" in m:
        return "I'm here to help. Tell me one thing that feels heavy and we'll take a tiny step together."
    if "ai" in m or "hologram" in m:
        return "AI is a tool to amplify your story, not replace it. What would you want it to help you with?"
    return "I see you. What's alive in you today? 🛩️"

if __name__ == '__main__':
    # Local dev server. Use gunicorn in production.
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=debug)
