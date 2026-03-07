# Pwnagotchi Setup & Bettercap – Praxisbericht

**Zeitraum:** Freitag 22.08.2025 – Samstag 23.08.2025  
**Ergebnis:** Pwnagotchi in unter 48 Stunden, ohne Anleitung, von Null auf stabil laufend

---

## Motivation

Dieses Projekt war meine erste praktische Auseinandersetzung mit Netzwerkanalyse, Monitor-Mode und dem Zusammenspiel von Hardware und Security-Software. Keine Anleitung, kein Vorwissen zum Setup — einfach reingeworfen und durchgezogen.

Grundlage für meinen Weg in Richtung Cybersecurity und Ethical Hacking.

> ⚠️ Alle Tests wurden ausschließlich im eigenen Netzwerk oder mit expliziter Zustimmung Dritter durchgeführt. Dieses Projekt hat reinen Lern- und Ausbildungscharakter.

---

## Hardware

- Raspberry Pi Zero W
- Waveshare 3 E-Ink Display
- 25.000 mAh Powerbank (reicht 2–3 Tage Dauerbetrieb)
- Fertig zusammengebaut im Case erhalten — ohne Doku

---

## Schritt 1 – Display identifizieren & konfigurieren

Display war ein **Waveshare 3** — musste erst identifiziert werden durch Auseinanderbauen.

Konfiguration in `/etc/pwnagotchi/config.toml`:

```toml
ui.display.enabled = true
ui.display.type = "waveshare_3"
ui.display.rotation = 180
ui.fps = 1
```

---

## Schritt 2 – SSH-Verbindung einrichten

Verbindung über USB-Ethernet:

```bash
ssh pi@10.0.0.2
```

Systemd-Status prüfen:

```bash
systemctl status pwnagotchi
```

---

## Schritt 3 – Bettercap & Monitor-Mode

Bettercap benötigt zwingend eine Netzwerkkarte im **Monitor-Mode**.

### Interface vorbereiten

```bash
# Interface prüfen
ifconfig
iw dev

# WLAN entsperren falls blockiert
rfkill unblock wifi

# Monitor-Interface erstellen
sudo iw phy phy0 interface add wlan0mon type monitor
sudo ip link set wlan0mon up

# Bettercap starten
sudo bettercap -iface wlan0mon
```

### Erste Ergebnisse
- Access Points und Clients wurden sofort gelistet
- BLE-Geräte parallel erfasst:

```bash
ble.recon on
```

---

## Schritt 4 – Fehleranalyse & Fixes

### Problem: "Interface Not Up"

`wlan0mon` war erstellt aber nicht aktiv — passiert häufig nach falschem Beenden von Bettercap.

```bash
sudo ip link set wlan0mon down
sudo iw dev wlan0mon del
sudo iw phy phy0 interface add wlan0mon type monitor
sudo ip link set wlan0mon up
```

### Problem: `RTNETLINK answers: Connection timed out`

Interface im Zombie-Zustand — einzige saubere Lösung:

```bash
sudo systemctl stop pwnagotchi
sudo pkill -9 bettercap
sudo reboot
```

**Erkenntnis:** Bettercap und Pwnagotchi laufen auf demselben Interface — Konflikte sind normal und lösbar, aber man muss die Reihenfolge verstehen.

---

## Schritt 5 – Handshake-Speicherung debuggen

### Problem
Keine Handshakes im erwarteten Pfad `/root/handshakes/`.

### Analyse

```bash
ls -lh /root/handshakes/    # leer
ls -lh /home/pi/handshakes/ # hier lagen die .pcap Dateien
```

Pwnagotchi legte Handshakes nicht unter `/root/` sondern unter `/home/pi/` ab — falsch angenommener Standardpfad.

### Fix
Config angepasst auf korrekten Pfad:

```toml
main.handshakes = "/home/pi/handshakes"
```

---

## Schritt 6 – Auto-Caplet erstellen

Ziel: Kein manuelles Eintippen von Befehlen bei jedem Start.

### Caplet erstellen

```bash
nano /usr/local/share/bettercap/caplets/autohs.cap
```

```
set wifi.handshakes.dump true
set wifi.handshakes.file /home/pi/handshakes/hs-{{.timestamp}}.pcap
wifi.recon on
events.stream on
```

### In Pwnagotchi-Config einbinden

```toml
bettercap.caplet = "/usr/local/share/bettercap/caplets/autohs.cap"
main.handshakes = "/home/pi/handshakes"
```

Nach Neustart läuft alles automatisch — Pwnagotchi wird damit zum autonom arbeitenden Gerät.

---

## Lessons Learned

- Pwnagotchi ist stark von Bettercap abhängig — ohne Monitor-Mode und korrekte Pfad-Config keine Handshakes
- Default-Config ≠ funktionierende Config — immer Pfade prüfen
- Display-Identifikation wichtig — verschiedene Waveshare-Versionen verhalten sich unterschiedlich
- Reboot ist oft die schnellste Lösung bei Interface-Hängern
- BLE und WiFi lassen sich parallel nutzen

---

## Status nach 48 Stunden

- ✅ Pwnagotchi läuft stabil im Auto-Modus
- ✅ Display aktiv mit Status & Mood
- ✅ Handshakes werden automatisch gespeichert unter `/home/pi/handshakes/`
- ✅ SSH-Zugriff jederzeit via `ssh pi@10.0.0.2`
- ✅ Mobiler Betrieb mit Powerbank funktioniert

---

## Nächste Schritte

- `.pcap` Dateien mit Wireshark / Aircrack-ng analysieren
- Pwnagotchi Plugins testen (gdrivesync, UI-Plugins)
- Einsatz mit externer WLAN-Karte auf Raspberry Pi 5
- Integration ins Pentesting-Lab (TryHackMe, DVWA, FlipperZero)
