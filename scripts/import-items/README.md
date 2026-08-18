# import-items

Turns the author's permissions spreadsheet and her folder of archival masters
into the site's catalog. Two scripts, run in this order:

```bash
python3 scripts/import-items/convert_images.py   # masters  -> src/assets/items/
python3 scripts/import-items/build.py --report   # CSV      -> src/data/items.json
npm run build                                    # validates the result
```

Both are safe to re-run. `convert_images.py` skips files whose output is already
newer than the master (`--force` re-does everything), and `build.py` regenerates
`items.json` from scratch every time. The author adds material to the Dropbox
folder incrementally, so **re-run both whenever new files land** rather than
hand-editing `items.json`.

## Inputs

Both live in `ignore/`, which is git-ignored — Dropbox is the source of truth.

- `ignore/Permission Brotherhood Hell - WEB IMAGES.csv`
- `ignore/Materials for Greenwich Mews Site/**`

## Editorial rules

**Only numbered rows become items.** The spreadsheet has ~53 further rows
describing images the author is still chasing. Those are a working wish-list,
not catalog entries, and are skipped.

**Nothing is invented.** Where the spreadsheet leaves a cell blank, the item
gets an empty string and the name of the missing field is appended to its
`needs` array. The Archive marks such a card `Incomplete`, and the item modal
lists exactly what is outstanding. That is deliberate: an earlier version of
this site filled the gaps with AI-generated images and plausible-sounding
sources, which made an unfinished catalog look complete.

**No cropping.** `convert_images.py` resizes but never trims. Auto-trimming a
border risks silently cutting the edge off a document. The two cropped images
(`fig01`, `fig02`, used as page headers) were checked by eye and live in
`src/assets/narrative/`.

**Filenames are the author's figure numbers**, zero-padded — `Fig8.tif` becomes
`fig08.jpg`. Every figure number maps to exactly one master, so the number is a
reliable key. See "known data issues" for the two exceptions.

## Format handling

`sharp`, and therefore Astro's image pipeline, **cannot decode HEIC or PDF**;
referencing one fails the build. `convert_images.py` routes those through `sips`
and `pdftoppm`. TIFF and PNG decode natively but are still converted, because
single masters run to 280 MB and this repo deploys to GitHub Pages.

Two subtleties that cost real debugging time, both handled in `to_rgb()`:

- **16-bit greyscale** (`Fig22`, `Fig8`) saturates to solid white under PIL's
  plain `.convert('RGB')`. Fig22 shipped as a blank rectangle before this was
  caught. Both files use nearly the whole 16-bit range, so they are divided by
  257 instead.
- **RGBA masters** composite onto black by default, turning a scanned document's
  margins into a black page. They are flattened onto white.

## Cross-references

`Image Category` parses cleanly — 46 of 47 rows sort into type / person /
production on the first attempt. The work is not parsing it but *resolving* it
against the site's own ids.

Production titles that do not match the book's appendix verbatim are mapped in
`TITLE_ALIASES`:

| Spreadsheet | Appendix |
|---|---|
| `Decision` | `The Decision` (1951) |
| `Life is a Dream` | `Life is a Dream (La Vida Es Sueño)` (1971) |
| `The Ox Cart` | `The Oxcart (La Carreta)` (1967) |

Anything genuinely ambiguous is listed in `NEEDS_AUTHOR` and left **unlinked**
rather than guessed — see below.

People resolve three ways, in descending order of richness: a full profile in
`people.json`; failing that, the **contributor index** built from the appendix's
cast and credit lines, which can show every production a person worked on
without anyone writing a biography; and only a name in neither place is
recorded as missing. All seven names without profiles resolve via the second
route.

Where an item links to a production, the first such item also becomes that
production's `image`, and `featured` follows: a production is featured on the
timeline exactly when a real photograph exists for it. That replaced a
hand-kept list which predated the archival images, and which both hid six
productions that now have one and featured four that rendered empty.
`scripts/import-productions/build.py` therefore leaves `image` null and
`featured` false; do not reintroduce a placeholder there.

## Known data issues, for the author

Regenerate this list any time with `build.py --report`.

- **`Fig8` is used twice** — once for the *Courageous One* stage shot and once
  for a pair of altar photographs. Only one `Fig8` master exists (the stage
  shot), so the altar photographs have neither a number nor a file. The second
  row is skipped and reported.
- **`Folder12` is one row for four scans** — two drawings, each shot front and
  back. The backs are blank versos carrying the 1946 approval stamp, so only
  the fronts are imported, as `folder12a` (cyanotype) and `folder12b` (pencil
  original). The row wants splitting.
- **`Jericho-Jim Crow` ran in both 1964 and 1968**, so `Fig36`/`Fig37` cannot be
  linked to a production without a year.
- **`Holy Moses` (`Fig46`) is not in the appendix at all** — either the
  production is missing from it or the figure is labelled with a working title.
- **Seven numbered rows have no master yet**: Fig3, Fig4, Fig27, Fig28, Fig36,
  Fig37, Fig42.
- **Seven names have no profile** in `people.json` — Fran Bennett, R. Graham
  Brown, Diana Sands, Alvin Ailey, Gilberto Zaldívar, Adrian Hall, William
  Glenesk. They are *not* unlinked: each appears in the productions appendix,
  so `build.py` links them through the contributor index instead, and the item
  modal opens their list of productions. A full profile would add biography and
  dates, but nothing is broken without one.

## What the catalog is still missing

As of the first full import — 47 items, 40 with a scan, 5 complete. Every
person named in the spreadsheet now resolves, either to a profile or to the
contributor index, so nothing is left dangling:

| Missing | Rows |
|---|---|
| rights status | 36 |
| date | 31 |
| credit line | 19 |
| image file | 7 |
| production link | 3 |
