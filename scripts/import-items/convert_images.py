#!/usr/bin/env python3
"""Convert the author's archival masters into web assets for src/assets/items/.

Reads every Fig-numbered file (and the Folder 12 building plans) out of the
git-ignored materials folder and writes a JPEG named for the author's own
figure number, so an asset stays traceable to her permissions spreadsheet.

Deliberately does NOT crop. These are archival scans; trimming a border
automatically risks silently cutting the edge off a document or a playbill.
The two images that ARE cropped (fig01, fig02, used as page headers) were
each checked by eye and live in src/assets/narrative/.

sharp -- and therefore Astro's image pipeline -- cannot decode HEIC or PDF,
so those go through sips and pdftoppm respectively. See CLAUDE.md.

Usage:  python3 scripts/import-items/convert_images.py [--force]
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parents[2]
MATERIALS = ROOT / "ignore" / "Materials for Greenwich Mews Site"
OUT = ROOT / "src" / "assets" / "items"

MAX_EDGE = 2000
QUALITY = 82

FIG_RE = re.compile(r"^fig\s*0*(\d+)", re.IGNORECASE)

# The Folder 12 plans are two drawings, each scanned front and back. The backs
# are blank versos carrying only the 1946 approval stamp, so only the fronts
# become assets.
PLANS = {
    "REC0074_0609_065_0001_front.tif": "folder12a",
    "REC0074_0609_065_0002_front.tif": "folder12b",
}


def discover() -> dict[str, Path]:
    """Map each output stem (fig01, folder12a...) to its master file."""
    found: dict[str, Path] = {}
    for path in MATERIALS.rglob("*"):
        if not path.is_file() or path.name.startswith("._"):
            continue
        if path.name in PLANS:
            found[PLANS[path.name]] = path
            continue
        match = FIG_RE.match(path.stem)
        if match:
            found[f"fig{int(match.group(1)):02d}"] = path
    return found


def load(path: Path) -> Image.Image:
    """Open a master as RGB, shelling out for the formats PIL can't read."""
    suffix = path.suffix.lower()

    if suffix in {".heic", ".heif"}:
        tmp = OUT / f".{path.stem}.tmp.png"
        subprocess.run(
            ["sips", "-s", "format", "png", str(path), "--out", str(tmp)],
            check=True, capture_output=True,
        )
        try:
            return to_rgb(Image.open(tmp))
        finally:
            tmp.unlink(missing_ok=True)

    if suffix == ".pdf":
        # pdftoppm appends its own .jpg to the stem it is given, so build the
        # expected output path by string, not with_suffix() -- these stems
        # contain dots and with_suffix would eat the wrong one.
        stem = OUT / f"pdftmp-{path.stem}"
        subprocess.run(
            ["pdftoppm", "-jpeg", "-r", "200", "-f", "1", "-l", "1",
             "-singlefile", str(path), str(stem)],
            check=True, capture_output=True,
        )
        tmp = Path(f"{stem}.jpg")
        try:
            return to_rgb(Image.open(tmp))
        finally:
            tmp.unlink(missing_ok=True)

    return to_rgb(Image.open(path))


def to_rgb(im: Image.Image) -> Image.Image:
    """Flatten any master to 8-bit RGB without destroying it.

    Two cases PIL's plain .convert('RGB') gets wrong on this collection:

    * 16-bit greyscale scans (mode 'I;16', e.g. Fig22 and Fig8) saturate to
      solid white, because convert() clips rather than rescales. Both files
      use nearly the whole 16-bit range, so dividing by 257 maps them onto
      0-255 with their tonality intact.
    * RGBA masters would composite transparency onto black, which turns the
      margins of a scanned document into a black page. White is the correct
      ground for paper.
    """
    if im.mode in {"I;16", "I;16B", "I;16L", "I"}:
        import numpy as np

        arr = np.asarray(im).astype("float32")
        if arr.max() > 255:
            arr = arr / 257.0
        grey = Image.fromarray(arr.clip(0, 255).astype("uint8"), mode="L")
        return grey.convert("RGB")

    if im.mode in {"RGBA", "LA", "PA"}:
        rgba = im.convert("RGBA")
        canvas = Image.new("RGB", rgba.size, (255, 255, 255))
        canvas.paste(rgba, mask=rgba.split()[-1])
        return canvas

    return im.convert("RGB")


def main() -> int:
    force = "--force" in sys.argv

    if not MATERIALS.is_dir():
        print(f"materials folder not found: {MATERIALS}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    masters = discover()
    if not masters:
        print("no Fig-numbered masters found", file=sys.stderr)
        return 1

    written = skipped = failed = 0
    for stem in sorted(masters):
        src = masters[stem]
        dst = OUT / f"{stem}.jpg"

        if dst.exists() and not force and dst.stat().st_mtime >= src.stat().st_mtime:
            skipped += 1
            continue

        try:
            im = load(src)
        except Exception as exc:  # noqa: BLE001 - report and keep going
            print(f"  FAIL {stem:10} {src.name}: {exc}", file=sys.stderr)
            failed += 1
            continue

        before = im.size
        scale = MAX_EDGE / max(im.size)
        if scale < 1:
            im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)

        im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        written += 1
        print(f"  {stem:10} {src.suffix.lower():6} {before[0]}x{before[1]}"
              f" -> {im.width}x{im.height}  {dst.stat().st_size / 1e6:.2f} MB")

    total = sum(f.stat().st_size for f in OUT.glob("*.jpg"))
    print(f"\n{written} written, {skipped} up to date, {failed} failed"
          f" -- {len(list(OUT.glob('*.jpg')))} assets, {total / 1e6:.1f} MB total")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
