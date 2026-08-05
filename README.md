# Greenwich Mews Theater

Companion website for *Brotherhood or the New Hell: The Greenwich Mews Theater, 1951–1973* by Hillary Miller.

The Greenwich Mews was an interfaith, interracial theater in New York City during the Civil Rights era. This site presents its story through a curated selection of archival materials — FBI file excerpts, playbills, letters, and production photographs — alongside a chronology of productions and profiles of the people who made them.

**Live site:** https://smorello87.github.io/greenwich-mews/

## Development

```sh
npm install
npm run dev      # dev server at localhost:4321
npm run build    # static build to ./dist/
npm run preview  # serve the production build locally
```

Built with [Astro](https://astro.build). Content lives in JSON files under `src/data/`, validated at build time as Astro content collections — see `CLAUDE.md` for the data model and site architecture.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the site and publishes it to GitHub Pages.

Because this is a GitHub project site, it is served from a subpath (`/greenwich-mews`) rather than a domain root. `astro.config.mjs` sets `base` accordingly, and every site-root-relative link goes through `withBase()` in `src/lib/url.ts`. If the site later moves to its own domain, change `site`/`base` in `astro.config.mjs` — the helper handles a root base without further edits.

## Images

The images currently in `src/assets/` are AI-generated placeholders standing in for archival material that has not yet been cleared for publication. They are not historical documents and should not be cited as such. Replace them as real scans become available.

## Credits

Site design and development by [Makeko Inc.](https://makeko.com), in collaboration with the American Social History Project / New Media Lab.
