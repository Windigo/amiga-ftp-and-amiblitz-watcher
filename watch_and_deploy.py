#!/usr/bin/env python3
"""
File watcher voor AmiBlitz3 ontwikkeling.

Houdt een projectfolder in de gaten en upload gewijzigde bestanden
automatisch naar de Amiga via FTP. Stuurt daarna een signaal naar
de Amiga om te compileren en het programma te starten.

Gebruik:
  python3 watch_and_deploy.py /pad/naar/amiblitz3/project
"""

import os
import sys
import time
import json
import socket
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Watchdog niet geinstalleerd. Installeer met:")
    print("  python3 -m pip install watchdog")
    sys.exit(1)


# Configuratie
CONFIG_FILE = Path(__file__).parent / "watch_config.json"

DEFAULT_CONFIG = {
    "ftp": {
        "host": "192.168.68.70",       # Amiga IP
        "port": 21,                     # FTP poort op Amiga (als die een server draait)
        "user": "amiga",
        "password": "amiga",
        "remote_dir": "Projects/MyBlitzProject"
    },
    "amiga": {
        "signal_port": 9999,            # Poort voor signaal naar Amiga
        "signal_host": "192.168.68.70", # Amiga IP voor signaal
        "compile_command": "amiblitz3 compile"
    },
    "watch": {
        "extensions": [".bb2", ".ab3", ".asm", ".inc", ".bm"],
        "ignore_dirs": [".git", "__pycache__", ".venv"]
    }
}


def load_config():
    """Laad configuratie, maak default als die niet bestaat."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    else:
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"Configuratie aangemaakt: {CONFIG_FILE}")
        print("Pas de instellingen aan voor jouw situatie.")
        return DEFAULT_CONFIG


class AmiBlitzHandler(FileSystemEventHandler):
    """Handler die reageert op bestandswijzigingen."""

    def __init__(self, config, project_dir):
        self.config = config
        self.project_dir = Path(project_dir).resolve()
        self.last_upload = {}
        self.debounce_seconds = 1  # Wacht 1 sec na laatste wijziging

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        ext = file_path.suffix.lower()

        # Alleen relevante extensies
        if ext not in self.config["watch"]["extensions"]:
            return

        # Check of het in genegeerde mappen zit
        for ignore in self.config["watch"]["ignore_dirs"]:
            if ignore in file_path.parts:
                return

        # Debounce: wacht tot bestand klaar is met schrijven
        now = time.time()
        last = self.last_upload.get(str(file_path), 0)
        if now - last < self.debounce_seconds:
            return
        self.last_upload[str(file_path)] = now

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Wijziging gedetecteerd: {file_path.name}")

        # Relatief pad tov project
        try:
            rel_path = file_path.relative_to(self.project_dir)
        except ValueError:
            rel_path = file_path.name

        # Upload via FTP
        self.upload_file(file_path, rel_path)

    def upload_file(self, local_path, remote_rel_path):
        """Upload een bestand naar de Amiga via FTP."""
        ftp_config = self.config["ftp"]
        remote_path = f"{ftp_config['remote_dir']}/{remote_rel_path}"

        try:
            import ftplib
            ftp = ftplib.FTP()
            ftp.connect(ftp_config["host"], ftp_config["port"], timeout=10)
            ftp.login(ftp_config["user"], ftp_config["password"])

            # Zorg dat de remote directory bestaat
            dirs = str(Path(remote_path).parent).split("/")
            for d in dirs:
                if d:
                    try:
                        ftp.cwd(d)
                    except ftplib.error_perm:
                        ftp.mkd(d)
                        ftp.cwd(d)

            # Ga naar root van remote dir
            ftp.cwd("/")
            try:
                ftp.cwd(ftp_config["remote_dir"])
            except ftplib.error_perm:
                ftp.mkd(ftp_config["remote_dir"])
                ftp.cwd(ftp_config["remote_dir"])

            # Upload het bestand
            with open(local_path, "rb") as f:
                ftp.storbinary(f"STOR {Path(remote_path).name}", f)

            ftp.quit()
            print(f"  -> Geupload: {remote_rel_path}")

            # Stuur signaal naar Amiga om te compileren
            self.signal_amiga(remote_rel_path)

        except Exception as e:
            print(f"  -> Fout bij upload: {e}")

    def signal_amiga(self, changed_file):
        """Stuur een signaal naar de Amiga dat er een bestand is gewijzigd."""
        amiga_config = self.config["amiga"]
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((amiga_config["signal_host"], amiga_config["signal_port"]))
            message = json.dumps({
                "action": "file_changed",
                "file": str(changed_file),
                "project": str(self.project_dir.name)
            })
            s.sendall(message.encode() + b"\n")
            s.close()
            print(f"  -> Signaal gestuurd naar Amiga")
        except Exception as e:
            print(f"  -> Kon geen signaal sturen naar Amiga: {e}")
            print(f"     (Amiga luistert niet op poort {amiga_config['signal_port']})")


def main():
    parser = argparse.ArgumentParser(
        description="File watcher voor AmiBlitz3 - upload automatisch naar Amiga"
    )
    parser.add_argument(
        "project_dir",
        nargs="?",
        default=".",
        help="Pad naar het AmiBlitz3 project (standaard: huidige map)"
    )
    parser.add_argument(
        "--no-ftp",
        action="store_true",
        help="Alleen watchen, niet uploaden (voor testen)"
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Projectmap bestaat niet: {project_dir}")
        sys.exit(1)

    config = load_config()

    print("=" * 50)
    print("AmiBlitz3 File Watcher")
    print("=" * 50)
    print(f"Project: {project_dir}")
    print(f"Amiga:   {config['ftp']['host']}")
    print(f"Remote:  {config['ftp']['remote_dir']}")
    print(f"Upload:  {'UIT' if args.no_ftp else 'AAN'}")
    print("-" * 50)
    print("Wacht op wijzigingen... (Ctrl-C om te stoppen)")
    print("=" * 50)

    event_handler = AmiBlitzHandler(config, project_dir)
    observer = Observer()
    observer.schedule(event_handler, str(project_dir), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStoppen...")
        observer.stop()
    observer.join()
    print("Gestopt.")


if __name__ == "__main__":
    main()
