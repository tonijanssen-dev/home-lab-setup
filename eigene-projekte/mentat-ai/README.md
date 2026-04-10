# 🧠 Mentat — Persönlicher Offline-KI-Assistent

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Python](https://img.shields.io/badge/python-3.x-blue?logo=python)
![Ollama](https://img.shields.io/badge/model-llama3.1:8b-orange)
![CUDA](https://img.shields.io/badge/CUDA-12%2B-76B900?logo=nvidia)
![Docker](https://img.shields.io/badge/docker-SearXNG-2496ED?logo=docker)
![MemPalace](https://img.shields.io/badge/memory-MemPalace-purple)
![Whisper](https://img.shields.io/badge/STT-faster--whisper-yellow)
![Piper](https://img.shields.io/badge/TTS-Piper-lightgrey)
![RPi](https://img.shields.io/badge/hardware-RPi5%20%2B%20Hailo--10H-C51A4A?logo=raspberrypi)
![Privacy](https://img.shields.io/badge/privacy-100%25%20lokal-darkgreen)

> *"Not a tool. A partner."*

Mentat ist ein vollständig lokal laufender, persönlicher KI-Assistent — aufgebaut auf eigener Hardware, ohne Cloud, ohne Datenweitergabe. Er läuft auf einem Raspberry Pi 5 mit Hailo-NPU als "Körper" und nutzt einen leistungsstarken Tower-PC als "Gehirn". Er hat ein persistentes Gedächtnis, kann das Web durchsuchen, hört zu und redet zurück.

![Mentat Voice Chat in Aktion](Bildschirmfoto_20260410_202545.png)

---

## Warum?

Weil ich eine KI wollte, der ich vertrauen kann. Kein Modell das meine Daten an fremde Server schickt, kein schwarzes System das ich nicht verstehe. Mentat läuft auf meiner Hardware, unter meinen Regeln — und wächst mit jeder Unterhaltung.

---

## Architektur

```
mentat-ai-node (RPi5 8GB + Hailo-10H NPU)
├── MemPalace (ChromaDB + SQLite)   → persistentes Gedächtnis
├── SearXNG (Docker, Port 8888)     → private Websuche
├── mentat.py                       → Text-Chat Interface
├── mentat-chats/                   → gespeicherte Gespräche
└── ~/.mempalace/identity.txt       → Mentats Seele

Tower (Nobara KDE, RTX 3070)
├── Ollama (Port 11434)             → llama3.1:8b
├── faster-whisper (CUDA)           → Speech-to-Text
├── Piper TTS                       → Text-to-Speech
└── mentat_voice.py                 → Voice-Chat Interface
```

Mentat hat zwei Interfaces:
- **`mentat`** — Textbasierter Chat, läuft direkt auf dem mentat-ai-node
- **`mentat-voice`** — Sprach-Chat, läuft auf dem Tower (Mikrofon + Lautsprecher erforderlich)

---

## Komponenten

| Komponente | Beschreibung | Läuft auf |
|---|---|---|
| llama3.1:8b | Sprachmodell (Gehirn) | Tower via Ollama |
| MemPalace | Persistentes Gedächtnis (ChromaDB) | mentat-ai-node |
| SearXNG | Private Metasuchmaschine | mentat-ai-node (Docker) |
| faster-whisper | Speech-to-Text (CUDA-beschleunigt) | Tower |
| Piper TTS | Text-to-Speech | Tower |
| Wake-on-LAN | Tower automatisch starten | mentat-ai-node → Tower |

---

## Features

- **Persistentes Gedächtnis** — Jedes Gespräch wird ins Palace gemined und bleibt erhalten
- **Websuche** — Mentat sucht selbstständig via SearXNG wenn er etwas nicht weiß, und speichert das Ergebnis
- **Vollständig offline** — Kein einziger Request geht nach außen (außer SearXNG Suchen)
- **Sprachein- und -ausgabe** — Whisper STT + Piper TTS, läuft lokal auf der GPU
- **Wake-on-LAN** — `mentat` startet den Tower automatisch wenn er schläft
- **Auto-Save + Auto-Mine** — Jedes Gespräch wird gespeichert und automatisch ins Palace geladen

---

## Setup

### Voraussetzungen

**mentat-ai-node:**
- Raspberry Pi 5 (8GB RAM empfohlen)
- Raspberry Pi OS Lite 64-bit
- Docker installiert
- Python 3.x mit pip
- Tailscale (optional, für Remote-Zugriff)

**Tower:**
- Linux (getestet mit Nobara KDE 43)
- NVIDIA GPU mit CUDA 12+
- Ollama installiert
- Python 3.x mit pip

---

### Installation

#### 1. MemPalace installieren (mentat-ai-node)

```bash
pip install mempalace --break-system-packages
mkdir ~/mentat-palace && mempalace init ~/mentat-palace
```

#### 2. SearXNG starten (mentat-ai-node)

```bash
docker run -d \
  --name searxng \
  --restart always \
  -p 0.0.0.0:8888:8080 \
  -e BASE_URL=http://<NODE_IP>:8888 \
  -e INSTANCE_NAME=mentat-search \
  searxng/searxng:latest
```

JSON-Format aktivieren:
```bash
docker exec searxng sh -c "printf '\nsearch:\n  formats:\n    - html\n    - json\n' >> /etc/searxng/settings.yml"
docker restart searxng
```

#### 3. Ollama + Modell installieren (Tower)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
```

Ollama im Netzwerk erreichbar machen:
```bash
# /etc/systemd/system/ollama.service.d/override.conf
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

```bash
sudo systemctl daemon-reload && sudo systemctl restart ollama
```

#### 4. Faster-Whisper + Piper installieren (Tower)

```bash
sudo dnf install -y portaudio-devel python3-devel pulseaudio-libs-devel
pip install faster-whisper sounddevice soundfile numpy --break-system-packages
pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" --break-system-packages
```

LD_LIBRARY_PATH dauerhaft setzen:
```bash
echo 'export LD_LIBRARY_PATH=/home/<USER>/.local/lib/python3.x/site-packages/nvidia/cublas/lib:/home/<USER>/.local/lib/python3.x/site-packages/nvidia/cudnn/lib' >> ~/.bashrc
```

Piper herunterladen:
```bash
mkdir -p ~/piper && cd ~/piper
wget https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz

# Stimme herunterladen
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium.onnx.json
```

#### 5. SSH-Key einrichten (Tower → mentat-ai-node)

```bash
ssh-keygen -t ed25519 -C "mentat-voice" -f ~/.ssh/mentat_node -N ""
ssh-copy-id -i ~/.ssh/mentat_node.pub pi@<NODE_IP>
```

#### 6. Wake-on-LAN einrichten (Tower)

BIOS: ErP State = Disabled, Wake on LAN = Enabled

```bash
# /etc/systemd/system/wol.service
[Unit]
Description=Wake-on-LAN
[Service]
ExecStart=/sbin/ethtool -s <NETZWERK_INTERFACE> wol g
[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now wol.service
```

#### 7. Scripts und Aliase einrichten

```bash
# mentat.py → auf mentat-ai-node nach ~/mentat.py kopieren
# mentat_voice.py → auf Tower nach ~/mentat_voice.py kopieren

# ~/.bashrc auf mentat-ai-node
echo "alias mentat='python3 ~/mentat.py'" >> ~/.bashrc

# ~/.bashrc auf Tower
echo "alias mentat-voice='python3 ~/mentat_voice.py'" >> ~/.bashrc
```

---

## Konfiguration

Wichtige Variablen in `mentat.py` und `mentat_voice.py` anpassen:

```python
TOWER_IP      = "<TOWER_IP>"        # IP des Tower-PCs
TOWER_MAC     = "<TOWER_MAC>"       # MAC für Wake-on-LAN
NODE_IP       = "pi@<NODE_IP>"      # IP des mentat-ai-node
OLLAMA_URL    = "http://<TOWER_IP>:11434/api/chat"
SEARXNG_URL   = "http://<NODE_IP>:8888/search"
```

---

## Die Seele

Mentats Persönlichkeit und Wissen über seinen Besitzer liegt in:

```
~/.mempalace/identity.txt   (auf mentat-ai-node)
```

Diese Datei wird bei jedem Start als System-Prompt geladen. Sie definiert wer Mentat ist, wen er dient und wie er sich verhält.

> ⚠️ Keine echten IPs, Passwörter oder sensiblen Daten in die Seele schreiben — sie liegt auf dem Node und wird per SSH übertragen.

---

## Nutzung

### Text-Chat (auf mentat-ai-node)

```bash
mentat
```

Schreibe eine Nachricht, drücke Enter. `exit` beendet das Gespräch und mined automatisch ins Palace.

### Voice-Chat (auf Tower)

```bash
mentat-voice
```

Sprich ins Mikrofon, drücke Enter wenn fertig. Mentat antwortet mit Stimme. `Strg+C` beendet das Gespräch.

### Websuche

Mentat sucht automatisch wenn er etwas nicht weiß — er gibt `[SEARCH: query]` aus, das Script sucht via SearXNG und injiziert die Ergebnisse. Das Suchergebnis wird anschließend ins Palace gemined.

---

## Palace verwalten

```bash
# Status
mempalace --palace ~/mentat-palace status

# Manuell minen
mempalace --palace ~/mentat-palace mine ~/mentat-chats --mode convos

# Suchen
mempalace --palace ~/mentat-palace search "dein suchbegriff"
```

---

## Sicherheitshinweise

- Keine echten IPs, MACs oder Zugangsdaten im Repository
- SearXNG läuft im eigenen Docker-Netzwerk
- Ollama ist nur im LAN erreichbar, nicht öffentlich
- SSH-Kommunikation Tower ↔ Node läuft über Key-Auth
- MemPalace speichert lokal — keine Cloud-Anbindung

---

## Scripts

### mentat.py — Text-Chat (mentat-ai-node)

```python
import subprocess, requests, os, time
from datetime import datetime

# ── Config ── Anpassen auf eigene Umgebung ───────────────────────────────────
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
    return '\n'.join(l for l in lines if not l.startswith('Wake-up')
                     and not l.startswith('===') and not l.startswith('##'))

def search_web(query):
    try:
        r = requests.get(SEARXNG_URL, params={"q": query, "format": "json"}, timeout=10)
        results = r.json().get("results", [])[:3]
        if not results:
            return "No results found."
        return "\n".join(f"- {x.get('title','')}: {x.get('content','')[:200]}" for x in results)
    except Exception as e:
        return f"Search failed: {e}"

def clean_search_tags(text):
    import re
    return re.sub(r'\[SEARCH:[^\]]*\]', '', text).strip()

def mine_to_palace(text, label="web_search"):
    os.makedirs(CHATS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{CHATS_DIR}/search_{ts}_{label[:30]}.md"
    with open(path, 'w') as f:
        f.write(f"# Search: {label}\n\n{text}\n")
    subprocess.run([MEMPALACE_BIN, "--palace", PALACE, "mine", path, "--mode", "convos"],
                   capture_output=True)

def save_conversation(messages):
    os.makedirs(CHATS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{CHATS_DIR}/chat_{ts}.md"
    with open(path, 'w') as f:
        for m in messages:
            if m['role'] == 'system':
                continue
            role = "Toni" if m['role'] == 'user' else "Mentat"
            f.write(f"**{role}:** {m['content']}\n\n")
    print(f"\n[Gespräch gespeichert: {path}]")
    subprocess.run([MEMPALACE_BIN, "--palace", PALACE, "mine", path, "--mode", "convos"],
                   capture_output=True)
    print("[Palace aktualisiert ✅]")

def ask(messages):
    for attempt in range(3):
        try:
            r = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": messages,
                                                "stream": False}, timeout=120)
            return r.json()["message"]["content"]
        except Exception:
            if attempt < 2:
                print("[Verbindungsfehler, versuche erneut...]")
            else:
                return None

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
        if "[SEARCH:" in user_input:
            start = user_input.find("[SEARCH:") + 8
            end = user_input.find("]", start)
            query = user_input[start:end].strip()
            print(f"[Suche: {query} — bitte warten...]")
            results = search_web(query)
            mine_to_palace(results, query.replace(" ", "_"))
            messages.append({"role": "user",
                             "content": f"{user_input}\n\n[Search results:\n{results}]"})
        else:
            messages.append({"role": "user", "content": user_input})
        reply = ask(messages)
        if reply is None:
            messages.pop()
            print("[Keine Antwort. Bitte nochmal eingeben.]\n")
            continue
        if "[SEARCH:" in reply:
            start = reply.find("[SEARCH:") + 8
            end = reply.find("]", start)
            query = reply[start:end].strip()
            print(f"[Mentat sucht: {query} — bitte warten...]")
            results = search_web(query)
            mine_to_palace(results, query.replace(" ", "_"))
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user",
                             "content": f"[Search results for '{query}':\n{results}]"})
            print("[Ergebnisse gefunden, Mentat antwortet...]")
            reply = ask(messages)
            if reply is None:
                print("[Keine Antwort nach Suche.]\n")
                continue
            reply = clean_search_tags(reply)
        messages.append({"role": "assistant", "content": reply})
        print(f"\nMentat: {reply}\n")

if __name__ == "__main__":
    chat()
```

---

### mentat_voice.py — Voice-Chat (Tower)

```python
import subprocess, requests, os, time, tempfile
import sounddevice as sd
import soundfile as sf
import numpy as np
from faster_whisper import WhisperModel
from datetime import datetime

# ── Config ── Anpassen auf eigene Umgebung ───────────────────────────────────
OLLAMA_URL     = "http://localhost:11434/api/chat"
SEARXNG_URL    = "http://<NODE_IP>:8888/search"
MODEL          = "llama3.1:8b"
PIPER_BIN      = "/home/<USER>/piper/piper/piper"
PIPER_MODEL    = "/home/<USER>/piper/en_GB-northern_english_male-medium.onnx"
WHISPER_MODEL  = "small"
MIC_DEVICE     = 13          # prüfen mit: python3 -c "import sounddevice as sd; print(sd.query_devices())"
MIC_SAMPLERATE = 44100
SSH_KEY        = "/home/<USER>/.ssh/mentat_node"
NODE_IP        = "pi@<NODE_IP>"
NODE_CHATS     = "/home/pi/mentat-chats"
NODE_PALACE    = "/home/pi/mentat-palace"
LOCAL_TMP      = "/tmp/mentat_chats"
MEMPALACE_BIN  = "/home/pi/.local/bin/mempalace"

print("[Whisper lädt...]")
whisper = WhisperModel(WHISPER_MODEL, device="cuda", compute_type="float16")
print("[Whisper bereit ✅]")

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

def listen():
    print("[Hört zu... Enter drücken wenn fertig]")
    chunks = []
    def callback(indata, frames, time_info, status):
        chunks.append(indata.copy())
    stream = sd.InputStream(samplerate=MIC_SAMPLERATE, channels=1,
                            dtype="float32", device=MIC_DEVICE, callback=callback)
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

def clean_search_tags(text):
    import re
    return re.sub(r'\[SEARCH:[^\]]*\]', '', text).strip()

def mine_to_palace(text, label="web_search"):
    os.makedirs(LOCAL_TMP, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = f"{LOCAL_TMP}/search_{ts}_{label[:30]}.md"
    node_path = f"{NODE_CHATS}/search_{ts}_{label[:30]}.md"
    with open(local_path, "w") as f:
        f.write(f"# Search: {label}\n\n{text}\n")
    subprocess.run(["scp", "-i", SSH_KEY, local_path, f"{NODE_IP}:{node_path}"],
                   capture_output=True)
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
    subprocess.run(["scp", "-i", SSH_KEY, local_path, f"{NODE_IP}:{node_path}"],
                   capture_output=True)
    ssh(f"{MEMPALACE_BIN} --palace {NODE_PALACE} mine {node_path} --mode convos")
    print("[Palace aktualisiert ✅]")

def ask(messages):
    for attempt in range(3):
        try:
            r = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": messages,
                                                "stream": False}, timeout=120)
            return r.json()["message"]["content"]
        except Exception:
            if attempt < 2:
                print("[Verbindungsfehler, versuche erneut...]")
            else:
                return None

def chat():
    print("[Mentat Voice lädt...]")
    system_prompt = wake_up()
    if not system_prompt:
        print("[Seele nicht erreichbar — prüfe SSH Verbindung zum mentat-node]")
        return
    messages = [{"role": "system", "content": system_prompt}]
    speak("Mentat online. I am listening.")
    time.sleep(1.5)
    print("[Mentat online. Sprich und drücke Enter wenn fertig. Strg+C zum Beenden]\n")
    while True:
        try:
            user_input = listen()
        except KeyboardInterrupt:
            speak("Goodbye.")
            save_conversation(messages)
            break
        if not user_input or len(user_input) < 2:
            continue
        if user_input.lower() in ["exit", "quit", "goodbye", "bye"]:
            speak("Goodbye.")
            save_conversation(messages)
            break
        messages.append({"role": "user", "content": user_input})
        reply = ask(messages)
        if reply is None:
            messages.pop()
            speak("Connection error. Please try again.")
            continue
        if "[SEARCH:" in reply:
            start = reply.find("[SEARCH:") + 8
            end = reply.find("]", start)
            query = reply[start:end].strip()
            print(f"[Mentat sucht: {query}]")
            results = search_web(query)
            mine_to_palace(results, query.replace(" ", "_"))
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user",
                             "content": f"[Search results for '{query}':\n{results}]"})
            reply = ask(messages)
            if reply is None:
                speak("Search failed.")
                continue
            reply = clean_search_tags(reply)
        messages.append({"role": "assistant", "content": reply})
        print(f"\nMentat: {reply}\n")
        speak(reply)
        time.sleep(1.5)

if __name__ == "__main__":
    chat()
```

---

## Roadmap

- [ ] Wöchentlicher Kontext-Refresh via N8N + Telegram
- [ ] Tool Calling: Mentat sucht selbst im Palace bei unbekannten Fragen
- [ ] Wakeword "Hey Mentat" (custom openwakeword Modell)
- [ ] Dokument-Mining: PDFs/Schulunterlagen ins Palace

---

## Tech Stack

`llama3.1:8b` `Ollama` `MemPalace` `ChromaDB` `SearXNG` `faster-whisper` `Piper TTS` `Docker` `Raspberry Pi 5` `Hailo-10H` `Wake-on-LAN` `Tailscale`
