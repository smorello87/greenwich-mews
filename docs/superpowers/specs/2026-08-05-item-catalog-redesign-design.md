# Item Catalog Redesign — Design Spec

**Date:** 2026-08-05
**Status:** Implemented (2026-08-05)

## Problem

Archival items (documents, photos, playbills, FBI files) are nested inside
individual entries in `src/data/people.json`. This means:

- An item can belong to only one person; items relevant to two people must be
  duplicated and will drift apart.
- Items have no category or tag field — "FBI file" vs. "playbill" vs.
  "photograph" is implied only by title text. Nothing can be filtered or
  grouped, and an item cannot be both "performance" and "headshot".
- `productions.json` entries have no `id`, and cast lists are plain strings,
  so people, productions, and items cannot reference each other.
- The richest metadata (`caption`, `source`, `rights`) exists in the JSON but
  is never rendered anywhere on the site.

Expected scale: **100–150 items total**, hand-curated by the author (a
non-developer editing JSON directly).

## Design

### 1. Data model — flat item catalog with references

New file `src/data/items.json`: a flat array, one entry per archival item.

```json
{
  "id": "holt-rehearsal-1960",
  "title": "Backstage at the Mews",
  "image": "holt-rehearsal-1960.png",
  "caption": "Stella Holt directing rehearsals, circa 1960.",
  "date": "c. 1960",
  "source": "Private Collection",
  "rights": "Used with permission",
  "tags": ["performance", "photograph"],
  "people": ["stella-holt"],
  "productions": ["simply-heavenly-1957"]
}
```

Field rules:

- `id` — unique kebab-case slug. Required.
- `title`, `image`, `caption`, `date`, `source`, `rights` — required strings.
  (`date` is a display string: `"1957"`, `"c. 1960"`.)
- `image` — bare filename resolved against `src/assets/items/` at build time
  via `import.meta.glob`, so item images go through Astro's `<Image>`
  optimization pipeline; a filename with no matching asset is a build error.
- `tags` — array of one or more kebab-case strings. Open vocabulary; initial
  set: `performance`, `headshot`, `photograph`, `fbi-file`, `playbill`,
  `letter`, `script`, `poster`, `program`. An item may carry any combination.
- `people` — array of person ids (may be empty).
- `productions` — array of production ids (may be empty).

Changes to existing data:

- `people.json`: remove the nested `documents` arrays; everything else stays.
  Existing documents migrate into `items.json` (current placeholder set is
  ~10 items).
- `productions.json`: each production gains a required `id` slug in the form
  `<title-slug>-<year>` (e.g. `simply-heavenly-1957`). The `image` and
  `description` fields stay for now (timeline display); item references are
  additive.

### 2. Validation — Astro content collections

Define all three datasets as content collections in `src/content.config.ts`
using the `file()` loader with zod schemas:

- Schema-check every field (required fields present, `tags` non-empty, etc.).
- Cross-reference check: every id in an item's `people`/`productions` arrays
  must exist in the corresponding collection; duplicate ids are build errors.

A typo'd reference or missing field fails `npm run build` with a clear
message instead of silently rendering a broken page.

### 3. UI

**New `/archive` page**

- Gallery grid of all items (thumbnail, title, date, tag labels).
- Tag filter chips, multi-select (selecting `performance` + `headshot` shows
  items matching *any* selected tag), plus a text search box matching title,
  caption, and tag text. Client-side vanilla JS, same pattern as the existing
  production table filter. Shows "N of M items" count.
- Clicking an item opens the item detail modal.
- Added to the site navigation.

**Item detail modal (new shared component, `ItemModal.astro`)**

- Displays full image, title, date, caption, source, rights, tag labels, and
  links to related people (opens person modal / links to people page) and
  productions (links to productions page).
- Opens from the archive gallery and from item cards inside the person modal
  (fixing the current dead `cursor: pointer` affordance).
- Built with DOM APIs / `textContent`, not `innerHTML` interpolation.

**Person modal (updated)**

- Items are looked up by reference (`items.filter(i => i.people.includes(id))`)
  at build time and passed to the page; visual layout unchanged.
- Item cards become keyboard-accessible (`<button>`), show tag labels, and
  open the item detail modal.

**Production timeline (updated, minimal)**

- Featured timeline entries may show related items pulled by reference.

### 4. Folded-in fixes

- Modal accessibility: trap focus while open, restore focus to the invoking
  element on close (applies to both person and item modals).
- Provide a real `public/images/og-image.jpg` (currently referenced by
  `BaseLayout.astro` but missing — shared links get a broken preview).
- Add a 404 page (`src/pages/404.astro`) in the site's visual style.
- Image optimization pattern: move item/portrait images to `src/assets/` and
  render via Astro's `<Image>` component (auto WebP + responsive sizes).
  Applied to the new components now so the pattern is in place before real
  archival scans replace the ~30 MB of placeholder PNGs.

## Out of scope (YAGNI at 150 items)

- Per-item permalink pages
- CMS or admin UI
- Tag taxonomy management / controlled-vocabulary enforcement beyond the
  documented initial set
- Pagination or server-side search
- Linking cast-member strings in `productions.json` to person ids

## Error handling

- Build-time: schema and cross-reference violations fail the build (see §2).
- Runtime: archive filtering degrades gracefully — with JS disabled the full
  gallery renders unfiltered; modals are progressive enhancement over visible
  content.

## Testing

- `npm run build` passes with migrated data; deliberately broken fixture
  (bad reference) fails with a clear error during development verification.
- Manual verification in the browser: archive filtering (single tag, multiple
  tags, search), item modal from both entry points, person modal parity with
  current behavior, keyboard-only operation of cards and modals.
