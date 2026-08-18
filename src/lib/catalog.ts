import { getCollection } from 'astro:content';
import { getImage } from 'astro:assets';
import { itemImage, personImage } from './images';
import { COMPANIES } from '../content.config';

// Client-side payload shapes shared by the archive page and the modals.
export interface ItemPayload {
  id: string;
  figId: string;
  title: string;
  caption: string;
  creator: string;
  date: string;
  source: string;
  rights: string;
  /** What this record is still missing; empty when the row is complete. */
  needs: string[];
  tags: { slug: string; label: string }[];
  sortYear: number;
  /** Null when no scan exists yet — the card renders an empty frame. */
  thumbSrc: string | null;
  fullSrc: string | null;
  people: { id: string; name: string }[];
  /** Names linkable via the contributor index rather than a full profile. */
  contributors: string[];
  productions: { id: string; title: string; year: number }[];
}

export interface ProductionPayload {
  id: string;
  year: number;
  title: string;
  company: string;
  playwright: string;
  director: string;
  cast: string[];
  credits: { role: string; names: string }[];
  notes: string;
}

/** One name from the productions list, with everywhere it appears. */
export interface ContributorPayload {
  slug: string;
  name: string;
  /** Slug of the matching people.json profile, when there is one. */
  profileId: string | null;
  appearances: {
    productionId: string;
    title: string;
    year: number;
    roles: string[];
  }[];
}

export interface PersonPayload {
  id: string;
  name: string;
  role: string;
  years: string;
  bio: string;
  /** Null when no portrait exists yet — the modal renders an empty frame. */
  portraitSrc: string | null;
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
      // An item with no scan yet still gets a card; the image slots stay null
      // and the page renders an empty frame in place of a picture.
      const meta = entry.data.image ? await itemImage(entry.data.image) : null;
      const [thumb, full] = meta
        ? await Promise.all([
            getImage({ src: meta, width: 480, format: 'webp' }),
            getImage({ src: meta, width: 1000, format: 'webp' }),
          ])
        : [null, null];
      return {
        id: entry.data.id,
        figId: entry.data.figId,
        title: entry.data.title,
        caption: entry.data.caption,
        creator: entry.data.creator,
        date: entry.data.date,
        source: entry.data.source,
        rights: entry.data.rights,
        needs: entry.data.needs,
        tags: entry.data.tags.map((t) => ({ slug: t, label: tagLabel(t) })),
        sortYear: parseInt(entry.data.date.replace(/\D+/g, ''), 10) || 9999,
        thumbSrc: thumb?.src ?? null,
        fullSrc: full?.src ?? null,
        people: entry.data.people.map((id) => ({
          id,
          name: personById.get(id)!.name,
        })),
        contributors: entry.data.contributors,
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

export function companyLabel(slug: string): string {
  return COMPANIES[slug as keyof typeof COMPANIES] ?? slug;
}

/** Every field the "Full Info" overlay shows, in chronological order. */
export async function getProductionPayloads(): Promise<ProductionPayload[]> {
  const productions = await getCollection('productions');
  return productions
    .map((entry) => ({
      id: entry.data.id,
      year: entry.data.year,
      title: entry.data.title,
      company: companyLabel(entry.data.company),
      playwright: entry.data.playwright,
      director: entry.data.director,
      cast: entry.data.cast,
      credits: entry.data.credits,
      notes: entry.data.notes,
    }))
    .sort((a, b) => a.year - b.year || a.title.localeCompare(b.title));
}

// A credit value can name several people ("David Lipsky, Richard Falk") and can
// hang a clause off the end ("Dorothy Raedler in association with Stella Holt").
// Commas outside parentheses separate names; the clause introduces more of them.
const NAME_SEPARATOR = /,\s*(?![^(]*\))|\s+in association with\s+/i;

export function splitNames(value: string): string[] {
  return value
    .split(NAME_SEPARATOR)
    .map((n) => n.trim())
    .filter(Boolean);
}

export function contributorSlug(name: string): string {
  return name
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

/**
 * Every name that appears anywhere in the productions list, indexed by slug,
 * with the productions and roles it appears under. Sorted so the modal can show
 * a person's work chronologically.
 */
export async function getContributorPayloads(): Promise<ContributorPayload[]> {
  const [productions, people] = await Promise.all([
    getCollection('productions'),
    getCollection('people'),
  ]);
  const profileBySlug = new Map(
    people.map((p) => [contributorSlug(p.data.name), p.data.id])
  );

  const byslug = new Map<string, ContributorPayload>();

  const record = (name: string, role: string, prod: (typeof productions)[number]['data']) => {
    const slug = contributorSlug(name);
    if (!slug) return;
    let entry = byslug.get(slug);
    if (!entry) {
      entry = {
        slug,
        name,
        profileId: profileBySlug.get(slug) ?? null,
        appearances: [],
      };
      byslug.set(slug, entry);
    }
    let appearance = entry.appearances.find((a) => a.productionId === prod.id);
    if (!appearance) {
      appearance = { productionId: prod.id, title: prod.title, year: prod.year, roles: [] };
      entry.appearances.push(appearance);
    }
    if (!appearance.roles.includes(role)) appearance.roles.push(role);
  };

  for (const entry of productions) {
    const prod = entry.data;
    for (const credit of prod.credits) {
      for (const name of splitNames(credit.names)) record(name, credit.role, prod);
    }
    for (const name of prod.cast) record(name, 'Cast', prod);
  }

  for (const entry of byslug.values()) {
    entry.appearances.sort((a, b) => a.year - b.year || a.title.localeCompare(b.title));
  }
  return [...byslug.values()].sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * The subset of contributors worth linking — those who appear in more than one
 * production, so a click always leads somewhere. Keyed by the name exactly as
 * it is printed, which is what the modal has to match against.
 */
export async function getLinkableContributors(): Promise<
  Record<string, ContributorPayload>
> {
  const contributors = await getContributorPayloads();
  return Object.fromEntries(
    contributors
      .filter((c) => c.appearances.length > 1)
      .map((c) => [c.name, c])
  );
}

export async function getPersonPayloads(): Promise<PersonPayload[]> {
  const [people, itemPayloads] = await Promise.all([
    getCollection('people'),
    getItemPayloads(),
  ]);
  return Promise.all(
    people.map(async (entry) => {
      // Null until a real portrait is cleared for this person.
      const portrait = entry.data.portrait
        ? await getImage({
            src: await personImage(entry.data.portrait),
            width: 480,
            format: 'webp',
          })
        : null;
      return {
        id: entry.data.id,
        name: entry.data.name,
        role: entry.data.role,
        years: entry.data.years,
        bio: entry.data.bio,
        portraitSrc: portrait?.src ?? null,
        items: itemPayloads.filter((i) =>
          i.people.some((p) => p.id === entry.data.id)
        ),
      };
    })
  );
}
