# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Greenwich Mews Theater is a static Astro website serving as a book companion for "Brotherhood or the New Hell: The Greenwich Mews Theater, 1951–1973". It presents the story of an interfaith, interracial Civil Rights–era theater through curated archival materials.

**This checkout is the only one to work in.** An older copy exists at `~/Downloads/github/hillary/greenwich-mews`; it is abandoned and has no GitHub remote of its own. Never edit, build, or port work into it — if a request seems to point there, redirect to this repository.

## Commands

```bash
npm run dev      # Start dev server at localhost:4321
npm run build    # Build static site to ./dist/
npm run preview  # Preview production build locally
```

Restart the dev server after editing `src/content.config.ts` — content-collection changes are not hot-reloaded.

## Deployment

The site publishes to GitHub Pages via `.github/workflows/deploy.yml`, served from a
subpath (`https://smorello87.github.io/greenwich-mews`). `astro.config.mjs` sets
`base` accordingly, so **every site-root-relative path must go through
`withBase()` from `src/lib/url.ts`** — a bare `href="/people"` works in `npm run
dev` and 404s in production. `isCurrent()` handles nav active-state comparisons.
`preview` serves at the same subpath: `localhost:4321/greenwich-mews/...`.

## Architecture

### Tech Stack
- **Framework**: Astro 5.x (static site generation)
- **Styling**: Vanilla CSS with CSS custom properties (no Tailwind/preprocessors)
- **Interactivity**: Vanilla JavaScript (Intersection Observer for animations, client-side filtering)
- **Data**: JSON files in `src/data/`, validated as Astro content collections

### Pages
- `index.astro` - Narrative storytelling with scroll-triggered sections
- `people.astro` - Profile cards with modal detail views
- `productions.astro` - Searchable/sortable table (Season, Title, Playwright, Director, Full Info) + visual timeline
- `archive.astro` - Filterable gallery of all archival items (tag chips + search)
- `book.astro` - Book promotional page
- `about.astro` - Author bio and project credits
- `404.astro` - Not-found page in the archive aesthetic

### Data Model
Three collections defined in `src/content.config.ts` (zod schemas over the JSON files):

- `src/data/items.json` - **The flat catalog of all archival items** (documents, photos, playbills, plans). **Generated — do not hand-edit**; see `scripts/import-items/`. Each item has an `id`, the author's own `figId`, a `title`/`caption`, a `tags` array (an item may carry any combination, e.g. both `production` and `space`), and `people`/`productions` arrays of ids that cross-reference the other collections.

  `image`, and the `date`/`source`/`rights` strings, are **allowed to be empty or null**, because the catalog is still being assembled. Whatever is missing is listed in the item's `needs` array, which the Archive surfaces as an `Incomplete` flag and the item modal spells out. This is load-bearing: the site previously filled these gaps with AI-generated images and invented sources, which made an unfinished catalog look finished. Render a gap as a gap — use the shared `.empty-frame` class — and never substitute a placeholder picture.
- `src/data/people.json` - Person profiles (no nested documents; items reference people, not the reverse). `thumbnail`/`portrait` are nullable for the same reason; the AI-generated portraits were deleted and profiles without a cleared photograph render an empty frame.
- `src/data/productions.json` - Productions with `id` slugs (`<title-slug>-<year>`), transcribed from the book's appendix. `playwright`/`director`/`cast` are lifted out for the table columns; every remaining credit line from the source (producers, designers, stage management, music, translation…) lives in `credits`, an ordered array of `{ role, names }` so an entry can carry any set of roles without a schema change. `company` distinguishes the three producing organizations (see `COMPANIES` in `content.config.ts`), and `featured` drives the timeline.

Role labels in `credits` are canonical: one label per job (no `Set`/`Sets`/`Set Design` drift), compound source labels already split into separate fields, and a fixed display order. Names are canonical too — one spelling per person, so a name is findable and the contributor index below can group by it. Both are enforced by the import script, not by hand; see `scripts/import-productions/`.

Validation is enforced at build time: missing fields, malformed slugs, unknown person/production ids in an item, or an `image` filename with no matching asset all fail `npm run build` with a clear error. Test this after schema changes by deliberately breaking a reference.

