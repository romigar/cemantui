#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path

POST_SCRIPT = Path(__file__).resolve().parent / "post.py"


def main() -> None:
    parser = argparse.ArgumentParser(description="Saisie interactive de mots pour Cemantix/Cemantle")
    parser.add_argument("--cemantle", action="store_true", help="Utiliser Cemantle (anglais)")
    args = parser.parse_args()

    game = "Cemantle" if args.cemantle else "Cemantix"
    print(f"{game} - entrez un mot a proposer (q pour quitter)")

    while True:
        try:
            mot = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not mot or mot.lower() in {"q", "quit", "exit"}:
            break

        cmd = [sys.executable, str(POST_SCRIPT), mot]
        if args.cemantle:
            cmd.append("--cemantle")
        subprocess.run(cmd)


if __name__ == "__main__":
    main()
