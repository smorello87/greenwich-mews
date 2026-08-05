// @ts-check
import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  // Project Pages serve from https://<user>.github.io/<repo>/, so every
  // site-root-relative path has to carry `base` — see src/lib/url.ts.
  site: 'https://smorello87.github.io',
  base: '/greenwich-mews',
});