`src/lib/catalog.ts` builds the client-side payloads (`getItemPayloads`, `getPersonPayloads`, `getProductionPayloads`) with pre-optimized image URLs; pages pass these to the modals via `define:vars`.

**Contributor index**: `getContributorPayloads()` walks every credit and cast list and indexes each name to the productions and roles it appears under, cross-referencing `people.json` for the handful with full profiles. `getLinkableContributors()` narrows that to names appearing in more than one production, keyed by the name exactly as printed — that is what the production modal matches against, so a click always leads somewhere. Multi-name credit values are split by `splitNames()`, which handles both commas and `in association with` clauses.

### Key Patterns

**Scroll Animations**: Elements with classes `fade-in`, `fade-in-left`, `fade-in-right` are animated via Intersection Observer in `BaseLayout.astro`. Add `stagger` class to parent for sequential child animations. `prefers-reduced-motion` disables them.

**Modal System**: `src/scripts/modal-controller.ts` provides shared open/close, focus trap, focus restore, and stacking (Escape closes only the top modal); `open()` is idempotent, so reopening an already-open modal never double-registers its key handler. Four modals use it:
- `PersonModal.astro` (`window.openPersonModal`) — a profiled person and their items.
- `ItemModal.astro` (`window.openItemModal`) — one item's caption/source/rights/tags; stacks above the person modal.
- `ProductionModal.astro` (`window.openProductionModal`) — the "Full Info" overlay behind every row of the productions table.
- `ContributorModal.astro` (`window.openContributorModal`) — one name's other productions; stacks above the production modal.

Selecting a production inside the contributor modal *repopulates the production modal in place* rather than stacking a second copy — `openProductionModal` detects that its backdrop is already open and skips `controller.open()`. Keep that guard if you touch it, or the two will fight over the stack.

Modal content is populated with DOM APIs (`textContent`), never `innerHTML` interpolation.

**Scoped CSS vs JS-built nodes**: Astro scopes component styles with a `data-astro-cid-*` attribute stamped onto elements *in the template*. Nodes a modal script creates at runtime never get that attribute, so any rule targeting them must be declared `:global(...)` — see `.tag-chip` in `ItemModal.astro`, `.production-modal__credit` and `.name-link` in `ProductionModal.astro`, `.contributor-appearance` in `ContributorModal.astro`. Symptom when missed: the markup is correct but renders completely unstyled.

**Archive Filtering**: `archive.astro` renders all item cards server-side with `data-tags`/`data-search` attributes; inline script does multi-select tag filtering (OR logic) and text search. `ProductionTable.astro` uses the same pattern for the productions table: only four fields are rendered as columns, but `data-searchable` is built from the whole record — cast, every credit line, company, and notes — so a designer or stage manager is findable from the search box.

**Hidden vs display**: Scoped component CSS that sets `display` on an element must include an `[hidden] { display: none; }` override, or JS filtering via the `hidden` attribute silently stops working.

### Design System
- **Fonts**: Playfair Display (display), Courier Prime (mono), Source Serif 4 (body)
- **Colors**: Warm sepia palette defined as CSS variables in `src/styles/global.css`
- **Aesthetic**: "Documentary Archive" - aged paper textures, typewriter typography, film-strip decorative elements

### Image Assets
Images live in `src/assets/` and go through Astro's `<Image>`/`getImage()` optimization (WebP, responsive sizes). Data files reference them by **bare filename**, resolved by `src/lib/images.ts` against:
- `src/assets/items/` - archival item images (referenced from `items.json` and production `image` fields)
- `src/assets/people/` - portraits (referenced from `people.json`)
- `src/assets/narrative/` - home page story images (referenced from `narrative.json`)

A referenced filename with no matching file fails the build. Don't leave unreferenced images in these directories — the glob imports them and ships the originals into `dist/`. `public/images/` holds only the social-share `og-image.jpg` and the author portrait.

Current images are AI-generated placeholders (Gemini 3 Pro Image via Vertex AI). Replace with real archival scans when available: drop the file in the right `src/assets/` directory and reference its filename from the data file.

