#!/usr/bin/env python3

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo
from rich import color
from rich.console import Console

console = Console()


def day_number(cemantle: bool) -> int:
    if cemantle:
        epoch = date(2022, 4, 4)
        tz = ZoneInfo("America/Los_Angeles")
    else:
        epoch = date(2022, 3, 2)
        tz = ZoneInfo("Europe/Paris")
    today = datetime.now(tz).date()
    return (today - epoch).days


def load_words(path: Path) -> list[str]:
    words = []
    for line in path.read_text(encoding="utf-8").splitlines():
        word = line.strip()
        if word and not word.startswith("#"):
            words.append(word)
    return words


RESULTS_FILE = Path("resultats.txt")
RESULTS_META = Path("resultats.meta")
RESULTS_HEADER = "mot\tscore\tposition\tstatus"


def read_results_meta() -> tuple[int | None, bool | None]:
    if not RESULTS_META.is_file():
        return None, None
    lines = RESULTS_META.read_text(encoding="utf-8").splitlines()
    if not lines:
        return None, None
    day = int(lines[0])
    cemantle = len(lines) > 1 and lines[1].lower() == "true"
    return day, cemantle


def count_results_lines() -> int:
    if not RESULTS_FILE.is_file():
        return 0
    return len(RESULTS_FILE.read_text(encoding="utf-8").splitlines())


def write_results_meta(day: int, cemantle: bool) -> None:
    line_count = count_results_lines()
    RESULTS_META.write_text(f"{day}\n{cemantle}\n{line_count}\n", encoding="utf-8")


def ensure_results_file(day: int, cemantle: bool) -> None:
    stored_day, stored_cemantle = read_results_meta()
    if (
        stored_day != day
        or stored_cemantle != cemantle
        or not RESULTS_FILE.is_file()
        or RESULTS_FILE.stat().st_size == 0
    ):
        RESULTS_FILE.write_text(RESULTS_HEADER + "\n", encoding="utf-8")
        write_results_meta(day, cemantle)


def parse_result_line(line: str) -> dict:
    parts = line.split("\t")
    while len(parts) < 4:
        parts.append("")
    score = float(parts[1]) if parts[1] else None
    position = int(parts[2]) if parts[2] else None
    return {
        "mot": parts[0],
        "score": score,
        "position": position,
        "status": parts[3],
    }


def load_results() -> list[dict]:
    if not RESULTS_FILE.is_file():
        return []
    lines = RESULTS_FILE.read_text(encoding="utf-8").splitlines()
    if not lines:
        return []
    data_lines = lines[1:] if lines[0] == RESULTS_HEADER else lines
    return [parse_result_line(line) for line in data_lines if line.strip()]


def write_results(results: list[dict], day: int, cemantle: bool) -> None:
    lines = [RESULTS_HEADER, *[format_result_line(r) for r in results]]
    RESULTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_results_meta(day, cemantle)


def append_result(result: dict, day: int, cemantle: bool) -> None:
    ensure_results_file(day, cemantle)
    results = load_results()
    results.append(result)
    results.sort(
        key=lambda r: r["score"] if r["score"] is not None else float("-inf"),
        reverse=True,
    )
    write_results(results, day, cemantle)


def format_result_line(result: dict) -> str:
    parts = [result["mot"]]
    if result.get("score") is not None:
        parts.append(str(result["score"]))
    else:
        parts.append("")
    if result.get("position") is not None:
        parts.append(str(result["position"]))
    else:
        parts.append("")
    parts.append(result.get("status", ""))
    return "\t".join(parts)


def post_word(mot: str, cemantle: bool) -> tuple[int, dict]:
    origin = "https://cemantle.certitudes.org" if cemantle else "https://cemantix.certitudes.org"
    day = day_number(cemantle)
    url = f"{origin}/score?n={day}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        ),
        "Origin": origin,
        "Referer": f"{origin}/",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        req = Request(url, data=urlencode({"word": mot}).encode(), headers=headers, method="POST")
        with urlopen(req) as resp:
            response = json.loads(resp.read().decode())
    except (HTTPError, URLError) as err:
        print(f"Requete echouee : {err}", file=sys.stderr)
        return 1, {"mot": mot, "status": f"Erreur reseau : {err}"}

    exit_code = 0
    result: dict = {"mot": mot, "score": None, "position": None, "status": ""}

    if response.get("r"):
        print(f"Numero de jour invalide ({day}).", file=sys.stderr)
        exit_code = 1
        result["status"] = f"Jour invalide ({day})"
    elif response.get("e"):
        print(f"Mot inconnu ou invalide : {mot}", file=sys.stderr)
        exit_code = 1
        result["status"] = "Mot inconnu"
    else:
        score = float(response["s"])
        proximite = round(score * 100, 2)
        position = int(response["p"]) if response.get("p") is not None else None

        result["score"] = proximite
        result["position"] = position

        console.print(f"Mot : {mot}", style="bold")

        if score >= 1.0:
            style = "green"
            text = "Trouve !"
        elif score >= 0.5:
            style = "red"
            text = "Tres chaud !"
        elif score >= 0.25:
            style = "orange3"
            text = "Tiede."
        else:
            style = "cyan"
            text = "Froid."

        result["status"] = text

        console.print(f"Score : {proximite}", style=style)
        console.print(text, style=style)
        if position is not None:
            console.print(f"Position : {position}", style=style)

    print()

    append_result(result, day, cemantle)

    return exit_code, result


def main() -> None:
    parser = argparse.ArgumentParser(description="Envoyer un mot a l'API Cemantix/Cemantle")
    parser.add_argument("mot", nargs="?", help="Mot a proposer")
    parser.add_argument("-f", "--file", type=Path, help="Fichier de mots (un par ligne)")
    parser.add_argument("--cemantle", action="store_true", help="Utiliser Cemantle (anglais)")
    args = parser.parse_args()

    if args.file and args.mot:
        parser.error("Utiliser soit un mot, soit --file, pas les deux.")
    if not args.file and not args.mot:
        parser.error("Mot ou --file requis.")

    if args.file:
        if not args.file.is_file():
            print(f"Fichier introuvable : {args.file}", file=sys.stderr)
            sys.exit(1)

        words = load_words(args.file)
        if not words:
            print(f"Aucun mot dans {args.file}", file=sys.stderr)
            sys.exit(1)

        exit_code = 0
        for i, mot in enumerate(words):
            if i > 0:
                print("-" * 40)
            code, _ = post_word(mot, args.cemantle)
            if code != 0:
                exit_code = code
        sys.exit(exit_code)

    code, _ = post_word(args.mot, args.cemantle)
    sys.exit(code)


if __name__ == "__main__":
    main()
