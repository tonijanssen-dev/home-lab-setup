# Kali Linux Setup — Raspberry Pi 5

## Hardware

- Raspberry Pi 5 (8GB RAM)
- 128GB Max Endurance SD Card
- Kali Linux (aktuelle Version)

## Grundkonfiguration

### SSH aktivieren

```bash
sudo systemctl enable ssh
sudo systemctl start ssh
```

Verbindung testen:
```bash
ssh kali@<PI-IP>
```

### System aktualisieren

```bash
sudo apt update && sudo apt upgrade -y
```

---

## DVWA (Damn Vulnerable Web Application)

Läuft auf Apache als lokales Übungsziel für Pentesting.

### Installation

```bash
sudo apt install apache2 mariadb-server php php-mysqli php-gd libapache2-mod-php -y
cd /var/www/html
sudo git clone https://github.com/digininja/DVWA.git
sudo chown -R www-data:www-data /var/www/html/DVWA
```

### Starten

```bash
sudo systemctl start apache2
sudo systemctl start mariadb
```

Erreichbar unter: `http://<PI-IP>/dvwa`

Standard-Login: `admin / password`

---

## Tools

| Tool | Zweck |
|---|---|
| Burp Suite | Web Application Testing |
| Metasploit | Exploitation Framework |
| TryHackMe | Geführtes Lernen (Pre-Security Pfad) |

---

## Lernstand

- TryHackMe: Pre-Security Pfad, Modul 3
- Fokus: Burp Suite + Metasploit Grundlagen
- Ziel: Vorbereitung Praktikum BerlinCert ab August 2026