#### Archival image intake

The author's originals live in `ignore/Materials for Greenwich Mews Site/` (git-ignored; Dropbox is the source of truth). She adds to that folder **incrementally**, so treat intake as a recurring job, not a one-time import — re-check for new files rather than assuming the last sweep was complete.

**Every non-JPEG original must be converted before it enters `src/assets/`.** Master scans are TIFF, HEIC, PNG, and PDF; as of the first sweep, 47 of 74 files needed conversion and the folder totals ~2.8 GB, with single TIFFs up to 280 MB. Two separate reasons to convert, and both matter:

- **Some formats simply don't build.** Astro's image pipeline is `sharp`, and `sharp` **cannot decode HEIC or PDF** — referencing one fails the build. TIFF and PNG *do* decode, so a TIFF will build; it just shouldn't, because of the second reason.
- **Repo weight.** These files are committed to a GitHub Pages repo. A 280 MB TIFF is unacceptable in git history even though Astro would happily optimize it.

Convert to JPEG (photographs) or PNG (line art, plans, documents with text), longest edge ~2400px for a full-bleed or zoomable image and ~1600px otherwise, then drop it in the right `src/assets/` directory. `sharp` handles TIFF and PNG; **HEIC and PDF need macOS `sips` or `pdftoppm`**, since `sharp` cannot read them:

```bash
sips -s format jpeg -Z 2400 input.HEIC --out output.jpg   # HEIC (sharp cannot)
pdftoppm -jpeg -r 300 -singlefile input.pdf output         # PDF  (sharp cannot)
sips -s format jpeg -Z 2400 input.tif --out output.jpg     # TIFF (sharp can, but see repo weight)
```

**Thumbnails do not need to be generated by hand.** Astro's `<Image>`/`getImage()` already emits responsive WebP derivatives at build time, and `src/lib/catalog.ts` pre-optimizes the modal payloads. Add a manual derivative only for a genuinely different *crop* — a square thumbnail from a tall document, say — not merely a smaller copy of the same framing. If a hand-cropped derivative is needed, commit it as its own file alongside the full-size one and reference each explicitly; do not overwrite the full-size asset.

Keep the author's `Fig` numbers in filenames (`fig01-village-church-1951.jpg`) so an asset stays traceable to her permissions spreadsheet, `ignore/Permission Brotherhood Hell - WEB IMAGES.csv`. Note that her spreadsheet writes `Fig1` while files on disk are `Fig01.tif` (and one is `Fig8.tif`, not `Fig08`), so match on the *number*, not the string.

**Rights gate:** that spreadsheet has a `Right obtained?` column, and many rows are blank, marked `in progress`, or carry a fee (`web only - $75`, `$375`). Publishing this site publishes the image. **Do not add an image to `src/assets/` until its row shows rights are cleared for web use**, and carry the `Credit Line` value into the item's `source`/`rights` fields verbatim.

### Import Scripts
`scripts/sync-materials/` pulls the author's latest work into `ignore/` — her permissions spreadsheet from Google Sheets and any new file from the shared Dropbox folder. **This is the entry point when asked to "pull her updates"**: `python3 scripts/sync-materials/sync.py --then-build` syncs, converts new masters, and regenerates the catalog in one pass. It never deletes local files. Its README covers the access requirements and the one real cost (Dropbox serves the folder only as a single ~2.7 GB zip, so the download is not incremental even though the extract is).

`scripts/import-items/` regenerates `src/data/items.json` (and attaches production images) from the author's permissions spreadsheet and her folder of archival masters, both in the git-ignored `ignore/`. Run `convert_images.py` then `build.py --report`; the report prints exactly what each row is still missing. She adds material incrementally, so re-run both rather than hand-editing the JSON. Its README records the editorial rules and the open questions left for her.

`scripts/import-productions/` regenerates `src/data/productions.json` from the book's appendix (`List of Productions.docx` → pandoc → `parse.py` → `build.py`). Its README records the editorial decisions and the open questions left for the author — read it before hand-editing productions data, and prefer adding a rule there over a one-off patch to the JSON.
