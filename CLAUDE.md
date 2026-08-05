# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Greenwich Mews Theater is a static Astro website serving as a book companion for "Brotherhood or the New Hell: The Greenwich Mews Theater, 1951–1973". It presents the story of an interfaith, interracial Civil Rights–era theater through curated archival materials.

## Commands

```bash
npm run dev      # Start dev server at localhost:4321
npm run build    # Build static site to ./dist/
npm run preview  # Preview production build locally
```

Restart the dev server after editing `src/content.config.ts` — content-collection changes are not hot-reloaded.

## Architecture

### Tech Stack
- **Framework**: Astro 5.x (static site generation)
- **Styling**: Vanilla CSS with CSS custom properties (no Tailwind/preprocessors)
- **Interactivity**: Vanilla JavaScript (Intersection Observer for animations, client-side filtering)
- **Data**: JSON files in `src/data/`, validated as Astro content collections

### Pages
- `index.astro` - Narrative storytelling with scroll-triggered sections
- `people.astro` - Profile cards with modal detail views
- `productions.astro` - Searchable table + visual timeline
- `archive.astro` - Filterable gallery of all archival items (tag chips + search)
- `book.astro` - Book promotional page
- `about.astro` - Author bio and project credits
- `404.astro` - Not-found page in the archive aesthetic

### Data Model
Three collections defined in `src/content.config.ts` (zod schemas over the JSON files):

- `src/data/items.json` - **The flat catalog of all archival items** (documents, photos, playbills, FBI files). Each item has an `id`, required `title`/`image`/`caption`/`date`/`source`/`rights`, a `tags` array (an item may carry any combination, e.g. both `performance` and `headshot`), and `people`/`productions` arrays of ids that cross-reference the other collections.
- `src/data/people.json` - Person profiles (no nested documents; items reference people, not the reverse).
- `src/data/productions.json` - Productions with `id` slugs (`<title-slug>-<year>`) and a `featured` flag for timeline display.

Validation is enforced at build time: missing fields, malformed slugs, unknown person/production ids in an item, or an `image` filename with no matching asset all fail `npm run build` with a clear error. Test this after schema changes by deliberately breaking a reference.

`src/lib/catalog.ts` builds the client-side payloads (`getItemPayloads`, `getPersonPayloads`) with pre-optimized image URLs; pages pass these to the modals via `define:vars`.

### Key Patterns

**Scroll Animations**: Elements with classes `fade-in`, `fade-in-left`, `fade-in-right` are animated via Intersection Observer in `BaseLayout.astro`. Add `stagger` class to parent for sequential child animations. `prefers-reduced-motion` disables them.

**Modal System**: `src/scripts/modal-controller.ts` provides shared open/close, focus trap, focus restore, and stacking (Escape closes only the top modal). `PersonModal.astro` (`window.openPersonModal`) shows a person and their items; `ItemModal.astro` (`window.openItemModal`) shows one item's full caption/source/rights/tags and can stack above the person modal. Modal content is populated with DOM APIs (`textContent`), never `innerHTML` interpolation.

**Archive Filtering**: `archive.astro` renders all item cards server-side with `data-tags`/`data-search` attributes; inline script does multi-select tag filtering (OR logic) and text search. `ProductionTable.astro` uses the same pattern for the productions table.

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
