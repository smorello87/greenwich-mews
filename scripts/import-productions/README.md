# Productions import

One-off transcription pipeline that produced `src/data/productions.json` from
`List of Productions.docx` (the book's appendix). Kept for provenance and so the
catalog can be regenerated if the source document is revised.

```bash
pandoc -t markdown "List of Productions.docx" -o productions.md
python3 parse.py    # productions.md -> parsed.json, reports unrecognised credit labels
python3 build.py    # parsed.json    -> ../../src/data/productions.json
```

`parse.py` splits the document into entries and matches each credit line against
the role labels the document actually uses. It prints any line it could not
label — that list should stay empty apart from the known `Ladybug` entry, whose
"Native American Consultant" label wraps across two paragraphs.

`build.py` expands the abbreviations defined in the document's own KEY block,
lifts playwright/director/cast into their own fields, merges roles the source
lists twice, and applies the hand-verified corrections collected in
`TITLE_FIXES`, `NAME_FIXES`, `PLAYWRIGHT_FALLBACK`, and `CREDIT_FIXES`. Editorial
decisions worth knowing about are commented inline next to each of those tables.

It also canonicalises the vocabulary: compound labels are split so each job is
its own field ("Sets, Lights: Frank Wicks" becomes Sets *and* Lights), each job
gets one spelling, and credits render in the fixed `ROLE_ORDER` so every
production's overlay reads the same way.

The featured set and its timeline blurbs also live in `build.py` (`FEATURED`).
Editing `src/data/productions.json` by hand is fine for small corrections; rerun
these scripts only when re-importing the whole list.

## Settled by the author

Answers given after the first pass, now encoded in `build.py`:

- **Role labels** (`Sets` / `Set Design` / `Set Designer`) — standardising them
  is correct; the programs' wording drifted over the years.
- **Playwright fallbacks** — all four stand as filled. The Mikado is billed
  **W.S. Gilbert**, not William Schwenck Gilbert, with Sullivan on music and
  Gilbert on libretto.
- **Preferred spellings**: Anne Fielding, Frances Drucker, L.D. Clements, James
  Gore, Manolo de Orellana, Thomas S. Vasiloff, Antoinette Kray (no "Toni"),
  and **R. Graham Brown** for every billing of a man who changed his stage name
  repeatedly. David Lucas is provisional.
- **Jericho-Jim Crow** — the programs drop the "h"; the published spelling wins,
  for the 1964 production and the 1968 revival alike.
- **Harriet Bailin** is the correct spelling in `Carricknabauna` (1968).
- **George Corwin / George Corrin** — two people. Corrin, an African-American
  set designer, did `In Splendid Error`; Corwin did `Major Barbara`.
- **Austin Briggs-Hall** (1955) and **Austin Briggs-Hall Jr.** (1967) — father
  and son. Both hyphenated; the "Jr." keeps them apart.

## Open questions for the author

Deliberately *not* normalised, because picking a side would mean guessing:

- **Joe Liberman / Joe Lieberman** — possibly one person, possibly two. Both
  spellings are left as printed until that is settled.
- **James Clark / James N. Clark / Jim Clark** — all in the 1955 season, and
  probably one person, but no preferred spelling yet.
- **James McMahon / James B. McMahon** — merged to James B. McMahon on the
  assumption they are one person; not yet confirmed.
- **Accents in Spanish-language names.** Only names that appear both ways in the
  source were fixed (Zaldívar, Marqués); the rest are left as printed.
