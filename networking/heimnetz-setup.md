# Heimnetz Übersicht

## Geräte im Netz

| Gerät | OS | Rolle | Erreichbar unter |
|---|---|---|---|
| Tower (RTX 3070, 32GB) | Nobara KDE 43 | Gaming, Alltag | `<TOWER-IP>` |
| Raspberry Pi 5 (Kali) | Kali Linux | Hacking Station | `<PI-IP>` / `kali-raspi` |
| mentat-ai-node | Raspberry Pi OS Lite | Lokaler AI-Node | `<MENTAT-IP>:5678` (N8N) |
| Huawei Laptop | Windows 11 + Ubuntu 24 | Schule, FISI | — |

> IPs werden hier nicht dokumentiert — im lokalen Setup nachschlagen via `ip a` (Linux) oder Router-Oberfläche

---

## Dienste

| Dienst | Port | Gerät |
|---|---|---|
| N8N | 5678 | mentat-ai-node |
| hailo-ollama API | 8000 | mentat-ai-node |
| DVWA (Apache) | 80 | Kali Pi |
| SSH | 22 | Kali Pi + mentat-ai-node |
| Samba | 445 | Kali Pi |

---

## Fernzugriff

Zugriff von außen über **Tailscale**:
1. Tailscale auf Kali Pi und mentat-ai-node aktiv
2. SSH auf Pi via aShellFish (iOS)
3. Vom Pi aus Heimnetz erreichbar

Kein offener Port am Router nötig.

---

## Feste IPs (via Router DHCP-Reservierung)

Alle Geräte haben feste IPs über DHCP-Reservierung im Router — keine statischen IP-Konfigurationen auf den Geräten nötig.

---

## Sicherheitshinweise

- hailo-ollama API nicht direkt ins Internet exponieren
- N8N nur im Heimnetz erreichbar
- Samba nur im Heimnetz, nicht nach außen
- Regelmäßig updaten: `sudo apt update && sudo apt upgrade -y`
