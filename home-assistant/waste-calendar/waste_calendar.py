"""Import a yearly waste collection plan (Excel, one column per waste type) into a
Home Assistant *Local Calendar* ICS file, in the same event format as the existing entries.

Two sub-commands:

  compare  <calendar.ics> <plan.xlsx>
      Matches every existing calendar title against every Excel column and prints how many
      dates overlap. Use it once with last year's plan to find out which column belongs to
      which calendar title (e.g. which "Sprengel"/district is yours).

  build    <calendar.ics> <plan.xlsx> <year> <out.ics> [--pdf plan.pdf]
      Appends the events of <year> for the columns mapped in config.json and writes <out.ics>.
      Refuses to run if a mapped column header is missing, a date is outside <year>,
      an event already exists, or (with --pdf) a date is not printed in the PDF plan.

Configuration lives in config.json next to this script (not committed, see config.example.json).
"""
import argparse
import json
import re
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent


def load_config():
    path = HERE / "config.json"
    if not path.exists():
        sys.exit(f"config.json missing - copy config.example.json to {path} and adjust it")
    return json.loads(path.read_text(encoding="utf-8"))


def read_plan(xlsx_path, header_row):
    """Return {column header: sorted list of dates} for the first sheet."""
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    header = rows[header_row - 1]
    columns = defaultdict(list)
    for row in rows[header_row:]:
        for i, value in enumerate(row):
            if isinstance(value, datetime) and i < len(header) and header[i]:
                columns[(i, str(header[i]).strip())].append(value.date())
    return rows[0], {k: sorted(v) for k, v in columns.items()}


def read_ics(path):
    raw = Path(path).read_bytes()
    newline = "\r\n" if b"\r\n" in raw else "\n"
    text = raw.decode("utf-8")
    unfolded = text.replace("\r\n ", "").replace("\n ", "")
    events = defaultdict(set)
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", unfolded, re.S):
        summary = re.search(r"^SUMMARY:(.*)$", block, re.M).group(1).strip()
        day = re.search(r"^DTSTART[^:]*:(\d{8})", block, re.M).group(1)
        events[summary].add(day)
    return text, newline, events


def cmd_compare(args, cfg):
    _, _, events = read_ics(args.calendar)
    _, columns = read_plan(args.plan, cfg.get("header_row", 2))
    print("overlap  calendar-title  ~  excel-column   (common / calendar / excel)")
    for title, days in sorted(events.items()):
        for (idx, head), dates in columns.items():
            common = len(days & {d.strftime("%Y%m%d") for d in dates})
            if common:
                print(f"{title:18} ~ [{idx}] {head:32} {common:3} / {len(days):3} / {len(dates):3}")


def pdf_text(path):
    from pypdf import PdfReader

    return "\n".join(page.extract_text() or "" for page in PdfReader(path).pages)


def cmd_build(args, cfg):
    text, nl, events = read_ics(args.calendar)
    first_row, columns = read_plan(args.plan, cfg.get("header_row", 2))
    by_index = {idx: (head, dates) for (idx, head), dates in columns.items()}

    planned = []
    for col in cfg["columns"]:
        idx, head, title = col["index"], col["header"], col["title"]
        if idx not in by_index or by_index[idx][0] != head:
            sys.exit(f"column {idx} is not '{head}' in this plan (found: {by_index.get(idx, ('-',))[0]}) - check config")
        for d in by_index[idx][1]:
            if d.year != args.year:
                sys.exit(f"date {d} in column '{head}' is not in {args.year}")
            planned.append((d, title))
    planned.sort()

    prefix = cfg.get("summary_prefix", "")
    duplicates = [(d, t) for d, t in planned if d.strftime("%Y%m%d") in events.get(prefix + t, set())]
    if duplicates:
        sys.exit(f"already in calendar: {duplicates[:5]} ...")

    if args.pdf:
        pdf = pdf_text(args.pdf)
        missing = [f"{d:%d.%m.} {t}" for d, t in planned if f"{d:%d.%m.}" not in pdf]
        if missing:
            sys.exit(f"not found in PDF: {missing}")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tz = cfg.get("timezone", "Europe/Vienna")
    start, end = cfg.get("start", "060000"), cfg.get("end", "220000")
    blocks = []
    for d, title in planned:
        day = d.strftime("%Y%m%d")
        lines = [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@{cfg.get('uid_domain', 'example.invalid')}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;TZID={tz}:{day}T{start}",
            f"DTEND;TZID={tz}:{day}T{end}",
            f"SUMMARY:{prefix}{title}",
        ]
        if cfg.get("description"):
            lines.append("DESCRIPTION:" + cfg["description"].replace(",", "\\,"))
        if cfg.get("category"):
            lines.append("CATEGORIES:" + cfg["category"])
        if cfg.get("alarm_trigger"):
            lines += [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                "DESCRIPTION:" + cfg.get("alarm_text", "{title}").format(title=title),
                "TRIGGER:" + cfg["alarm_trigger"],
                "END:VALARM",
            ]
        lines.append("END:VEVENT")
        blocks.append(nl.join(lines))

    pos = text.rstrip().rfind("END:VCALENDAR")
    if pos < 0:
        sys.exit("END:VCALENDAR not found")
    out = text[:pos] + nl.join(blocks) + nl + text[pos:]
    Path(args.out).write_bytes(out.encode("utf-8"))

    print("plan title:", first_row[0])
    print("new per title:", dict(Counter(t for _, t in planned)))
    print("new total:", len(planned), "|", planned[0][0], "to", planned[-1][0])
    print("events before/after:", text.count("BEGIN:VEVENT"), "/", out.count("BEGIN:VEVENT"))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare")
    c.add_argument("calendar")
    c.add_argument("plan")
    b = sub.add_parser("build")
    b.add_argument("calendar")
    b.add_argument("plan")
    b.add_argument("year", type=int)
    b.add_argument("out")
    b.add_argument("--pdf")
    args = p.parse_args()
    cfg = load_config()
    {"compare": cmd_compare, "build": cmd_build}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
