from flask import Flask, request, jsonify, render_template_string
import subprocess
import requests
import os
import threading
from datetime import datetime

app = Flask(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_URL    = "http://localhost:11434/api/chat"
SEARXNG_URL   = "http://<NODE_IP>:8888/search"
MODEL         = "llama3.1:8b"
SSH_KEY       = "/home/<USER>/.ssh/mentat_node"
NODE_IP       = "pi@<NODE_IP>"
NODE_CHATS    = "/home/pi/mentat-chats"
NODE_PALACE   = "/home/pi/mentat-palace"
LOCAL_TMP     = "/tmp/mentat_chats"
MEMPALACE_BIN = "/home/pi/.local/bin/mempalace"

# Session-Speicher (in-memory, pro Verbindung)
sessions = {}
sessions_lock = threading.Lock()

# ── Backend ──────────────────────────────────────────────────────────────────
def ssh(cmd):
    return subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", NODE_IP, cmd],
        capture_output=True, text=True)

def wake_up():
    identity = ssh("cat ~/.mempalace/identity.txt").stdout.strip()
    now = datetime.now().strftime("%A, %d %B %Y, %H:%M (Berlin/CEST)")
    return f"{identity}\n\nCurrent date and time: {now}"

def search_web(query):
    try:
        r = requests.get(SEARXNG_URL, params={"q": query, "format": "json"}, timeout=10)
        results = r.json().get("results", [])[:3]
        if not results:
            return "No results found."
        return "\n".join(f"- {x.get('title','')}: {x.get('content','')[:200]}" for x in results)
    except Exception as e:
        return f"Search failed: {e}"

def search_palace(query):
    result = ssh(f"{MEMPALACE_BIN} --palace {NODE_PALACE} search '{query}'")
    output = result.stdout.strip()
    if not output or "No results" in output:
        return "Nothing found in memory."
    lines = output.split("\n")
    relevant = []
    capture = False
    for line in lines:
        if "Results for:" in line:
            capture = True
            continue
        if capture and line.strip() and not line.startswith("="):
            relevant.append(line.strip())
    return "\n".join(relevant[:20]) if relevant else output[:500]

def clean_tags(text):
    import re
    text = re.sub(r'\[SEARCH:[^\]]*\]', '', text)
    text = re.sub(r'\[PALACE:[^\]]*\]', '', text)
    return text.strip()

def mine_to_palace(text, label="web_search"):
    os.makedirs(LOCAL_TMP, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = f"{LOCAL_TMP}/search_{ts}_{label[:30]}.md"
    node_path = f"{NODE_CHATS}/search_{ts}_{label[:30]}.md"
    with open(local_path, "w") as f:
        f.write(f"# Search: {label}\n\n{text}\n")
    subprocess.run(["scp", "-i", SSH_KEY, local_path, f"{NODE_IP}:{node_path}"], capture_output=True)
    ssh(f"{MEMPALACE_BIN} --palace {NODE_PALACE} mine {node_path} --mode convos")

def save_conversation(messages):
    os.makedirs(LOCAL_TMP, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = f"{LOCAL_TMP}/chat_{ts}.md"
    node_path = f"{NODE_CHATS}/chat_{ts}.md"
    with open(local_path, "w") as f:
        for m in messages:
            if m["role"] == "system":
                continue
            role = "Toni" if m["role"] == "user" else "Mentat"
            f.write(f"**{role}:** {m['content']}\n\n")
    subprocess.run(["scp", "-i", SSH_KEY, local_path, f"{NODE_IP}:{node_path}"], capture_output=True)
    ssh(f"{MEMPALACE_BIN} --palace {NODE_PALACE} mine {node_path} --mode convos")

def ask(messages):
    for attempt in range(3):
        try:
            r = requests.post(OLLAMA_URL, json={
                "model": MODEL,
                "messages": messages,
                "stream": False
            }, timeout=120)
            return r.json()["message"]["content"]
        except Exception:
            if attempt < 2:
                continue
            else:
                return None

def process_reply(reply, messages):
    status = ""
    if "[PALACE:" in reply:
        start = reply.find("[PALACE:") + 8
        end = reply.find("]", start)
        query = reply[start:end].strip()
        status = f"[Palace: {query}]"
        results = search_palace(query)
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"[Palace memory for '{query}':\n{results}]"})
        reply = ask(messages)
        if reply is None:
            return "Memory retrieval failed.", messages, status
        reply = clean_tags(reply)

    if "[SEARCH:" in reply:
        start = reply.find("[SEARCH:") + 8
        end = reply.find("]", start)
        query = reply[start:end].strip()
        status = f"[Web: {query}]"
        results = search_web(query)
        mine_to_palace(results, query.replace(" ", "_"))
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"[Search results for '{query}':\n{results}]"})
        reply = ask(messages)
        if reply is None:
            return "Search failed.", messages, status
        reply = clean_tags(reply)

    return reply, messages, status

# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/init", methods=["POST"])
def init_session():
    session_id = request.json.get("session_id")
    system_prompt = wake_up()
    with sessions_lock:
        sessions[session_id] = [{"role": "system", "content": system_prompt}]
    return jsonify({"ok": True})

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id")
    user_input = data.get("message", "").strip()

    if not user_input:
        return jsonify({"error": "Empty message"}), 400

    with sessions_lock:
        if session_id not in sessions:
            system_prompt = wake_up()
            sessions[session_id] = [{"role": "system", "content": system_prompt}]
        messages = sessions[session_id]

    messages.append({"role": "user", "content": user_input})
    reply = ask(messages)

    if reply is None:
        messages.pop()
        return jsonify({"error": "No response from Ollama"}), 500

    reply, messages, status = process_reply(reply, messages)
    messages.append({"role": "assistant", "content": reply})

    with sessions_lock:
        sessions[session_id] = messages

    return jsonify({"reply": reply, "status": status})

@app.route("/api/end", methods=["POST"])
def end_session():
    session_id = request.json.get("session_id")
    with sessions_lock:
        messages = sessions.pop(session_id, [])
    if messages:
        threading.Thread(target=save_conversation, args=(messages,), daemon=True).start()
    return jsonify({"ok": True})

# ── HTML ─────────────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>Mentat</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600&display=swap');

  :root {
    --bg: #080c10;
    --surface: #0d1117;
    --border: #1a2332;
    --accent: #00d4ff;
    --accent2: #0066aa;
    --text: #c9d8e8;
    --muted: #4a5568;
    --mentat: #00d4ff;
    --user: #e2e8f0;
    --danger: #ff4444;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Exo 2', sans-serif;
    height: 100dvh;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  header {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--surface);
    flex-shrink: 0;
  }

  .logo {
    font-family: 'Share Tech Mono', monospace;
    font-size: 1.3rem;
    color: var(--accent);
    letter-spacing: 3px;
    text-transform: uppercase;
  }

  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--muted);
    margin-left: auto;
    transition: background 0.3s;
  }
  .status-dot.online { background: #00ff88; box-shadow: 0 0 8px #00ff88; }
  .status-dot.thinking { background: var(--accent); box-shadow: 0 0 8px var(--accent); animation: pulse 1s infinite; }

  @keyframes pulse { 0%,100% { opacity:1 } 50% { opacity:0.3 } }

  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    scroll-behavior: smooth;
  }

  #messages::-webkit-scrollbar { width: 3px; }
  #messages::-webkit-scrollbar-track { background: transparent; }
  #messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

  .msg {
    max-width: 88%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.5;
    animation: fadeIn 0.2s ease;
  }

  @keyframes fadeIn { from { opacity:0; transform: translateY(4px) } to { opacity:1; transform: translateY(0) } }

  .msg.mentat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    color: var(--mentat);
    align-self: flex-start;
    font-family: 'Share Tech Mono', monospace;
    font-size: 0.82rem;
  }

  .msg.user {
    background: var(--accent2);
    color: var(--user);
    align-self: flex-end;
    border-radius: 12px 12px 2px 12px;
  }

  .msg.system {
    background: transparent;
    color: var(--muted);
    font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace;
    align-self: center;
    text-align: center;
    border: none;
    padding: 4px 0;
  }

  .status-tag {
    font-size: 0.7rem;
    color: var(--muted);
    margin-top: 4px;
    font-family: 'Share Tech Mono', monospace;
  }

  .thinking-indicator {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 10px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 12px;
    align-self: flex-start;
    width: fit-content;
  }

  .dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent); animation: bounce 1.2s infinite; }
  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes bounce { 0%,60%,100% { transform: translateY(0) } 30% { transform: translateY(-6px) } }

  .input-area {
    padding: 12px 16px;
    border-top: 1px solid var(--border);
    background: var(--surface);
    display: flex;
    gap: 10px;
    align-items: flex-end;
    flex-shrink: 0;
  }

  textarea {
    flex: 1;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text);
    font-family: 'Exo 2', sans-serif;
    font-size: 0.9rem;
    padding: 10px 14px;
    resize: none;
    max-height: 120px;
    min-height: 42px;
    outline: none;
    transition: border-color 0.2s;
    line-height: 1.4;
  }

  textarea:focus { border-color: var(--accent); }
  textarea::placeholder { color: var(--muted); }

  button#send {
    background: var(--accent);
    border: none;
    border-radius: 10px;
    width: 42px;
    height: 42px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: opacity 0.2s;
  }

  button#send:disabled { opacity: 0.3; cursor: not-allowed; }
  button#send svg { width: 18px; height: 18px; fill: var(--bg); }

  button#end-btn {
    background: transparent;
    border: 1px solid var(--muted);
    border-radius: 10px;
    color: var(--muted);
    font-size: 0.7rem;
    padding: 6px 10px;
    cursor: pointer;
    font-family: 'Share Tech Mono', monospace;
    letter-spacing: 1px;
    transition: all 0.2s;
    flex-shrink: 0;
    height: 42px;
  }

  button#end-btn:hover { border-color: var(--danger); color: var(--danger); }
