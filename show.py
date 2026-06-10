#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from post import RESULTS_HEADER, parse_result_line, result_style, results_paths

console = Console()
sys.stdout.reconfigure(encoding="utf-8")

def read_meta_details(cemantle: bool) -> tuple[int | None, bool | None, int | None]:
    _, meta_file = results_paths(cemantle)
    if not meta_file.is_file():
        return None, None, None
    lines = meta_file.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None, None, None
    day = int(lines[0])
    cemantle = len(lines) > 1 and lines[1].lower() == "true"
    line_count = int(lines[2]) if len(lines) > 2 else None
    return day, cemantle, line_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Afficher les resultats Cemantix/Cemantle")
    parser.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Fichier de resultats (defaut: resultats.txt ou resultats_cemantle.txt)",
    )
    parser.add_argument("--cemantle", action="store_true", help="Afficher les resultats Cemantle")
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        metavar="N",
        help="Afficher seulement les N premiers resultats",
    )
    args = parser.parse_args()

    results_file = args.file if args.file else results_paths(args.cemantle)[0]

    if not results_file.is_file():
        print(f"Fichier introuvable : {results_file}", file=sys.stderr)
        sys.exit(1)

    results = load_results_from(results_file)
    if not results:
        console.print("Aucun resultat.", style="yellow")
        sys.exit(0)

    day, _, line_count = read_meta_details(args.cemantle)
    game = "Cemantle" if args.cemantle else "Cemantix"

    if day is not None:
        console.print(f"{game} - jour #{day}", style="bold")
    else:
        console.print(game, style="bold")

    total = len(results)
    displayed = results[: args.limit] if args.limit is not None else results

    if args.limit is not None:
        console.print(f"{len(displayed)} / {total} proposition(s) affichee(s)", style="dim")
    else:
        console.print(f"{total} proposition(s)", style="dim")
    if line_count is not None:
        console.print(f"{line_count} ligne(s) dans {results_file.name}", style="dim")
    console.print()

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", style="dim", justify="right")
    table.add_column("Mot")
    table.add_column("Score", justify="right")
    table.add_column("Position", justify="right")
    table.add_column("Status")

    for i, result in enumerate(displayed, start=1):
        style = result_style(result)
        score = "" if result.get("score") is None else str(result["score"])
        position = "" if result.get("position") is None else str(result["position"])
        table.add_row(
            str(i),
            result["mot"],
            score,
            position,
            result.get("status", ""),
            style=style,
        )

    console.print(table)


def load_results_from(path: Path) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    data_lines = lines[1:] if lines[0] == RESULTS_HEADER else lines
    return [parse_result_line(line) for line in data_lines if line.strip()]


if __name__ == "__main__":
    main()
