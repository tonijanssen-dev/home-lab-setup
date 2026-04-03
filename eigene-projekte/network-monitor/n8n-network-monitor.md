# Mentat Network Monitor

Automatischer Heimnetzwerk-Monitor der alle 8h einen nmap + arp-scan durchführt, Geräte gegen eine Whitelist prüft und einen Bericht via Telegram meldet.

---

## Workflow

![N8N Workflow](n8n-network-monitor-workflow.png)

**Pipeline:**
`Cron Job (Pi)` → `scan.sh` → `Webhook (N8N)` → `Code in JavaScript (Whitelist-Check + Nachricht)` → `IF` → `HTTP Request (Ollama)` → `Send a text message (Telegram)`

---

## Infrastruktur

| Komponente | Details |
|------------|---------|
| N8N | Docker Container auf `mentat-ai-node` |
| hailo-ollama | Nativer Prozess auf Pi, Port 8000, Hailo-8 NPU |
| Modell | `qwen2.5-instruct:1.5b` |
| nmap | Nativ auf Pi installiert |
| arp-scan | Nativ auf Pi installiert |

---

## Dateien auf dem Pi

| Pfad | Beschreibung |
|------|-------------|
| `/etc/network-monitor/scan.sh` | Bash Script — führt Scans aus, schickt an Webhook |
| `/etc/network-monitor/whitelist.json` | Liste bekannter Geräte (IP + MAC + Name) |

---

## scan.sh

```bash
#!/bin/bash

WHITELIST="/etc/network-monitor/whitelist.json"
WEBHOOK="http://localhost:5678/webhook/network-scan"

NMAP_OUT=$(sudo /usr/bin/nmap -sn 192.168.x.0/24 2>/dev/null)
ARP_OUT=$(sudo /usr/sbin/arp-scan --localnet --retry=3 2>/dev/null)

DEVICES=$(echo "$ARP_OUT" | grep -E "^192\." | awk '{print $1, $2}')

JSON="["
FIRST=true

while IFS= read -r line; do
  IP=$(echo "$line" | awk '{print $1}')
  MAC=$(echo "$line" | awk '{print $2}')

  KNOWN=$(python3 -c "
import json, sys
wl = json.load(open('$WHITELIST'))
for d in wl:
    if d['mac'].lower() == '$MAC'.lower():
        print(d['name'])
        sys.exit()
print('UNKNOWN')
")

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    JSON="$JSON,"
  fi

  JSON="$JSON{\"ip\":\"$IP\",\"mac\":\"$MAC\",\"name\":\"$KNOWN\",\"known\":$([ \"$KNOWN\" = \"UNKNOWN\" ] && echo false || echo true)}"

done <<< "$DEVICES"

JSON="$JSON]"

curl -s -X POST "$WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "{\"devices\":$JSON,\"timestamp\":\"$(date -Iseconds)\"}"
```

---

## whitelist.json

```json
[
  {"ip": "192.168.x.1", "mac": "xx:xx:xx:xx:xx:xx", "name": "Router"},
  {"ip": "192.168.x.2", "mac": "xx:xx:xx:xx:xx:xx", "name": "Desktop-PC"},
  {"ip": "192.168.x.3", "mac": "xx:xx:xx:xx:xx:xx", "name": "Kali-LAN"},
  {"ip": "192.168.x.4", "mac": "xx:xx:xx:xx:xx:xx", "name": "mentat-ai-node"},
  {"ip": "192.168.x.5", "mac": "xx:xx:xx:xx:xx:xx", "name": "Kali-WLAN"},
  {"ip": "192.168.x.6", "mac": "xx:xx:xx:xx:xx:xx", "name": "Smartphone"},
  {"ip": "192.168.x.7", "mac": "xx:xx:xx:xx:xx:xx", "name": "Smart-TV"}
]
```

> ⚠️ MACs wurden aus Sicherheitsgründen entfernt.

---

## Code in JavaScript — Whitelist-Check & Nachricht

Bei bekannten Geräten wird die Telegram-Nachricht direkt gebaut. Bei unbekannten Geräten werden IP und MAC für Ollama aufbereitet.

```javascript
const body = $input.first().json.body;
const devices = body.devices || [];
const timestamp = body.timestamp;

const date = new Date(timestamp);
const formatted = date.toLocaleString('de-DE', {
  timeZone: 'Europe/Berlin',
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit'
});

const known = devices.filter(d => d.known === true);
const unknown = devices.filter(d => d.known === false);

if (unknown.length === 0) {
  const deviceList = known.map(d => `✓ ${d.name}`).join('\n');
  return [{
    json: {
      has_unknown: false,
      message: `🟢 Netzwerk-Scan — ${formatted}\n\n${known.length} Geraete online, alle bekannt.\n\n${deviceList}`
    }
  }];
}

const unknownList = unknown.map(d => `IP: ${d.ip}\nMAC: ${d.mac}`).join('\n\n');

return [{
  json: {
    has_unknown: true,
    unknown_count: unknown.length,
    known_count: known.length,
    timestamp: formatted,
    unknown_details: unknownList
  }
}];
```

---

## IF — Bekannt oder Unbekannt

- `{{ $json.has_unknown }}` is equal to `true` (Convert types: an)
- **true** → Ollama bewertet das unbekannte Gerät → Telegram
- **false** → direkt Telegram mit fertigem Bericht (kein LLM-Call)

---

## Ollama Prompt — nur bei unbekannten Geräten

```json
{
  "model": "qwen2.5-instruct:1.5b",
  "messages": [
    {
      "role": "system",
      "content": "Du bist ein Netzwerk-Sicherheitsassistent. Antworte IMMER auf Deutsch. Maximal 3 Saetze. Nur Fakten."
    },
    {
      "role": "user",
      "content": "Ein unbekanntes Geraet wurde in meinem Heimnetz gefunden. Bewerte kurz ob es gefaehrlich sein koennte basierend auf der MAC-Adresse.\n\n{{ $json.unknown_details }}\nGefunden: {{ $json.timestamp }}"
    }
  ],
  "stream": false
}
```

---

## Telegram
- Text: `{{ $json.summary ?? $json.message ?? $json.description }}`

---

## Cron Job

```
0 0,8,16 * * * /bin/bash /etc/network-monitor/scan.sh
```

Läuft täglich um **00:00, 08:00, 16:00 Uhr**.

---

## Verhalten

| Situation | Verhalten |
|-----------|-----------|
| Alle Geräte bekannt | Direkte Telegram Nachricht mit Geräteliste — kein LLM |
| Unbekanntes Gerät | IP + MAC sichtbar, Ollama bewertet → Telegram Warnung |

---

## Changelog

### v1.1 — 03.04.2026
- Ollama nur bei unbekannten Geräten aufgerufen
- Bei bekannten Geräten direkte Telegram Nachricht mit Geräteliste und Uhrzeit
- IP und MAC des unbekannten Geräts direkt in Telegram sichtbar
- Keine Halluzination mehr bei normalem Scan

### v1.0 — 03.04.2026
- Initialer Aufbau
- nmap + arp-scan via Bash Script
- Whitelist-Check in N8N Code Node
- Ollama Zusammenfassung auf Deutsch
- Cron Job alle 8h
