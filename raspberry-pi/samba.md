# Samba Netzwerkfreigabe — Raspberry Pi 5

Netzwerkfreigabe im Heimnetz zwischen Pi und Windows-Geräten.

## Installation

```bash
sudo apt install samba -y
```

## Konfiguration

Freigabe-Verzeichnis erstellen:
```bash
mkdir -p ~/freigabe
```

Samba-Konfiguration bearbeiten:
```bash
sudo nano /etc/samba/smb.conf
```

Folgendes am Ende einfügen:
```ini
[freigabe]
path = /home/kali/freigabe
browsable = yes
writable = yes
valid users = kali
```

NetBIOS-Name setzen (ebenfalls in smb.conf unter [global]):
```ini
netbios name = kali-raspi
```

## Samba-Passwort setzen

```bash
sudo smbpasswd -a kali
```

## Dienst starten

```bash
sudo systemctl enable smbd
sudo systemctl start smbd
```

## Zugriff von Windows

```
\\<PI-IP>\freigabe
\\kali-raspi\freigabe
```
