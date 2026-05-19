# AmiBlitz3 Ontwikkelworkflow

Dit project bevat alles wat je nodig hebt om AmiBlitz3 te programmeren
vanuit VS Code op je Mac, met automatische upload en compilatie naar je Amiga.

## Overzicht

```
VS Code (Mac)  -->  watch_and_deploy.py  -->  FTP  -->  Amiga
     |                                                    |
  Jij slaat op                                    amiga_build.rexx
  .bb2 bestand                                    compileert & start
```

## Snelstart (alles in 1x starten)

```bash
cd /Volumes/M4-Lexar/Development/Ftp
./start_dev.sh
```

Dit start de FTP-server en file watcher in 1 commando.

Andere handige commando's:

```bash
./start_dev.sh status   # toon of alles draait
./start_dev.sh stop     # stop alles
```

## 1. FTP-server (voor bestandsoverdracht)

De FTP-server draait op je Mac, zodat de Amiga bestanden kan ophalen.

```bash
cd /Volumes/M4-Lexar/Development/Ftp
sudo python3 ftp_server.py
```

- Poort: **21** (standaard FTP)
- Gebruiker: `amiga` / Wachtwoord: `amiga`
- Gedeelde map: `share/`

## 2. File Watcher (voor automatische upload)

De file watcher ziet wanneer je een bestand opslaat in VS Code en
uploadt het automatisch naar de Amiga.

```bash
# Installeer watchdog (eenmalig)
python3 -m pip install watchdog

# Start de watcher voor je project
python3 watch_and_deploy.py /pad/naar/amiblitz3/project
```

De eerste keer wordt `watch_config.json` aangemaakt. Pas daarin aan:

```json
{
    "ftp": {
        "host": "192.168.68.70",
        "port": 21,
        "user": "amiga",
        "password": "amiga",
        "remote_dir": "Projects/MyBlitzProject"
    },
    "watch": {
        "extensions": [".bb2", ".ab3", ".asm", ".inc", ".bm"]
    }
}
```

## 3. Amiga Build Script (voor compilatie)

Het AREXX script `amiga_build.rexx` moet op de Amiga draaien.
Het compileert je project en start het programma.

**Installatie op de Amiga:**

1. Kopieer `amiga_build.rexx` naar je Amiga (via FTP)
2. Open een shell op de Amiga en typ:
   ```
   RX amiga_build.rexx
   ```
3. Of zet het in `SYS:WBStartup` voor automatisch starten

**Configuratie in het script:**

```rexx
PROJECT_DIR = "DH0:Projects/MyBlitzProject/"
MAIN_FILE = "main.bb2"
COMPILER = "Amiblitz3:Amiblitz3"
```

## 4. Complete Workflow

1. **Start alles** met 1 commando:
   ```bash
   cd /Volumes/M4-Lexar/Development/Ftp
   ./start_dev.sh
   ```

2. **Start het build script** op de Amiga:
   ```
   RX amiga_build.rexx
   ```

3. **Programmeer in VS Code** en sla op (Ctrl+S)

4. **Automatisch** gebeurt dan:
   - Bestand wordt geupload naar de Amiga via FTP
   - Amiga compileert met AmiBlitz3
   - Het programma wordt gestart

## Bestanden in dit project

| Bestand | Doel |
|---------|------|
| `start_dev.sh` | **Startscript** - start FTP + watcher in 1x |
| `ftp_server.py` | FTP-server voor bestandsoverdracht |
| `watch_and_deploy.py` | File watcher + auto-upload |
| `watch_config.json` | Configuratie voor file watcher |
| `amiga_build.rexx` | AREXX script voor Amiga (compile + run) |
| `share/` | Gedeelde FTP-map |
| `requirements.txt` | Python dependencies |

## Tips

- **Eerste keer**: Maak een simpel `.bb2` bestand aan en test of de
  workflow werkt voordat je een groot project begint.
- **Debuggen**: Gebruik `--debug` op de FTP-server om te zien wat er
  gebeurt: `sudo python3 ftp_server.py --debug`
- **Alleen watchen**: Gebruik `--no-ftp` om alleen te testen of de
  file watcher werkt zonder te uploaden.
- **Logs bekijken**:
  ```bash
  tail -f /tmp/amiga_ftp_server.log   # FTP logs
  tail -f /tmp/amiga_watch.log        # File watcher logs
  ```
