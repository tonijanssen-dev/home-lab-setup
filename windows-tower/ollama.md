# Ollama — Windows Tower

Lokale AI-Modelle auf dem Windows Tower betreiben.

## Hardware

- RTX 3070 (8GB VRAM)
- 32GB RAM
- Windows 11

## Installation

1. [ollama.com](https://ollama.com) → Download für Windows → installieren
2. Ollama läuft danach automatisch im Hintergrund

## Modelle

```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

| Modell | Zweck |
|---|---|
| `llama3.1:8b` | Allround, Gespräche, Security-Theorie |
| `qwen2.5-coder:7b` | Code, Scripting, PowerShell, Python |

## Verfügbare Modelle anzeigen

```bash
ollama list
```

## Modell direkt in der Konsole testen

```bash
ollama run llama3.1:8b
```

## Hinweise

- Ollama lauscht standardmäßig auf `localhost:11434`
- GPU wird automatisch genutzt wenn CUDA verfügbar
- 8GB VRAM = maximale Modellgröße ~8B Parameter (quantisiert)
