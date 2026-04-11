import subprocess
import requests
import os
import time
import tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel
from datetime import datetime

# ── Config ──────────────────────────────────────────────────────────────────
OLLAMA_URL         = "http://localhost:11434/api/chat"
SEARXNG_URL        = "http://<NODE_IP>:8888/search"
MODEL              = "llama3.1:8b"
PIPER_BIN          = "/home/tonij/piper/piper/piper"
PIPER_MODEL        = "/home/tonij/piper/en_GB-northern_english_male-medium.onnx"
WHISPER_MODEL      = "small"
MIC_DEVICE         = 13
MIC_SAMPLERATE     = 48000
SSH_KEY            = "/home/tonij/.ssh/mentat_node"
NODE_IP            = "pi@<NODE_IP>"
NODE_CHATS         = "/home/pi/mentat-chats"
NODE_PALACE        = "/home/pi/mentat-palace"
LOCAL_TMP          = "/tmp/mentat_chats"
MEMPALACE_BIN      = "/home/pi/.local/bin/mempalace"
WAKEWORD_MODEL     = "/home/tonij/openwakeword-trainer/export/hey_mentat.onnx"
WAKEWORD_THRESHOLD = 0.5

# ── Modelle laden ────────────────────────────────────────────────────────────
print("[Whisper lädt...]")
whisper = WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
print("[Whisper bereit ✅]")

print("[Wakeword Modell lädt...]")
wakeword = WakeWordModel(wakeword_model_paths=[WAKEWORD_MODEL])
print("[Wakeword bereit ✅]")

# ── Funktionen ───────────────────────────────────────────────────────────────
def speak(text):
    try:
        proc = subprocess.Popen(
            [PIPER_BIN, "--model", PIPER_MODEL, "--output-raw"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        raw, _ = proc.communicate(input=text.encode())
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            fname = f.name
        sf.write(fname, np.frombuffer(raw, dtype=np.int16), 22050)
        os.system(f"aplay -q {fname}")
        os.unlink(fname)
    except Exception as e:
        print(f"[Piper Fehler: {e}]")

def wait_for_wakeword():
    print("[Warte auf 'Hey Mentat'...]")
    detected = False
    def callback(indata, frames, time_info, status):
        nonlocal detected
        audio = indata[:, 0]
        audio_16k = audio[::3].astype(np.int16)
        result = wakeword.predict(audio_16k)
        score = result.get("hey_mentat", 0)
        if score >= WAKEWORD_THRESHOLD:
            detected = True
    with sd.InputStream(samplerate=MIC_SAMPLERATE, channels=1, dtype="int16",
                        device=MIC_DEVICE, callback=callback, blocksize=3840):
        while not detected:
            time.sleep(0.1)
    print("[Hey Mentat erkannt! ✅]")

def listen():
    print("[Enter drücken zum Starten...]")
    input()
    print("[Aufnahme läuft... Enter drücken zum Stoppen]")
    chunks = []
    def callback(indata, frames, time_info, status):
        chunks.append(indata.copy())
    stream = sd.InputStream(samplerate=MIC_SAMPLERATE, channels=1, dtype="float32",
                            device=MIC_DEVICE, callback=callback)
    stream.start()
    input()
    stream.stop()
    stream.close()
    if not chunks:
        return ""
    audio = np.concatenate(chunks, axis=0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        fname = f.name
    sf.write(fname, audio, MIC_SAMPLERATE)
    segments, _ = whisper.transcribe(fname, language="en")
    os.unlink(fname)
    text = " ".join([s.text for s in segments]).strip()
    print(f"[Du sagtest: {text}]")
    return text

def ssh(cmd):
    return subprocess.run(
        ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", NODE_IP, cmd],
        capture_output=True, text=True)

def wake_up():
    return ssh("cat ~/.mempalace/identity.txt").stdout.strip()

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
    """Sucht im MemPalace per SSH und gibt die Ergebnisse zurück."""
    result = ssh(f"{MEMPALACE_BIN} --palace {NODE_PALACE} search '{query}'")
    output = result.stdout.strip()
    if not output or "No results" in output:
        return "Nothing found in memory."
    # Nur relevante Zeilen — alles nach "Results for:"
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
    print("\n[Gespräch gespeichert]")
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
    """Verarbeitet SEARCH und PALACE Tags in Mentat's Antwort."""

    # PALACE Tag abfangen
    if "[PALACE:" in reply:
        start = reply.find("[PALACE:") + 8
        end = reply.find("]", start)
        query = reply[start:end].strip()
        print(f"[Mentat sucht im Palace: {query}]")
        results = search_palace(query)
        print(f"[Palace Ergebnis: {results[:100]}...]")
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"[Palace memory for '{query}':\n{results}]"})
        reply = ask(messages)
        if reply is None:
            return "I couldn't retrieve that from memory.", messages
        reply = clean_tags(reply)

    # SEARCH Tag abfangen
    if "[SEARCH:" in reply:
        start = reply.find("[SEARCH:") + 8
        end = reply.find("]", start)
        query = reply[start:end].strip()
        print(f"[Mentat sucht im Web: {query}]")
        results = search_web(query)
        mine_to_palace(results, query.replace(" ", "_"))
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"[Search results for '{query}':\n{results}]"})
        reply = ask(messages)
        if reply is None:
            return "Search failed.", messages
        reply = clean_tags(reply)

    return reply, messages

# ── Main ─────────────────────────────────────────────────────────────────────
def chat():
    print("[Mentat Voice lädt...]")
    system_prompt = wake_up()
    if not system_prompt:
        print("[Seele nicht erreichbar — prüfe SSH Verbindung zum mentat-node]")
        return
    messages = [{"role": "system", "content": system_prompt}]
    speak("Mentat online. I am ready.")
    time.sleep(1.5)
    print("[Bereit. Enter zum Starten der Aufnahme. Strg+C zum Beenden]\n")

    while True:
        try:
            user_input = listen()
        except KeyboardInterrupt:
            speak("Goodbye Toni.")
            save_conversation(messages)
            break

        if not user_input or len(user_input) < 2:
            continue

        if user_input.lower() in ["exit", "quit", "goodbye", "bye"]:
            speak("Goodbye Toni.")
            save_conversation(messages)
            break

        messages.append({"role": "user", "content": user_input})
        reply = ask(messages)

        if reply is None:
            messages.pop()
            speak("Connection error. Please try again.")
            continue

        reply, messages = process_reply(reply, messages)
        messages.append({"role": "assistant", "content": reply})
        print(f"\nMentat: {reply}\n")
        speak(reply)
        time.sleep(1.5)

if __name__ == "__main__":
    chat()
