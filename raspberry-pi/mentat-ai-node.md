# mentat-ai-node – Raspberry Pi 5 + Hailo-10H AI Node

Lokaler, privater AI-Inference-Node auf Basis des Raspberry Pi 5 mit AI HAT+ 2 (Hailo-10H). Komplett offline-fähig, kein Cloud-Zwang, volle Kontrolle. Potenzielles IHK-Abschlussprojekt.

---

## Hardware

| Komponente | Details |
|---|---|
| Raspberry Pi 5 | 8GB RAM |
| AI HAT+ 2 | Hailo-10H, 40 TOPS, 8GB LPDDR4X onboard |
| Netzteil | Raspberry Pi 27W USB-C |
| Kühler | Berry Base Aktiver Kühler + Heatsink |
| SD-Karte | 64GB A2 microSD |

---

## OS & Grundsetup

- **OS:** Raspberry Pi OS Lite 64-bit (Trixie)
- **SSH:** aktiviert
- **Hostname:** mentat-ai-node

### System aktualisieren

```bash
sudo apt update && sudo apt full-upgrade -y
```

---

## Netzwerk & Remote Access

### Tailscale installieren

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
sudo systemctl enable tailscaled
```

Zugriff von überall per Tailscale-IP oder via aShellFish (iOS).

---

## Hailo-10H Treiber & SDK

### hailo-h10-all installieren

```bash
sudo apt install hailo-h10-all -y
sudo reboot
```

> Wichtig: `hailo-all` allein reicht nicht für den Hailo-10H — `hailo-h10-all` ist das richtige Paket für diesen Chip.

### Installation verifizieren

```bash
lspci | grep Hailo
sudo hailortcli fw-control identify
```

**Erwarteter Output:**
```
Executing on device: 0001:01:00.0
Firmware Version: 5.1.1 (release,app)
Device Architecture: HAILO10H
```

---

## hailo-ollama installieren

```bash
wget https://dev-public.hailo.ai/2025_12/Hailo10/hailo_gen_ai_model_zoo_5.1.1_arm64.deb
sudo dpkg -i hailo_gen_ai_model_zoo_5.1.1_arm64.deb
```

### hailo-ollama als systemd Service

```bash
sudo nano /etc/systemd/system/hailo-ollama.service
```

```ini
[Unit]
Description=Hailo Ollama Runtime
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStartPre=/bin/sleep 5
ExecStart=/usr/bin/hailo-ollama
Restart=always
RestartSec=3
Environment=HAILO_LOG_LEVEL=info

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable hailo-ollama
sudo systemctl start hailo-ollama
```

### Modell herunterladen

```bash
curl http://localhost:8000/api/pull \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen2.5-instruct:1.5b", "stream": true}'
```

### Verfügbare Modelle anzeigen

```bash
curl --silent http://localhost:8000/hailo/v1/list
```

### Modell testen

```bash
curl http://localhost:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model": "qwen2.5-instruct:1.5b", "messages": [{"role": "user", "content": "Hallo, wer bist du?"}]}'
```

---

## Docker installieren

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker pi
```

Nach dem Neueinloggen testen:

```bash
docker run hello-world
```

---

## N8N via Docker

```bash
docker run -d \
  --name n8n \
  --restart always \
  -p 5678:5678 \
  -e N8N_SECURE_COOKIE=false \
  -e GENERIC_TIMEZONE=Europe/Berlin \
  -e TZ=Europe/Berlin \
  -v n8n_data:/home/node/.n8n \
  --network host \
  n8nio/n8n
```

Erreichbar unter: `http://<MENTAT-IP>:5678`

---

## Backup

Vor größeren Änderungen vollständiges SD-Karten Image erstellen:

- Tool: **Win32DiskImager** (Windows) oder **dd** (Linux)
- SD-Karte in den PC stecken
- Image lesen nach z.B. `~/Backups/mentat-ai-node-backup-DATUM.img`

> Lektion aus dem Pwnagotchi-Fiasko: **Immer vor größeren Änderungen ein Backup ziehen.**

---

## Aktueller Status

- ✅ Raspberry Pi OS Lite 64-bit
- ✅ SSH aktiv
- ✅ Tailscale aktiv
- ✅ Aktiver Kühler verbaut
- ✅ hailo-h10-all installiert
- ✅ Hailo-10H erkannt (FW 5.1.1)
- ✅ hailo-ollama als systemd Service
- ✅ qwen2.5-instruct:1.5b läuft (~8 Token/s)
- ✅ Docker 29.3.1 installiert
- ✅ N8N läuft auf Port 5678
- ✅ SD-Karten Backup erstellt

---

## Warum Hailo-10H?

Der Hailo-10H ist ein dedizierter Neural Processing Unit (NPU) mit 8GB eigenem RAM:

- LLM-Inferenz läuft auf dem HAT, Pi CPU bleibt frei
- Stromsparend — single-digit Watt
- Komplett offline, keine Cloud, keine Datenweitergabe
- Perfekt als always-on lokaler AI-Node im Heimnetz

---

> ⚠️ Dieses Repository enthält keine echten IPs, Passwörter oder sensiblen Netzwerkdaten.
