#!/usr/bin/env python3
"""Pull the author's latest spreadsheet and Dropbox files into ignore/.

Fetches two things, both of which live outside git:

1. The permissions spreadsheet, exported as CSV from the "WEB IMAGES" tab.
2. Any file in the shared Dropbox folder that is not already on disk.

Nothing local is ever deleted. Files that exist only locally are reported and
left alone, so a file the author removes upstream does not silently vanish from
a build you have already run.

Usage:
    python3 scripts/sync-materials/sync.py              # sync both
    python3 scripts/sync-materials/sync.py --then-build # ...then re-import
    python3 scripts/sync-materials/sync.py --dry-run    # report, change nothing
    python3 scripts/sync-materials/sync.py --sheet-only
    python3 scripts/sync-materials/sync.py --zip FILE   # reuse a downloaded zip

Note on cost: Dropbox only serves a shared folder as one zip of everything, so
a sync downloads the whole folder (~2.7 GB and growing) even when one file has
changed. The extract step is incremental; the download is not. Use
--sheet-only when you only need the spreadsheet.
"""

from __future__ import annotations

import argparse
import csv
import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IGNORE = ROOT / "ignore"
MATERIALS = IGNORE / "Materials for Greenwich Mews Site"
CSV_PATH = IGNORE / "Permission Brotherhood Hell - WEB IMAGES.csv"

# The "WEB IMAGES" tab of the author's permissions spreadsheet. The document
# must be shared as "anyone with the link can view" for this to work without
# credentials; it returns an HTML login page (HTTP 401) otherwise.
SHEET_ID = "1TXp93ZtKu8D5fN5yvx-g6sup1IJxIl4OvhsdQ1Y0HmU"
SHEET_GID = "843309143"
SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={SHEET_GID}"
)

# Shared folder link with dl=1, which serves the whole folder as a zip whose
# entries are already rooted at "Space/", "Productions/" and so on — i.e. they
# map straight onto MATERIALS with no wrapper directory to strip.
DROPBOX_URL = (
    "https://www.dropbox.com/scl/fo/ogqvxg55wxwe998beps0o/"
    "AJTodzbNx93r51iNSg2Xh-w?rlkey=4fowc6ee2lb2jlxci2xbxxfga&dl=1"
)

# macOS resource forks and Dropbox/zip bookkeeping; never wanted on disk.
def is_noise(name: str) -> bool:
    parts = Path(name).parts
    return (
        name.endswith("/")
        or any(p.startswith("._") for p in parts)
        or "__MACOSX" in parts
        or Path(name).name in {".DS_Store", ""}
    )


def curl(url: str, dest: Path, label: str) -> None:
    """Download with curl, following redirects and failing loudly on HTTP errors."""
    print(f"  fetching {label}…")
    result = subprocess.run(
        ["curl", "-L", "--fail", "--retry", "3", "--retry-delay", "2",
         "-#", "-o", str(dest), url],
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"  FAILED to download {label} (curl exit {result.returncode}).\n"
            "  If this is the spreadsheet, check it is shared as "
            "'anyone with the link can view'."
        )


def row_count(path: Path) -> int:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return sum(1 for row in csv.reader(handle) if any(c.strip() for c in row))


def sync_sheet(dry_run: bool) -> bool:
    print("\nSpreadsheet")
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "sheet.csv"
        curl(SHEET_URL, fresh, "spreadsheet CSV")

        head = fresh.read_bytes()[:400].lstrip()
        if head.startswith(b"<"):
            raise SystemExit(
                "  Got HTML instead of CSV — the sheet is not publicly readable."
            )

        new_rows = row_count(fresh)
        if CSV_PATH.exists():
            old_rows = row_count(CSV_PATH)
            if fresh.read_bytes() == CSV_PATH.read_bytes():
                print(f"  unchanged ({new_rows} non-empty rows)")
                return False
            delta = new_rows - old_rows
            print(f"  updated: {old_rows} -> {new_rows} non-empty rows "
                  f"({delta:+d})")
        else:
            print(f"  new file, {new_rows} non-empty rows")

        if dry_run:
            print("  [dry run] not written")
            return False
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fresh, CSV_PATH)
        return True


def sync_dropbox(dry_run: bool, zip_path: Path | None) -> bool:
    print("\nDropbox")
    tmpdir = None
    try:
        if zip_path is None:
            tmpdir = tempfile.mkdtemp()
            zip_path = Path(tmpdir) / "materials.zip"
            curl(DROPBOX_URL, zip_path, "Dropbox folder (whole folder, ~2.7 GB)")
        else:
            print(f"  using existing zip: {zip_path}")

        MATERIALS.mkdir(parents=True, exist_ok=True)

        added: list[str] = []
        replaced: list[str] = []
        with zipfile.ZipFile(zip_path) as archive:
            entries = [i for i in archive.infolist() if not is_noise(i.filename)]
            remote = {i.filename for i in entries}

            for info in entries:
                target = MATERIALS / info.filename
                if target.exists() and target.stat().st_size == info.file_size:
                    continue
                (replaced if target.exists() else added).append(info.filename)
                if dry_run:
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)

        local = {
            str(p.relative_to(MATERIALS))
            for p in MATERIALS.rglob("*")
            if p.is_file() and not is_noise(str(p.relative_to(MATERIALS)))
        }
        only_local = sorted(local - remote)

        print(f"  {len(remote)} files upstream, {len(local)} local")
        for name in added:
            print(f"  + {name}")
        for name in replaced:
            print(f"  ~ {name} (size changed)")
        if only_local:
            print(f"  {len(only_local)} local-only file(s), left untouched:")
            for name in only_local:
                print(f"    . {name}")
        if not added and not replaced:
            print("  nothing new")
        if dry_run and (added or replaced):
            print("  [dry run] nothing extracted")
            return False
        return bool(added or replaced)
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sheet-only", action="store_true")
    parser.add_argument("--dropbox-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--then-build", action="store_true",
                        help="run the image conversion and catalog import afterwards")
    parser.add_argument("--zip", type=Path, default=None,
                        help="use an already-downloaded folder zip instead of fetching")
    args = parser.parse_args()

    changed = False
    if not args.dropbox_only:
        changed |= sync_sheet(args.dry_run)
    if not args.sheet_only:
        changed |= sync_dropbox(args.dry_run, args.zip)

    if args.then_build and not args.dry_run:
        print("\nRe-importing")
        for step in (
            [sys.executable, str(ROOT / "scripts/import-items/convert_images.py")],
            [sys.executable, str(ROOT / "scripts/import-items/build.py"), "--report"],
        ):
            result = subprocess.run(step, cwd=ROOT)
            if result.returncode != 0:
                return result.returncode
    elif changed:
        print("\nNext: python3 scripts/import-items/convert_images.py"
              " && python3 scripts/import-items/build.py --report")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
