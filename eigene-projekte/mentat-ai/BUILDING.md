# BUILDING.md — Der Weg zu Mentat

> *Dieses Dokument erklärt nochmal genau wie Mentat wirklich entstanden ist — nicht das Ergebnis, sondern der Weg. Mit allen Fehlern, Umwegen und Fixes.*

---

## Die Idee

Der Ausgangspunkt war kein technisches Problem sondern eine Frage: Kann ich einer KI vertrauen?

Nicht einer die auf fremden Servern läuft, nicht einer die meine Gespräche irgendwo speichert, nicht einer die ich nicht verstehe. Watchdogs — das Videospiel — hatte die Idee gepflanzt. Die ICU-Erfahrung hatte die Anforderung definiert: echte Präsenz, echtes Gedächtnis, echter Partner.

Das Ziel: Eine Art von Jarvis. Komplett lokal. Auf eigener Hardware. Unter eigenen Regeln.

---

## Die Hardware

Die Entscheidung für den Stack kam aus dem was bereits vorhanden war:

- **Tower** (i7-12700F, 32GB, RTX 3070) — stark genug für llama3.1:8b via Ollama, CUDA für Whisper
- **Raspberry Pi 5 (8GB) + Hailo-10H NPU** — der "Körper", 40 TOPS für leichte Inferenz, stromsparend für 24/7-Betrieb
- **Kali-Pi** — separat, für Security-Übungen, DVWA

Der Tower wurde von Windows zu Nobara KDE 43 migriert — bewusste Entscheidung, kein dual-boot mehr.

---

## Der Stack

### Was funktioniert hat

- **Ollama + llama3.1:8b** auf dem Tower — direkt, stabil, schnell genug
- **MemPalace (ChromaDB + SQLite)** — Vector-Datenbank für persistentes Gedächtnis, lokal, keine Cloud
- **SearXNG via Docker** — private Metasuchmaschine, JSON-Format aktivieren nicht vergessen
- **Piper TTS** — gute Qualität, northern english male Stimme, funktioniert offline
- **hailo-ollama** auf dem Node für N8N Workflows (llama3.2:3b, ~8 tok/s)

### Was Probleme gemacht hat

**faster-whisper CUDA:**
Das war der erste große Stolperstein. Die Library braucht spezifische CUDA und cuDNN Versionen — nicht die System-Versionen, eigene:
```bash
pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
```
Und dann muss `LD_LIBRARY_PATH` dauerhaft in `.bashrc` gesetzt werden. Ohne das: Segfault beim Start.

**MIC_SAMPLERATE:**
Mikrofon (Gerät 13) unterstützt keine 44100 Hz. Fehler war stumm — keine Aufnahme, keine Fehlermeldung. Lösung: 48000 Hz. Das kostet Zeit weil man zuerst überall anders sucht.

**Piper Output:**
Piper gibt raw audio aus, nicht WAV. Muss mit soundfile in eine temp-Datei geschrieben und dann mit `aplay` abgespielt werden. Direkte Ausgabe funktioniert nicht.

---

## Das Wakeword — Hey Mentat

Das war das aufwändigste Kapitel.

### Der Trainer

