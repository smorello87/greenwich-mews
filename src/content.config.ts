import { defineCollection, z } from 'astro:content';
import { file } from 'astro/loaders';
import peopleData from './data/people.json';
import productionsData from './data/productions.json';

// Id sets for cross-reference validation. A typo'd reference in items.json
// fails the build instead of silently rendering a broken page.
const personIds = new Set(peopleData.map((p) => p.id));
const productionIds = new Set(productionsData.map((p) => p.id));

const slugPattern = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const people = defineCollection({
  loader: file('src/data/people.json'),
  schema: z.object({
    id: z.string().regex(slugPattern),
    name: z.string().min(1),
    role: z.string().min(1),
    years: z.string().min(1),
    thumbnail: z.string().min(1),
    portrait: z.string().min(1),
    bio: z.string().min(1),
  }),
});

const productions = defineCollection({
  loader: file('src/data/productions.json'),
  schema: z.object({
    id: z.string().regex(slugPattern),
    year: z.number().int(),
    title: z.string().min(1),
    playwright: z.string().min(1),
    director: z.string().min(1),
    cast: z.array(z.string()),
    notes: z.string(),
    featured: z.boolean(),
    image: z.string().nullable(),
    description: z.string().nullable(),
  }),
});

const items = defineCollection({
  loader: file('src/data/items.json'),
  schema: z.object({
    id: z.string().regex(slugPattern),
    title: z.string().min(1),
    image: z.string().min(1),
    caption: z.string().min(1),
    date: z.string().min(1),
    source: z.string().min(1),
    rights: z.string().min(1),
    tags: z.array(z.string().regex(slugPattern)).min(1),
    people: z.array(
      z.string().refine((id) => personIds.has(id), (id) => ({
        message: `Unknown person id "${id}" — must match an id in people.json`,
      }))
    ),
    productions: z.array(
      z.string().refine((id) => productionIds.has(id), (id) => ({
        message: `Unknown production id "${id}" — must match an id in productions.json`,
      }))
    ),
  }),
});

export const collections = { people, productions, items };
