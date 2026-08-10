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
`TITLE_FIXES`, `NAME_FIXES`, `PLAYWRIGHT_FALLBACK`, and `DROP_CREDITS`. Editorial
decisions worth knowing about are commented inline next to each of those tables.

It also canonicalises the vocabulary: compound labels are split so each job is
its own field ("Sets, Lights: Frank Wicks" becomes Sets *and* Lights), each job
gets one spelling, and credits render in the fixed `ROLE_ORDER` so every
production's overlay reads the same way.

The featured set and its timeline blurbs also live in `build.py` (`FEATURED`).
Editing `src/data/productions.json` by hand is fine for small corrections; rerun
these scripts only when re-importing the whole list.

## Open questions for the author

Deliberately *not* normalised, because picking a side would mean guessing:

- **Harriet Ballin / Harriet Bailin** — `Carricknabauna` (1968) credits the music
  twice, spelled both ways. `DROP_CREDITS` keeps Ballin.
- **George Corwin / George Corrin** — both design 1954 productions.
- **James Clark / James N. Clark / Jim Clark** — all in the 1955 season.
- **Austin Briggs-Hall** (1955) vs **Austin Briggs Hall Jr.** (1967).
- **Accents in Spanish-language names.** Only names that appear both ways in the
  source were fixed (Zaldívar, Marqués); the rest are left as printed.
