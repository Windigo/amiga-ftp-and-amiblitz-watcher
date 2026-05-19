#!/usr/bin/env python3
"""
Eenvoudige FTP-server voor Amiga/Pistorm/CaffeineOS.

Gebruik:
  sudo python3 ftp_server.py

Verbind vanaf je Amiga met:
  host = je Mac-adres of localhost
  poort = 21 (standaard FTP-poort)
  gebruiker = amiga
  wachtwoord = amiga

Gedeelde bestanden staan in de map `share`.
"""

import os
import argparse
import logging
import socket

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


class AmigaFTPHandler(FTPHandler):
    """FTP handler met extra compatibiliteit voor Amiga FTP-clients."""

    # Amiga FTP clients (vooral oudere) werken beter met deze instellingen:
    # - Geen UTF-8 opties (sommige Amiga clients snappen dat niet)
    # - Geen MLSD/MLST (sommige clients gebruiken alleen LIST)
    # - Alleen ASCII banner (geen speciale tekens)
    use_mlst = False
    use_mlsd = False
    use_utf8 = False

    def on_connect(self):
        self.log_info(f"Connectie vanaf {self.remote_ip}:{self.remote_port}")

    def on_disconnect(self):
        self.log_info(f"Verbinding verbroken: {self.remote_ip}:{self.remote_port}")

    def on_login(self, username):
        self.log_info(f"Gebruiker ingelogd: {username}")

    def on_logout(self, username):
        self.log_info(f"Gebruiker uitgelogd: {username}")

    def on_file_sent(self, file):
        self.log_info(f"Bestand verstuurd: {file}")

    def on_file_received(self, file):
        self.log_info(f"Bestand ontvangen: {file}")

    def on_incomplete_file_received(self, file):
        self.log_info(f"Onvolledig bestand ontvangen: {file}")

    def ftp_LANG(self, cmd, arg):
        """Ondersteun LANG commando (sommige Amiga clients sturen dit)."""
        self.respond("200 OK")

    def ftp_feat(self, cmd, arg):
        """Stuur minimale FEAT response voor betere compatibiliteit."""
        self.respond("211-Features:")
        self.respond(" PASV")
        self.respond("211 End")

    def ftp_syst(self, cmd, arg):
        """Stuur een eenvoudig SYST antwoord."""
        self.respond("215 UNIX Type: L8")

    def ftp_help(self, cmd, arg):
        """Stuur een eenvoudig HELP antwoord."""
        self.respond("214 The following commands are recognized:")
        self.respond("214  USER PASS ACCT CWD CDUP SMNT QUIT REIN PORT PASV")
        self.respond("214  TYPE STRU MODE RETR STOR STOU APPE LIST NLST")
        self.respond("214  SYST HELP PWD MKD RMD RNFR RNTO DELE SITE")
        self.respond("214  SIZE MDTM FEAT LANG")
        self.respond("214 Direct comments to admin")


def get_local_ip():
    """Probeer het lokale IP-adres te vinden voor masquerade."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Eenvoudige FTP-server voor Amiga")
    parser.add_argument("--host", default="0.0.0.0", help="Host om te binden")
    parser.add_argument("--port", type=int, default=21, help="FTP-poort (standaard: 21)")
    parser.add_argument("--user", default="amiga", help="FTP-gebruiker")
    parser.add_argument("--passwd", default="amiga", help="FTP-wachtwoord")
    parser.add_argument("--dir", default="share", help="Map om te delen")
    parser.add_argument(
        "--masquerade",
        type=str,
        default=None,
        help="Masquerade IP (nodig als Amiga via NAT verbindt, "
        "bijv. PiStorm slirp). Als niet opgegeven, wordt "
        "automatisch het lokale IP gebruikt.",
    )
    parser.add_argument(
        "--pasv-min",
        type=int,
        default=30000,
        help="Minimale passive poort (standaard: 30000)",
    )
    parser.add_argument(
        "--pasv-max",
        type=int,
        default=30999,
        help="Maximale passive poort (standaard: 30999)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Uitgebreide debug logging",
    )
    args = parser.parse_args()

    os.makedirs(args.dir, exist_ok=True)

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    authorizer = DummyAuthorizer()
    authorizer.add_user(args.user, args.passwd, args.dir, perm="elradfmwMT")
    authorizer.add_anonymous(args.dir, perm="elr")

    handler = AmigaFTPHandler
    handler.authorizer = authorizer
    handler.banner = "Amiga FTP server ready"

    # Masquerade address voor NAT (PiStorm slirp)
    masquerade_ip = args.masquerade
    if masquerade_ip is None:
        masquerade_ip = get_local_ip()
    if masquerade_ip:
        handler.masquerade_address = masquerade_ip
        print(f"Masquerade-adres: {masquerade_ip}")

    # Passive ports range
    handler.passive_ports = range(args.pasv_min, args.pasv_max + 1)

    address = (args.host, args.port)
    server = FTPServer(address, handler)

    print(f"FTP-server gestart op ftp://{args.host}:{args.port}")
    print(f"Gebruiker: {args.user} / Wachtwoord: {args.passwd}")
    print(f"Map: {os.path.abspath(args.dir)}")
    print(f"Passive ports: {args.pasv_min}-{args.pasv_max}")
    print("Stop met Ctrl-C")

    server.max_cons = 5
    server.max_cons_per_ip = 2
    server.serve_forever()


if __name__ == "__main__":
    main()