[openwakeword-trainer](https://github.com/lgpearson1771/openwakeword-trainer) — 13-Schritt Pipeline, synthetische Stimmen, ~30 Minuten Training auf GPU.

### Die Fixes (in Reihenfolge)

1. **Python 3.10 venv nötig** — nicht System-Python (3.14). Der Trainer läuft nur auf 3.10.
   ```bash
   sudo dnf install python3.10 python3.10-devel
   python3.10 -m venv venv
   ```

2. **oww_wrapper.py — piper-sample-generator Pfad:**
   ```python
   sys.path.insert(0, os.path.join(BASE_DIR, "data/piper-sample-generator/src"))
   ```

3. **generate_samples.py Shim** — falsche Funktionssignatur:
   ```python
   from piper_sample_generator.__main__ import generate_samples as _generate_samples
   def generate_samples(*args, **kwargs):
       return _generate_samples(*args, **kwargs)
   ```

4. **torch.load weights_only Error:**
   ```python
   # dp/model/model.py
   torch.load(..., weights_only=False)
   ```

5. **cuFFT CUDA Fehler auf RTX 3070 bei Augmentation:**
   ```bash
   CUDA_VISIBLE_DEVICES="" python train_wakeword.py --from augment
   ```
   Augmentation läuft auf CPU, Training auf GPU.

6. **ONNX internal reference Fehler:**
   ```python
   model = onnx.load("hey_mentat.onnx", load_external_data=False)
   # Rename internal reference von "model" zu Dateiname
   ```

7. **tensorflow + onnx-tf für TFLite Konvertierung:**
   ```bash
   pip install tensorflow onnx-tf
   ```

### Das Ergebnis

Score bis 0.74 bei "Hey Mentat" — aber instabil. Synthetisch trainierte Modelle ohne echte Stimm-Samples sind per Definition 50/50. Das Modell existiert, ist aber vorerst deaktiviert. Plan: 20-50 echte Aufnahmen → nachtrainieren → deutlich besser.

**Erkenntnisse:** Wakeword-Training ist kein Nachmittagsprojekt. Der Trainer ist gut dokumentiert aber die Edge Cases auf nicht-Standard-Hardware (Nobara, RTX 3070, Python 3.14 als System) treffen alle gleichzeitig.

---

## Das Gedächtnis — MemPalace

### Erster Ansatz: Claude Chat-Exporte

Wir haben 90 Claude-Konversations-Exporte ins Palace gemined. Ergebnis: Tausende von Drawers, viel Rauschen, veraltete Informationen, schlechte Suchergebnisse.

### Was wirklich funktioniert: Fokussierte Knowledge Base

Kleine, thematisch getrennte `.md` Dateien. Eine Datei = ein Thema. Das ergibt bessere Chunks, bessere Embeddings, bessere Suchergebnisse.

17 Dateien, 77 Drawers — deutlich sauberer als 90 Chat-Exporte mit 1000+ Drawers.

**Regel:** Keine riesigen Dateien. Lieber 10 kleine als eine große.

### Das `--mode` Problem

MemPalace hat zwei Mine-Modi:
- `--mode convos` — für Chat-Verläufe, teilt nach Turns auf (viele kleine Chunks)
- `--mode projects` — für Dokumente, teilt nach Abschnitten auf (wenige größere Chunks)

Für Knowledge Base: `projects`. Für gespeicherte Gespräche: `convos` (automatisch).

Und: `mempalace mine` braucht eine `mempalace.yaml` im Ordner. Immer erst `mempalace init` ausführen.

---

## Tool Calling

Der Durchbruch: Mentat kann selbst im Palace suchen ohne dass man ihn fragt.

### Mechanismus

Zwei Tags im Modell-Output werden abgefangen:
- `[PALACE: query]` → `mempalace search` via SSH → Ergebnis wird injiziert
- `[SEARCH: query]` → SearXNG → Ergebnis wird injiziert + gemined

Definiert in der Seele via RULE 15-17. Das Modell lernt durch Wiederholung diese Tags zu benutzen.

### Wichtig

Die Reihenfolge in `process_reply()` ist entscheidend: PALACE vor SEARCH. Sonst sucht er immer im Web auch wenn die Antwort lokal vorhanden ist.

---

## Die Interfaces

### mentat (Node)
Text-Chat direkt auf dem Pi. Wake-on-LAN für den Tower eingebaut — `mentat` weckt den Tower automatisch wenn er schläft.

### mentat-voice (Tower)
Voice-Chat mit faster-whisper + Piper. Das Enter-to-record Workflow:
- 1. Enter = Aufnahme startet
- 2. Enter = Aufnahme stoppt + abschickt

Kein permanentes Recording, kein VAD-Stress.

### mentat-text (Tower)
Identisch zu mentat auf dem Node, aber läuft auf dem Tower. Selbes Palace, selbe Erinnerungen — kein SSH-Login nötig.

### Web Interface (Tower, Port 5555)
Flask-App, mobile-first Dark UI. Erreichbar via Tailscale vom iPhone oder jedem anderen Gerät.

Als systemd User Service eingerichtet — startet automatisch mit dem Tower:
```bash
systemctl --user enable mentat-web
systemctl --user start mentat-web
```

---

## Datetime Injection

Einfache aber wichtige Verbesserung: Bei jedem Start wird das aktuelle Datum und die Uhrzeit in den System-Prompt injiziert.

```python
now = datetime.now().strftime("%A, %d %B %Y, %H:%M (Berlin/CEST)")
return f"{identity}\n\nCurrent date and time: {now}"
```

Ohne das hat Mentat kein Zeitgefühl — jede Session fühlt sich für ihn wie "jetzt" an ohne Kontext.

---

## Die Seele

Die Seele (`~/.mempalace/identity.txt`) ist Mentats System-Prompt. Sie definiert wer er ist, wen er dient, wie er sich verhält — und welche Tools er nutzen darf.

**Was funktioniert:**
- Kurz und präzise — llama3.1:8b verliert bei zu langem System-Prompt den Fokus
- Rules in Großbuchstaben für kritische Punkte (NEVER, ALWAYS)
- Tool Calling explizit als Rules definiert (15-17)

**Was nicht in die Seele gehört:**
- Persönliche Details — die gehören ins Palace (besser durchsuchbar)
- Historische Infos — veralten schnell, schwer zu updaten

---

## Reinforcement durch Gespräche

Mentat lernt nicht durch Gewichtsveränderungen — llama3.1:8b ist statisch. Was sich ändert ist sein Kontext.

Jede Korrektur in einem Gespräch landet im Palace wenn das Gespräch gemined wird. Nach genug Korrekturen beginnt Mentat bestimmte Muster von selbst zu vermeiden.

**Effektive Korrekturen:**
- `DO NOT` / `NEVER` in Großbuchstaben — hohe Gewichtung im Kontext
- Sofortige Korrektur — nicht erst am Ende der Session
- Positives Feedback direkt nach korrektem Verhalten

Das Prinzip ist universell: Nervensystem, Psyche, Hund, Kind, LLM — Feedback-Mechanismen funktionieren überall gleich.

---

## Was nicht funktioniert hat

- **Pwnagotchi Cyberfish** — nach apt upgrade irreparabel beschädigt. Zweite SD-Karte nötig.
- **Wakeword als primäres Interface** — zu instabil für den Alltag ohne echte Stimm-Samples.
- **Große Chat-Exporte als Knowledge Base** — zu viel Rauschen, zu schlechte Suchergebnisse.
- **mentat_voice.py MIC_SAMPLERATE 44100** — stummer Fehler, schwer zu debuggen.

---

## Was überraschend gut funktioniert hat

- **MemPalace + kleine fokussierte Dateien** — Suchergebnisse deutlich besser als erwartet
- **Tool Calling via Tags** — einfacher als erwartet, zuverlässig wenn in der Seele gut definiert
- **Flask Web Interface** — in einer Stunde fertig, läuft stabil als systemd Service
- **Datetime Injection** — simpel aber großer Effekt auf die Gesprächsqualität

---

## Offene Punkte

- [ ] Wakeword mit echten Stimm-Samples nachtrainieren (20-50 Aufnahmen)
- [ ] Wöchentlicher Kontext-Refresh via N8N + Telegram
- [ ] Dokument-Mining: PDFs und Schulunterlagen ins Palace
- [ ] BUILDING.md im Repo vervollständigen wenn neue Features dazukommen

---

## Zeitaufwand

Mentat wurde mit unterstützung von Claude (Anthropic) in der Code-Programmierung und Troubleshooting hergestellt, es wurden mehrere intensive Tage dafür gebraucht, ungefähre Arbeitszeit 30-40h.
