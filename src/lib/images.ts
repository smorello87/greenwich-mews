import type { ImageMetadata } from 'astro';

// Data files reference images by bare filename; each filename must have a
// matching asset in the corresponding src/assets/ directory or the build fails.
// Globs are lazy so assets that no data file references are never imported
// (eager globs would ship every original file into dist/).
type Glob = Record<string, () => Promise<{ default: ImageMetadata }>>;

const itemImages: Glob = import.meta.glob('../assets/items/*.{png,jpg,jpeg,webp}');
const peopleImages: Glob = import.meta.glob('../assets/people/*.{png,jpg,jpeg,webp}');
const narrativeImages: Glob = import.meta.glob('../assets/narrative/*.{png,jpg,jpeg,webp}');

async function resolve(glob: Glob, dir: string, filename: string): Promise<ImageMetadata> {
  const load = glob[`../assets/${dir}/${filename}`];
  if (!load) {
    throw new Error(
      `Missing image asset: src/assets/${dir}/${filename} (referenced from a data file)`
    );
  }
  return (await load()).default;
}

export const itemImage = (filename: string) => resolve(itemImages, 'items', filename);
export const personImage = (filename: string) => resolve(peopleImages, 'people', filename);
export const narrativeImage = (filename: string) => resolve(narrativeImages, 'narrative', filename);
