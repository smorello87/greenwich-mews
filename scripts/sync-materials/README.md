# sync-materials

Pulls the author's latest material into `ignore/` — her permissions spreadsheet
and any Dropbox file not already on disk. `ignore/` is git-ignored; her Google
Sheet and Dropbox folder are the source of truth, and this keeps the local copy
level with them.

```bash
python3 scripts/sync-materials/sync.py                # sync both
python3 scripts/sync-materials/sync.py --then-build   # ...then re-import the catalog
python3 scripts/sync-materials/sync.py --dry-run      # report what would change
python3 scripts/sync-materials/sync.py --sheet-only   # skip the 2.7 GB download
```

The usual full run is:

```bash
python3 scripts/sync-materials/sync.py --then-build
npm run build
```

which pulls everything, converts any new masters, regenerates `items.json`,
prints what each row is still missing, and validates the result.

## What it does

**Spreadsheet** — exports the `WEB IMAGES` tab (`gid=843309143`) as CSV to
`ignore/Permission Brotherhood Hell - WEB IMAGES.csv`, and reports the change in
row count. The workbook has a second tab with different columns; the gid pins
the right one.

**Dropbox** — downloads the shared folder and extracts only entries that are
missing locally or whose size differs. Entry paths are already rooted at
`Space/`, `Productions/` and so on, so they map straight onto
`ignore/Materials for Greenwich Mews Site/` with no wrapper to strip. macOS
`._*` resource forks, `__MACOSX/` and `.DS_Store` are skipped.

**Nothing local is ever deleted.** Files that exist only on disk are listed and
left alone, so a file the author removes upstream cannot silently disappear from
a catalog you have already built. If you want one gone, delete it by hand.

## Access

Both links must be readable without credentials:

- The **Google Sheet** needs "anyone with the link can view". Without it the
  export returns an HTML sign-in page and the script stops with that message
  rather than writing a broken CSV.
- The **Dropbox** link carries its own `rlkey`, and the script appends `dl=1` to
  get a zip.

Neither needs a token or an API key. If the sheet's sharing is tightened, or
either link is regenerated, update `SHEET_URL` / `DROPBOX_URL` at the top of
`sync.py`.

## The one real cost

Dropbox only serves a shared folder as a single zip of the whole thing, so a
sync downloads everything (~2.7 GB today, growing as the author adds material)
even when one file changed. Extraction is incremental; the download is not.

Use `--sheet-only` when you just want her latest spreadsheet, and `--zip FILE`
to re-run the extract against a zip you already have without fetching again.
