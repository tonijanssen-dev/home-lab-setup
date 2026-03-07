# Heimnetz Übersicht

## Geräte im Netz

| Gerät | Rolle | Erreichbar unter |
|---|---|---|
| Windows Tower | AI-Host, Hauptrechner | `<TOWER-IP>:3000` (Open WebUI) |
| Raspberry Pi 5 | Hacking Station, Server | `<PI-IP>` / `kali-raspi` |
| Huawei Laptop | Schule, Entwicklung | — |

> IPs werden hier nicht dokumentiert — im lokalen Setup nachschlagen via `ipconfig` (Windows) oder `ip a` (Linux)

## Dienste

| Dienst | Port | Gerät |
|---|---|---|
| Open WebUI | 3000 | Windows Tower |
| Ollama API | 11434 | Windows Tower |
| DVWA (Apache) | 80 | Raspberry Pi |
| SSH | 22 | Raspberry Pi |
| Samba | 445 | Raspberry Pi |

## Fernzugriff

Zugriff von außen über **Tailscale**:
1. Tailscale auf Pi aktiv
2. SSH auf Pi via aShellFish (iOS)
3. Vom Pi aus Heimnetz erreichbar

Kein offener Port am Router nötig.

## Sicherheitshinweise

- Ollama API nicht direkt ins Internet exponieren
- Open WebUI mit Benutzeraccounts absichern
- Samba nur im Heimnetz, nicht nach außen
- Pi regelmäßig updaten: `sudo apt update && sudo apt upgrade -y`
