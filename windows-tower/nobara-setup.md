# Windows Tower – Nobara KDE 43 (aktuelles Setup)

> Der Tower lief ursprünglich unter Windows 11. Nach dem Wechsel zu Linux ist Nobara KDE 43 das aktuelle Betriebssystem. Die Windows-Konfiguration ist unter [Windows Tower (veraltetes Setup)](windows-tower-veraltet.md) dokumentiert.

---

## Hardware

| Komponente | Details |
|---|---|
| CPU | Intel Core i7-12700F |
| RAM | 32GB DDR4-3200 (Corsair 2x16GB, XMP aktiv) |
| GPU | ZOTAC RTX 3070 8GB GDDR6 |
| Mainboard | Medion B660M Gaming |
| IP | 192.168.0.2 (fest via Router DHCP-Reservierung) |

---

## Betriebssystem

- **OS:** Nobara KDE 43 (64-bit)
- **Basis:** Fedora-basiert, Gaming-optimiert
- **Desktop:** KDE Plasma

---

## Konfiguration

### Samba (Netzwerkfreigabe)

Dauerhaft via fstab gemountet unter `/mnt/samba`.

### KeePass

Passwortdatenbank unter `~/Dokumente/KeePass/`

### Flatpak Apps

```bash
# Filius (Netzwerksimulation für FISI-Schule)
flatpak install filius

# IntelliJ IDEA (Java Entwicklung)
flatpak install intellij-idea
```

### Gaming

- **Crimson Desert:** läuft via Proton Hotfix
  - `DXVK_HDR=0`
  - Raytracing: aus
  - DLSS 4.5 Quality

---

## Geplant

- Ollama + Open WebUI werden zukünftig auf dem **mentat-ai-node** laufen, nicht mehr auf dem Tower
- Tower bleibt Gaming- und Alltags-Station

---

> ⚠️ Dieses Repository enthält keine echten IPs, Passwörter oder sensiblen Netzwerkdaten.
