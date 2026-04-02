# Mentat Network Monitor

Automatischer Heimnetzwerk-Monitor der alle 8h einen nmap + arp-scan durchführt, Geräte gegen eine Whitelist prüft und einen Bericht via Telegram meldet.

---

## Workflow

**Pipeline:**
`Cron Job (Pi)` → `scan.sh` → `Webhook (N8N)` → `Code in JavaScript (Whitelist-Check)` → `HTTP Request (Ollama)` → `Send a text message (Telegram)`

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

## Code in JavaScript — Whitelist-Check

```javascript
const body = $input.first().json.body;
const devices = body.devices || [];
const timestamp = body.timestamp;

const known = devices.filter(d => d.known === true);
const unknown = devices.filter(d => d.known === false);

const knownList = known.map(d => `[OK] ${d.name} - ${d.ip} (${d.mac})`).join('\n');
const unknownList = unknown.length > 0
  ? unknown.map(d => `[UNBEKANNT] ${d.ip} (${d.mac})`).join('\n')
  : null;

const report = unknownList
  ? `UNBEKANNTE GERAETE GEFUNDEN:\n${unknownList}\n\nBekannte Geraete:\n${knownList}`
  : `Alle Geraete bekannt:\n${knownList}`;

return [{
  json: {
    report,
    unknown_count: unknown.length,
    known_count: known.length,
    timestamp,
    has_unknown: unknown.length > 0
  }
}];
```

---

## Ollama Prompt (HTTP Request Body)

```json
{
  "model": "qwen2.5-instruct:1.5b",
  "messages": [
    {
      "role": "system",
      "content": "Du bist ein Netzwerk-Monitor. Antworte IMMER auf Deutsch. Nur Fakten, keine Erfindungen."
    },
    {
      "role": "user",
      "content": "Netzwerk-Scan abgeschlossen. Gib eine kurze sachliche Zusammenfassung in 2-3 Saetzen. Keine Vermutungen. Nur was du weisst.\n\nScan-Zeit: {{ $json.timestamp }}\nBekannte Geraete: {{ $json.known_count }}\nUnbekannte Geraete: {{ $json.unknown_count }}\nStatus: {{ $json.has_unknown == true ? 'WARNUNG - Unbekannte Geraete gefunden' : 'Alles in Ordnung' }}"
    }
  ],
  "stream": false
}
```

---

## Telegram
- Text: `{{ $json.message?.content }}`

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
| Alle Geräte bekannt | Kurzer OK-Bericht via Telegram |
| Unbekanntes Gerät | Warnung via Telegram |

---

## Changelog

### v1.0 — 03.04.2026
- Initialer Aufbau
- nmap + arp-scan via Bash Script
- Whitelist-Check in N8N Code Node
- Ollama Zusammenfassung auf Deutsch
- Cron Job alle 8h
