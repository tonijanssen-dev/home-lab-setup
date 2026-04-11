import subprocess
import requests
import os
import sys
import select
from datetime import datetime

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

# ── Funktionen ───────────────────────────────────────────────────────────────
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
    print(f"\n[Gespräch gespeichert]")
    subprocess.run(["scp", "-i", SSH_KEY, local_path, f"{NODE_IP}:{node_path}"], capture_output=True)
    ssh(f"{MEMPALACE_BIN} --palace {NODE_PALACE} mine {node_path} --mode convos")
    print("[Palace aktualisiert ✅]")

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
                print("[Verbindungsfehler, versuche erneut...]")
            else:
                return None

def process_reply(reply, messages):
    if "[PALACE:" in reply:
        start = reply.find("[PALACE:") + 8
        end = reply.find("]", start)
        query = reply[start:end].strip()
        print(f"[Mentat sucht im Palace: {query}...]")
        results = search_palace(query)
        print(f"[Palace: {results[:80]}...]")
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"[Palace memory for '{query}':\n{results}]"})
        reply = ask(messages)
        if reply is None:
            return "[Keine Antwort nach Palace-Suche.]", messages
        reply = clean_tags(reply)

    if "[SEARCH:" in reply:
        start = reply.find("[SEARCH:") + 8
        end = reply.find("]", start)
        query = reply[start:end].strip()
        print(f"[Mentat sucht im Web: {query}...]")
        results = search_web(query)
        mine_to_palace(results, query.replace(" ", "_"))
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"[Search results for '{query}':\n{results}]"})
        reply = ask(messages)
        if reply is None:
            return "[Keine Antwort nach Web-Suche.]", messages
        reply = clean_tags(reply)

    return reply, messages

def read_input():
    print("Du: ", end="", flush=True)
    lines = []
    first = sys.stdin.readline()
    if not first:
        raise EOFError
    lines.append(first.rstrip('\n'))
    while select.select([sys.stdin], [], [], 0.15)[0]:
        line = sys.stdin.readline()
        if not line:
            break
        lines.append(line.rstrip('\n'))
    return '\n'.join(lines).strip()

# ── Main ─────────────────────────────────────────────────────────────────────
def chat():
    print("[Mentat lädt...]")
    system_prompt = wake_up()
    if not system_prompt:
        print("[Seele nicht erreichbar — prüfe SSH Verbindung zum mentat-node]")
        return
    messages = [{"role": "system", "content": system_prompt}]
    print("Mentat online. 'exit' zum Beenden.\n")

    while True:
        try:
            user_input = read_input()
        except (KeyboardInterrupt, EOFError):
            print("\nBis dann.")
            save_conversation(messages)
            break

        if user_input.lower() == "exit":
            print("Bis dann.")
            save_conversation(messages)
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})
        reply = ask(messages)

        if reply is None:
            messages.pop()
            print("[Keine Antwort. Bitte nochmal eingeben.]\n")
            continue

        reply, messages = process_reply(reply, messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"\nMentat: {reply}\n")

if __name__ == "__main__":
    chat()