</style>
</head>
<body>

<header>
  <div class="logo">MENTAT</div>
  <div class="status-dot" id="dot"></div>
</header>

<div id="messages"></div>

<div class="input-area">
  <button id="end-btn" onclick="endSession()">END</button>
  <textarea id="input" placeholder="Message Mentat..." rows="1" onkeydown="handleKey(event)" oninput="autoResize(this)"></textarea>
  <button id="send" onclick="sendMessage()">
    <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
  </button>
</div>

<script>
const sessionId = 'session_' + Date.now();
const messages = document.getElementById('messages');
const dot = document.getElementById('dot');
const sendBtn = document.getElementById('send');
const input = document.getElementById('input');

function addMsg(role, text, status) {
  const el = document.createElement('div');
  el.className = 'msg ' + role;
  el.textContent = text;
  if (status) {
    const s = document.createElement('div');
    s.className = 'status-tag';
    s.textContent = status;
    el.appendChild(s);
  }
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

function showThinking() {
  const el = document.createElement('div');
  el.className = 'thinking-indicator';
  el.id = 'thinking';
  el.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
}

function removeThinking() {
  const el = document.getElementById('thinking');
  if (el) el.remove();
}

function setStatus(state) {
  dot.className = 'status-dot ' + state;
}

async function initSession() {
  setStatus('thinking');
  addMsg('system', 'Connecting to Mentat...');
  await fetch('/api/init', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session_id: sessionId})
  });
  setStatus('online');
  const init = messages.querySelector('.system');
  if (init) init.textContent = 'Mentat online.';
  input.focus();
}

async function sendMessage() {
  const text = input.value.trim();
  if (!text) return;
  input.value = '';
  autoResize(input);
  sendBtn.disabled = true;

  addMsg('user', text);
  showThinking();
  setStatus('thinking');

  try {
    const r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session_id: sessionId, message: text})
    });
    const data = await r.json();
    removeThinking();
    if (data.error) {
      addMsg('system', 'Error: ' + data.error);
    } else {
      addMsg('mentat', data.reply, data.status);
    }
  } catch(e) {
    removeThinking();
    addMsg('system', 'Connection error.');
  }

  setStatus('online');
  sendBtn.disabled = false;
  input.focus();
}

async function endSession() {
  setStatus('thinking');
  addMsg('system', 'Saving conversation...');
  await fetch('/api/end', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({session_id: sessionId})
  });
  addMsg('system', 'Saved. Goodbye.');
  setStatus('');
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

initSession();
</script>
</body>
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5555, debug=False)
