import subprocess, requests, os, time
from datetime import datetime

PALACE        = "/home/pi/mentat-palace"
CHATS_DIR     = "/home/pi/mentat-chats"
OLLAMA_URL    = "http://<TOWER_IP>:11434/api/chat"
SEARXNG_URL   = "http://localhost:8888/search"
MODEL         = "llama3.1:8b"
TOWER_MAC     = "<TOWER_MAC>"
TOWER_IP      = "<TOWER_IP>"
MEMPALACE_BIN = "/home/pi/.local/bin/mempalace"

def wake_up_tower():
    try:
        requests.get(f"http://{TOWER_IP}:11434", timeout=3)
        return True
    except:
        print("[Tower schläft — sende Wake-on-LAN...]")
        subprocess.run(["wakeonlan", TOWER_MAC], capture_output=True)
        print("[Warte auf Tower...]")
        for _ in range(30):
            time.sleep(5)
            try:
                requests.get(f"http://{TOWER_IP}:11434", timeout=3)
                print("[Tower online ✅]")
                return True
            except:
                print(".", end="", flush=True)
        print("\n[Tower nicht erreichbar.]")
        return False

def wake_up():
    result = subprocess.run(
        [MEMPALACE_BIN, "--palace", PALACE, "wake-up"],
        capture_output=True, text=True
    )
    lines = result.stdout.strip().split('\n')
    identity = '\n'.join(l for l in lines if not l.startswith('Wake-up')
                         and not l.startswith('===') and not l.startswith('##'))
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
    """Sucht im MemPalace und gibt relevante Ergebnisse zurück."""
    result = subprocess.run(
        [MEMPALACE_BIN, "--palace", PALACE, "search", query],
        capture_output=True, text=True
    )
    output = result.stdout.strip()
    if not output or "No results" in output:
        return "Nothing found in memory."
    # Relevante Zeilen extrahieren
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
    os.makedirs(CHATS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"{CHATS_DIR}/search_{ts}_{label[:30]}.md"
    with open(filepath, 'w') as f:
        f.write(f"# Search: {label}\n\n{text}\n")
    subprocess.run(
        [MEMPALACE_BIN, "--palace", PALACE, "mine", filepath, "--mode", "convos"],
        capture_output=True
    )

def save_conversation(messages):
    os.makedirs(CHATS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = f"{CHATS_DIR}/chat_{ts}.md"
    with open(filepath, 'w') as f:
        for m in messages:
            if m['role'] == 'system':
                continue
            role = "Toni" if m['role'] == 'user' else "Mentat"
            f.write(f"**{role}:** {m['content']}\n\n")
    print(f"\n[Gespräch gespeichert: {filepath}]")
    subprocess.run(
        [MEMPALACE_BIN, "--palace", PALACE, "mine", filepath, "--mode", "convos"],
        capture_output=True
    )
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
    """Verarbeitet PALACE und SEARCH Tags in Mentats Antwort."""

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
    first = __import__('sys').stdin.readline()
    if not first:
        raise EOFError
    lines.append(first.rstrip('\n'))
    import select, sys
    while select.select([sys.stdin], [], [], 0.15)[0]:
        line = sys.stdin.readline()
        if not line:
            break
        lines.append(line.rstrip('\n'))
    return '\n'.join(lines).strip()

def chat():
    print("Mentat lädt...")
    if not wake_up_tower():
        print("Tower nicht erreichbar. Abbruch.")
        return
    system_prompt = wake_up()
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
