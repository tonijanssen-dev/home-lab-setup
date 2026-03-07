# 🧠 Offline KI & Privacy – Raspberry Pi 5 + Tor

Dieses Dokument zeigt wie ich lokale KI-Modelle auf dem PC und Raspberry Pi 5 betreibe und Tor sicher nutze — komplett offline, ohne Cloud, ohne Datenweitergabe.

Ziel: Praxisnaher Leitfaden für Mitschüler und gleichzeitig ein Nachweis für Arbeitgeber, dass ich mich technisch fundiert und verantwortungsvoll mit IT-Sicherheit und KI auseinandersetze.

---

## 🔒 Teil 1 – Tor Browser sicher nutzen

### Installation
Download **ausschließlich** von der offiziellen Seite: [https://www.torproject.org/download/](https://www.torproject.org/download/)

### Verbindung prüfen
Nach dem Start auf "Connect" klicken, dann verifizieren:
[https://check.torproject.org](https://check.torproject.org)

### Regeln für Anonymität
- Keine echten Daten eingeben
- Keine Add-ons installieren
- Fenstergröße nicht verändern (Fingerprinting-Schutz)
- Downloads nicht direkt im Browser öffnen

### Optional: VPN davor schalten
Ein VPN (z.B. ProtonVPN) vor Tor schalten verhindert, dass der Internet-Provider sieht, dass du Tor nutzt. Für Einsteiger reicht **Tor allein** völlig aus.

---

## 💻 Teil 2 – Offline KI auf Windows / Linux

Empfohlene Tools: **Ollama**, **LM Studio**, **GPT4All**

Ich nutze **Ollama** — läuft lokal, kein Internet nötig, einfach zu bedienen.

```bash
# Modelle ziehen
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

**Vorteil:** Komplett offline, keine Datenweitergabe, volle Kontrolle  
**Nachteil:** Kleinere Modelle (3–8B Parameter) sind deutlich schwächer als Cloud-Dienste

---

## 🍓 Teil 3 – Lokale KI auf dem Raspberry Pi 5

### Hardware
- Raspberry Pi 5, 8GB RAM
- 128GB Max Endurance SD-Karte
- Kali Linux

### Ansatz A – Ollama (empfohlen, einfacher)

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:3b
ollama run llama3.2:3b
```

> Hinweis: Auf dem Pi 5 sind 3B Modelle realistisch. 7B läuft, aber langsam (~1 Token/Sekunde).

### Ansatz B – llama.cpp (mehr Kontrolle, manueller)

#### Modell herunterladen

```bash
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.2-GGUF \
  mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  --local-dir ~/models --local-dir-use-symlinks False
```

#### llama.cpp kompilieren

```bash
sudo apt update
sudo apt install -y git build-essential cmake libopenblas-dev
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_NATIVE=ON -DGGML_BLAS=ON -DGGML_OPENBLAS=ON
cmake --build build -j"$(nproc)"
```

#### Start-Script erstellen

```bash
nano ~/start-llm.sh
```

```bash
#!/bin/bash
cd ~/llama.cpp
./build/bin/llama-cli \
  -m ~/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
  -c 4096 -n 512 \
  --interactive-first \
  --reverse-prompt "### User:" \
  --prompt "### System:
Du bist ein hilfreicher Assistent. Antworte kurz und auf Deutsch.

### User:
"
```

```bash
chmod +x ~/start-llm.sh
~/start-llm.sh
```

---

## 🎯 Fazit

Lokale KI auf dem Pi 5 ist möglich — mit realistischen Erwartungen. Für komplexe Aufgaben bleibt der Windows Tower die bessere Wahl. Der Pi eignet sich gut als immer-an Server mit kleinem Modell für einfache Abfragen.

Kombination aus beidem: Ollama auf dem Tower, Zugriff vom Pi via Heimnetz oder Tailscale — das ist mein produktives Setup.
