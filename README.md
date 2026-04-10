# 🏠 Home Lab Setup

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Kali Linux](https://img.shields.io/badge/OS-Kali%20Linux-557C94?logo=kalilinux)
![Nobara](https://img.shields.io/badge/OS-Nobara%20KDE%2043-blue?logo=fedora)
![Docker](https://img.shields.io/badge/container-Docker-2496ED?logo=docker)
![N8N](https://img.shields.io/badge/automation-N8N-EA4B71)
![Ollama](https://img.shields.io/badge/AI-Ollama-orange)
![Tailscale](https://img.shields.io/badge/VPN-Tailscale-242424?logo=tailscale)
![Burp Suite](https://img.shields.io/badge/pentest-Burp%20Suite-FF6633)
![TryHackMe](https://img.shields.io/badge/learning-TryHackMe-212C42?logo=tryhackme)
![RPi](https://img.shields.io/badge/hardware-Raspberry%20Pi%205-C51A4A?logo=raspberrypi)
![NVIDIA](https://img.shields.io/badge/GPU-RTX%203070-76B900?logo=nvidia)

Dokumentation meines persönlichen Home Labs — aufgebaut für Ethical Hacking, Pentesting, FISI-Ausbildung und allgemeine IT-Praxis.

---

## Geräte

| Gerät | OS | Rolle |
|---|---|---|
| Tower (RTX 3070, 32GB RAM) | Nobara KDE 43 (Linux) | Gaming, Alltag, KI-Gehirn |
| Raspberry Pi 5 (8GB RAM) | Kali Linux | Hacking Station, Server |
| mentat-ai-node (RPi 5 + Hailo-10H) | Raspberry Pi OS Lite | Lokaler AI-Node, Mentat-Körper |
| Huawei Laptop | Windows 11 + Kali Live USB | Schule, FISI, Pentesting |

---

## Inhalt

- [Raspberry Pi Setup](./raspberry-pi/)
  - [Kali Linux Grundsetup](./raspberry-pi/kali-setup.md)
  - [Samba Netzwerkfreigabe](./raspberry-pi/samba.md)
  - [Tailscale VPN](./raspberry-pi/tailscale.md)
  - [Pwnagotchi & Bettercap](./raspberry-pi/pwnagotchi-bettercap.md)
  - [Offline KI & Tor](./raspberry-pi/offline-ki-tor.md)
  - [mentat-ai-node Setup](./raspberry-pi/mentat-ai-node.md)
- [Tower Setup](./windows-tower/)
  - [Nobara KDE 43 (aktuell)](./windows-tower/nobara-setup.md)
  - [Windows 11 Setup (veraltet)](./windows-tower/windows-tower-veraltet.md)
- [Networking](./networking/)
  - [Heimnetz Übersicht](./networking/heimnetz-setup.md)
- [DVWA Übungen](./dvwa/)
  - [Brute Force — Burp Suite Intruder](./dvwa/dvwa-brute-force.md)
- [Eigene Projekte](./eigene-projekte/)
  - [N8N CVE Monitor](./eigene-projekte/cve-monitor/n8n-cve-monitor.md)
  - [Mentat Network Monitor](./eigene-projekte/network-monitor/n8n-network-monitor.md)
  - [Mentat — Persönlicher Offline-KI-Assistent](./eigene-projekte/mentat-ai/README.md)

---

## Ziel

Vorbereitung auf Praktikum bei BerlinCert (IT-Security/Pentesting) und langfristig Ethical Hacker / regulatorischer Pentester.

---

## Tools & Technologien

`Kali Linux` `Nobara Linux` `Docker` `N8N` `Hailo-10H` `Metasploit` `Burp Suite` `DVWA` `Tailscale` `Samba` `TryHackMe` `Pwnagotchi` `Bettercap` `Tor` `nmap` `arp-scan` `Ollama` `llama3.1:8b` `MemPalace` `SearXNG` `Whisper` `Piper TTS`

---

> ⚠️ Dieses Repository enthält keine echten IPs, Passwörter oder sensiblen Netzwerkdaten.
