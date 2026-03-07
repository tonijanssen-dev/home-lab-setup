# Tailscale VPN — Raspberry Pi 5

Tailscale ermöglicht sicheren Fernzugriff auf das Heimnetz von überall.

## Installation

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

## Aktivieren

```bash
sudo tailscale up
```

Im Browser den Authentifizierungslink öffnen und einloggen.

## Status prüfen

```bash
tailscale status
```

## Autostart

```bash
sudo systemctl enable tailscaled
```

---

## Zugriff von unterwegs

- **iOS:** aShellFish App → SSH auf Tailscale-IP des Pi
- Vom Pi aus dann Zugriff auf das gesamte Heimnetz möglich
- Open WebUI auf Windows Tower erreichbar über interne Heimnetz-IP

## Vorteil gegenüber Port-Forwarding

- Kein offener Port am Router
- Ende-zu-Ende verschlüsselt
- Kein statische IP nötig
