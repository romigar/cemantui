#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from post import RESULTS_FILE, RESULTS_HEADER, RESULTS_META, parse_result_line, result_style

console = Console()


def read_meta_details() -> tuple[int | None, bool | None, int | None]:
    if not RESULTS_META.is_file():
        return None, None, None
    lines = RESULTS_META.read_text(encoding="utf-8").splitlines()
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
        default=RESULTS_FILE,
        help="Fichier de resultats (defaut: resultats.txt)",
    )
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        metavar="N",
        help="Afficher seulement les N premiers resultats",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        print(f"Fichier introuvable : {args.file}", file=sys.stderr)
        sys.exit(1)

    results = load_results_from(args.file)
    if not results:
        console.print("Aucun resultat.", style="yellow")
        sys.exit(0)

    day, cemantle, line_count = read_meta_details()
    game = "Cemantle" if cemantle else "Cemantix"

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
        console.print(f"{line_count} ligne(s) dans {args.file.name}", style="dim")
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
