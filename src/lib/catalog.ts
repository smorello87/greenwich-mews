import { getCollection } from 'astro:content';
import { getImage } from 'astro:assets';
import { itemImage, personImage } from './images';

// Client-side payload shapes shared by the archive page and the modals.
export interface ItemPayload {
  id: string;
  title: string;
  caption: string;
  date: string;
  source: string;
  rights: string;
  tags: { slug: string; label: string }[];
  sortYear: number;
  thumbSrc: string;
  fullSrc: string;
  people: { id: string; name: string }[];
  productions: { id: string; title: string; year: number }[];
}

export interface PersonPayload {
  id: string;
  name: string;
  role: string;
  years: string;
  bio: string;
  portraitSrc: string;
  items: ItemPayload[];
}

export function tagLabel(tag: string): string {
  const overrides: Record<string, string> = { 'fbi-file': 'FBI File' };
  return (
    overrides[tag] ??
    tag.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ')
  );
}

export async function getItemPayloads(): Promise<ItemPayload[]> {
  const [items, people, productions] = await Promise.all([
    getCollection('items'),
    getCollection('people'),
    getCollection('productions'),
  ]);
  const personById = new Map(people.map((p) => [p.data.id, p.data]));
  const productionById = new Map(productions.map((p) => [p.data.id, p.data]));

  const payloads = await Promise.all(
    items.map(async (entry) => {
      const meta = await itemImage(entry.data.image);
      const [thumb, full] = await Promise.all([
        getImage({ src: meta, width: 480, format: 'webp' }),
        getImage({ src: meta, width: 1000, format: 'webp' }),
      ]);
      return {
        id: entry.data.id,
        title: entry.data.title,
        caption: entry.data.caption,
        date: entry.data.date,
        source: entry.data.source,
        rights: entry.data.rights,
        tags: entry.data.tags.map((t) => ({ slug: t, label: tagLabel(t) })),
        sortYear: parseInt(entry.data.date.replace(/\D+/g, ''), 10) || 9999,
        thumbSrc: thumb.src,
        fullSrc: full.src,
        people: entry.data.people.map((id) => ({
          id,
          name: personById.get(id)!.name,
        })),
        productions: entry.data.productions.map((id) => ({
          id,
          title: productionById.get(id)!.title,
          year: productionById.get(id)!.year,
        })),
      };
    })
  );
  return payloads.sort((a, b) => a.sortYear - b.sortYear);
}

export async function getPersonPayloads(): Promise<PersonPayload[]> {
  const [people, itemPayloads] = await Promise.all([
    getCollection('people'),
    getItemPayloads(),
  ]);
  return Promise.all(
    people.map(async (entry) => {
      const portrait = await getImage({
        src: await personImage(entry.data.portrait),
        width: 480,
        format: 'webp',
      });
      return {
        id: entry.data.id,
        name: entry.data.name,
        role: entry.data.role,
        years: entry.data.years,
        bio: entry.data.bio,
        portraitSrc: portrait.src,
        items: itemPayloads.filter((i) =>
          i.people.some((p) => p.id === entry.data.id)
        ),
      };
    })
  );
}
