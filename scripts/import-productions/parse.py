"""Parse the pandoc-markdown rendering of 'List of Productions.docx' into
structured production records. Emits parsed.json plus a report of any credit
line whose role label was not recognised, so the label list can be tightened."""

import json
import re
import sys
import unicodedata

SRC = "productions.md"

# Role labels as they literally appear in the document, including the compound
# forms ("Sets, Lighting"). Matched longest-first so "Music Arr. and Dir." wins
# over "Music".
LABELS = [
    "Playwright, Dir.",
    "Playwrights",
    "Playwright",
    "Adapted and Arr.",
    "Adapted by",
    "Book and Lyrics",
    "Librettist",
    "Lyricist",
    "Composers",
    "Composer",
    "Translation",
    "Trans.",
    "Producer, Director",
    "Directors",
    "Director",
    "DIrector",
    "Associate Dir.",
    "Managing Dir",
    "Artistic Dir.",
    "Artistic Director",
    "Artistic Coord, PM",
    "Artistic Coord",
    "Admin Coord",
    "Production Coord",
    "Production Asst.",
    "Presented by",
    "Producers",
    "Producer",
    "Asst. Producer",
    "Sponsors",
    "Co-producer",
    "Music Arr. and Dir.",
    "Music Supervision",
    "Musical Arr",
    "Musical Dir.",
    "Musical Dir",
    "Music Dir.",
    "Music Dir",
    "Music, Sound",
    "Music",
    "MDs",
    "Orchestrations",
    "Choreography",
    "Choreo",
    "Cast",
    "Understudies",
    "Set Designer",
    "Set Design",
    "Original design",
    "Sets, Costumes",
    "Sets, Lighting",
    "Sets, Lights",
    "Sets and Lights",
    "Sets",
    "Set",
    "Costume Design",
    "Costumes, Lights",
    "Costumes",
    "Costumer",
    "Gown Design",
    "Light Design",
    "Lighting",
    "Lights, Sound",
    "Lights",
    "Sound",
    "Props",
    "Design",
    "Press Agent",
    "Public Relations",
    "PR",
    "PSM",
    "ASM",
    "SM",
    "PM, HM",
    "PM",
    "TD",
    "TM",
    "BM",
    "GM",
    "HM",
    "AD, SM",
    "AD",
    "AC",
    "APs",
    "AP",
    "PAs",
    "PA",
    "TAs",
    "TA",
    "WR",
    "Coord",
    "PC",
]
LABELS.sort(key=len, reverse=True)
LABEL_RE = re.compile(r"^(%s)\s+(.*)$" % "|".join(re.escape(l) for l in LABELS))

SECTIONS = {
    "The Greenwich Mews Spanish Theatre": "greenwich-mews-spanish-theatre",
    "Arts Ministry of The Village Church": "village-church-arts-ministry",
}


def strip_markup(text: str) -> str:
    """Remove pandoc emphasis/underline markup and normalise whitespace."""
    text = re.sub(r"\[([^\]]*)\]\{\.ul\}", r"\1", text)
    text = text.replace("***", "").replace("**", "").replace("*", "")
    text = text.replace("\\'", "'").replace("\\", "")
    text = re.sub(r"~,~", "", text)
    return re.sub(r"\s+", " ", text).strip()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def join_wrap(head: str, tail: str) -> str:
    """Rejoin a credit that wrapped onto a following block. A plain space join is
    correct either way: the separating comma, when there is one, is already at the
    end of `head`, and when there isn't the wrap fell inside a single name
    ("... Bill Gunn, Hilda" + "Haynes, ..." -> "... Hilda Haynes, ...")."""
    return f"{head.strip()} {tail.strip()}"


def blocks(lines):
    """Group the markdown into blank-line-separated blocks, preserving whether
    a block was a blockquote continuation."""
    buf, out = [], []
    for line in lines:
        if line.strip():
            buf.append(line)
        elif buf:
            out.append(buf)
            buf = []
    if buf:
        out.append(buf)
    return out


def main():
    raw = open(SRC, encoding="utf-8").read().split("\n")
    company = "greenwich-mews-theatre"
    entries, unmatched = [], []
    current = None
    pending = None  # the credit dict the next continuation block appends to

    # A production heading: a bold block whose text starts with a 4-digit year.
    head_re = re.compile(r"^\s*\*\*\d{4}")

    for block in blocks(raw):
        text = " ".join(l.strip() for l in block)
        flat = strip_markup(text)

        # Section divider
        for label, slug in SECTIONS.items():
            if flat.startswith(label):
                company = slug
                current = None
                pending = None
                break
        else:
            if head_re.match(block[0]):
                m = re.match(r"^(\d{4})\s*,?\s*(.*)$", flat)
                if not m:
                    unmatched.append(("HEAD", flat))
                    continue
                year, title = int(m.group(1)), m.group(2).strip().rstrip(",").strip()
                current = {
                    "year": year,
                    "title": title,
                    "company": company,
                    "credits": [],
                }
                entries.append(current)
                pending = None
                continue

            if current is None:
                continue  # key/preamble

            is_continuation = block[0].lstrip().startswith(">")
            # Strip the blockquote marker from every line, not just the first —
            # long cast lists carry bare ">" spacer lines mid-block.
            body = strip_markup(
                " ".join(re.sub(r"^\s*>\s?", "", l.strip()) for l in block))

            if is_continuation and pending is not None:
                pending["names"] = join_wrap(pending["names"], body)
                continue

            m = LABEL_RE.match(body)
            if not m:
                unmatched.append((current["title"], body))
                continue

            credit = {"role": m.group(1), "names": m.group(2).strip()}
            current["credits"].append(credit)
            pending = credit

    # Tidy: collapse doubled separators, assign ids.
    for e in entries:
        for c in e["credits"]:
            c["names"] = re.sub(r"\s*,\s*", ", ", c["names"]).strip().strip(",")
            c["names"] = re.sub(r"\s+", " ", c["names"])
        e["id"] = f"{slugify(e['title'])}-{e['year']}"

    json.dump(entries, open("parsed.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    print(f"{len(entries)} entries")
    ids = [e["id"] for e in entries]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        print("DUPLICATE IDS:", dupes)
    print(f"\n{len(unmatched)} unmatched lines:")
    for title, line in unmatched:
        print(f"  [{title}] {line[:110]}")


if __name__ == "__main__":
    main()
