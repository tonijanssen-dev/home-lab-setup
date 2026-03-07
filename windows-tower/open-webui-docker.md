# Open WebUI — Docker Setup

ChatGPT-ähnliches Interface für lokale Ollama-Modelle.

## Voraussetzungen

- Docker Desktop installiert
- Ollama läuft auf Windows

## Installation

```bash
docker run -d \
  -p 0.0.0.0:3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

### Befehl erklärt

| Parameter | Bedeutung |
|---|---|
| `-d` | Läuft im Hintergrund |
| `-p 0.0.0.0:3000:8080` | Port 3000 im Heimnetz erreichbar |
| `--add-host=host.docker.internal:host-gateway` | Container kann Ollama auf Windows erreichen |
| `-v open-webui:/app/backend/data` | Daten persistent speichern |
| `--restart always` | Startet automatisch neu |

## Zugriff

- Lokal: `http://localhost:3000`
- Im Heimnetz: `http://<TOWER-IP>:3000`

## Mehrere Benutzer

- Erster registrierter Account = Admin
- Weitere Accounts = normale User
- Modellzugriff: Admin Panel → Modelle → Zugriff auf "Öffentlich" setzen

## Container verwalten

```bash
# Stoppen
docker stop open-webui

# Löschen
docker rm open-webui

# Logs anzeigen
docker logs open-webui
```

## Ollama Verbindung prüfen

Admin Panel → Einstellungen → Verbindungen → `http://host.docker.internal:11434`
