#!/usr/bin/env python3
"""Regenerate src/data/items.json from the author's permissions spreadsheet.

Reads the numbered rows of `ignore/Permission Brotherhood Hell - WEB IMAGES.csv`
and writes one catalog item per row, so the site shows her actual data instead
of placeholders.

Two principles:

* Never invent. A field the spreadsheet leaves blank is emitted as an empty
  string, and the name of the missing field is recorded in the item's `needs`
  array so the gap is visible on the page rather than papered over.
* Never guess a cross-reference. A production or person link is only made when
  the spreadsheet's wording resolves to a real id in productions.json /
  people.json. Anything ambiguous is left unlinked and reported.

Usage:  python3 scripts/import-items/build.py [--report]
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "ignore" / "Permission Brotherhood Hell - WEB IMAGES.csv"
ITEMS_PATH = ROOT / "src" / "data" / "items.json"
PEOPLE_PATH = ROOT / "src" / "data" / "people.json"
PRODUCTIONS_PATH = ROOT / "src" / "data" / "productions.json"
ASSETS = ROOT / "src" / "assets" / "items"

# Column positions. The sheet has two unnamed empty columns (one after Credit
# Line, one trailing), so read by index rather than by header name.
ID, CATEGORY, CAPTION, CREATOR, DATE, CREDIT, _BLANK, OWNER, SOURCE, \
    COPYRIGHT, NOTES, RIGHTS = range(12)

# Spreadsheet production wording -> appendix title. These are the titles that
# do not match productions.json verbatim; each was checked against the
# appendix by hand.
TITLE_ALIASES = {
    "decision": "The Decision",
    "life is a dream": "Life is a Dream (La Vida Es Sueño)",
    "the ox cart": "The Oxcart (La Carreta)",
    "the oxcart": "The Oxcart (La Carreta)",
}

# Titles that legitimately match more than one production, or none at all.
# Left unlinked on purpose -- resolving them needs the author, not a guess.
NEEDS_AUTHOR = {
    "jericho-jim crow": "ran in both 1964 and 1968 - which production?",
    "holy moses": "no production of this name in the appendix",
}

MEDIA_TAGS = [
    ("playbill", r"\bplaybill\b"),
    ("program", r"\bprogram(me)?\b"),
    ("poster", r"\bposter|showcard\b"),
    ("clipping", r"\bclipping|review|herald tribune|nytimes|new york times\b"),
    ("letter", r"\bletter\b"),
    ("flyer", r"\bflyer\b"),
    ("plan", r"\bbuilding plans|seating diagram\b"),
    ("portrait", r"\bportrait|headshot\b"),
]


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return re.sub(r"-{2,}", "-", value)


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def asset_stem(raw_id: str) -> str:
    """Fig1 / Fig01 / Folder12 -> the stem convert_images.py writes."""
    match = re.match(r"(?i)^fig\s*0*(\d+)$", raw_id)
    if match:
        return f"fig{int(match.group(1)):02d}"
    if raw_id.lower().startswith("folder12"):
        return "folder12"
    return slugify(raw_id)


def short_title(caption: str, fallback: str) -> str:
    """A card-sized title: the caption, truncated on a word boundary.

    Deliberately does NOT split on the first sentence. Captions here are full
    of abbreviations -- "Rev. Stitt...", "Charles A. Collins..." -- and a
    sentence split turns those into titles reading "Rev" and "Charles A".
    """
    if not caption:
        return fallback
    text = " ".join(caption.split()).strip()
    if len(text) > 72:
        text = text[:72].rsplit(" ", 1)[0].rstrip(",;:") + "…"
    else:
        text = text.rstrip(".")
    return text or fallback


def main() -> int:
    if not CSV_PATH.exists():
        print(f"spreadsheet not found: {CSV_PATH}", file=sys.stderr)
        return 1

    people = json.loads(PEOPLE_PATH.read_text())
    productions = json.loads(PRODUCTIONS_PATH.read_text())
    people_by_name = {norm(p["name"]): p["id"] for p in people}
    productions_by_title: dict[str, list[str]] = {}
    for prod in productions:
        productions_by_title.setdefault(norm(prod["title"]), []).append(prod["id"])

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))[1:]  # drop header

    items: list[dict] = []
    report: list[str] = []
    seen_ids: set[str] = set()

    for row in rows:
        row = row + [""] * (12 - len(row))
        raw_id = row[ID].strip()
        if not raw_id:
            continue  # unnumbered wish-list rows are not catalog items yet

        caption = row[CAPTION].strip()
        category = row[CATEGORY].strip()
        stem = asset_stem(raw_id)

        # Folder12 is one row standing for two drawings; emit both.
        stems = ["folder12a", "folder12b"] if stem == "folder12" else [stem]

        for index, one in enumerate(stems):
            item_id = one
            if item_id in seen_ids:
                # Fig8 is used twice in the sheet. Keep the first and flag it
                # rather than silently overwriting the earlier row.
                report.append(
                    f"{raw_id}: duplicate ID, second row skipped -- {caption[:60]!r}"
                )
                continue
            seen_ids.add(item_id)

            needs: list[str] = []
            tags: list[str] = []
            linked_people: list[str] = []
            linked_productions: list[str] = []

            # --- category -> tags, people, productions -------------------
            # The sheet uses ";" to separate categories, except in Fig27
            # ("Person: Stella Holt; Langston Hughes") where it separates two
            # names. So a bare segment following a "Person:" segment is read as
            # another name rather than as a category of its own.
            last_was_person = False

            def add_person(name: str) -> None:
                name = name.strip()
                if not name:
                    return
                found = people_by_name.get(norm(name))
                if found:
                    linked_people.append(found)
                else:
                    needs.append(f"profile for {name}")

            for part in category.split(";"):
                part = part.strip()
                if not part:
                    continue
                match = re.match(r"^(person|individual)\s*:\s*(.+)$", part, re.I)
                if match:
                    tags.append("person")
                    for name in match.group(2).split(","):
                        add_person(name)
                    last_was_person = True
                    continue

                if last_was_person and ":" not in part:
                    for name in part.split(","):
                        add_person(name)
                    continue
                last_was_person = False

                match = re.match(r"^production[^:]*:\s*(.+)$", part, re.I)
                if match:
                    tags.append("production")
                    title = match.group(1).strip()
                    key = title.lower().strip()
                    if key in NEEDS_AUTHOR:
                        needs.append(f"production link ({NEEDS_AUTHOR[key]})")
                        continue
                    lookup = norm(TITLE_ALIASES.get(key, title))
                    found = productions_by_title.get(lookup)
                    if found and len(found) == 1:
                        linked_productions.append(found[0])
                    elif found:
                        needs.append(f"production link (“{title}” matches {len(found)} productions)")
                    else:
                        needs.append(f"production link (“{title}” not in the appendix)")
                    continue

                if re.match(r"^space$", part, re.I):
                    tags.append("space")
                elif re.match(r"^origins", part, re.I):
                    tags.append("origins")
                elif part:
                    tags.append(slugify(part))

            # --- media type from the caption -----------------------------
            haystack = f"{caption} {row[NOTES]}".lower()
            for tag, pattern in MEDIA_TAGS:
                if re.search(pattern, haystack) and tag not in tags:
                    tags.append(tag)

            if not tags:
                tags = ["uncategorised"]
                needs.append("category")

            # --- plain fields --------------------------------------------
            image = f"{one}.jpg" if (ASSETS / f"{one}.jpg").exists() else None
            if image is None:
                needs.append("image file")

            date = row[DATE].strip()
            if not date:
                needs.append("date")

            credit = row[CREDIT].strip()
            source = credit or row[OWNER].strip() or row[SOURCE].strip()
            if not credit:
                needs.append("credit line")

            rights = row[RIGHTS].strip() or row[COPYRIGHT].strip()
            if not rights:
                needs.append("rights status")

            if not caption:
                needs.append("caption")

            title = short_title(caption, raw_id)
            if stem == "folder12":
                title = f"{title} ({'blueprint' if index == 0 else 'architect’s drawing'})"

            items.append({
                "id": item_id,
                "figId": raw_id,
                "title": title,
                "image": image,
                "caption": caption or f"[No caption recorded for {raw_id}]",
                "creator": row[CREATOR].strip(),
                "date": date,
                "source": source,
                "rights": rights,
                "tags": sorted(set(tags)),
                "people": sorted(set(linked_people)),
                "productions": sorted(set(linked_productions)),
                "needs": needs,
            })

    items.sort(key=lambda i: (
        0 if re.match(r"^fig\d", i["id"]) else 1,
        int(re.sub(r"\D", "", i["id"]) or 0),
        i["id"],
    ))

    ITEMS_PATH.write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n")

    # Attach a real photograph to each production that one of the author's
    # figures depicts, replacing the AI placeholder the productions importer
    # used to emit. Only productions the items actually link to get an image;
    # everything else stays null and the timeline renders an empty frame.
    by_production: dict[str, str] = {}
    for item in items:
        if not item["image"]:
            continue
        for pid in item["productions"]:
            by_production.setdefault(pid, item["image"])

    changed = 0
    for prod in productions:
        wanted = by_production.get(prod["id"])
        if prod.get("image") != wanted:
            prod["image"] = wanted
            changed += 1
    PRODUCTIONS_PATH.write_text(json.dumps(productions, indent=2, ensure_ascii=False) + "\n")

    complete = sum(1 for i in items if not i["needs"])
    with_image = sum(1 for i in items if i["image"])
    print(f"wrote {len(items)} items to {ITEMS_PATH.relative_to(ROOT)}")
    print(f"  {with_image} have an image, {len(items) - with_image} do not")
    print(f"  {complete} complete, {len(items) - complete} need something")
    print(f"  {len(by_production)} productions now illustrated by a real figure"
          f" ({changed} entries updated)")

    if "--report" in sys.argv:
        print("\n--- what each item still needs ---")
        for item in items:
            if item["needs"]:
                print(f"  {item['figId']:9} {', '.join(item['needs'])}")
        from collections import Counter
        tally = Counter(
            re.sub(r" \(.*", "", n).split(" for ")[0]
            for i in items for n in i["needs"]
        )
        print("\n--- totals ---")
        for need, count in tally.most_common():
            print(f"  {count:3}  {need}")
        for line in report:
            print(f"  NOTE {line}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
