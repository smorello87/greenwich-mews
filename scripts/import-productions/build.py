"""Turn parsed.json into src/data/productions.json.

Expands the role abbreviations defined in the document's own KEY, lifts
playwright/director/cast out of the credit list for the table columns, and
applies a small set of hand-verified source corrections.
"""

import json
import pathlib
import re
import unicodedata

OUT = pathlib.Path(__file__).resolve().parents[2] / "src/data/productions.json"

# From the "KEY FOR ROLES" block at the top of the document, plus the plural
# forms and Asst. Producer, which the document uses without defining.
ROLE_KEY = {
    "AD": "Asst. Director",
    "Admin Coord": "Administrative Coordinator",
    "Artistic Coord": "Artistic Coordinator",
    "Artistic Dir.": "Artistic Director",
    "ASM": "Asst. Stage Manager",
    "BM": "Business Manager",
    "Coord": "Coordinator",
    "GM": "General Management",
    "HM": "House Manager",
    "PM": "Production Manager",
    "PR": "Public Relations",
    "PSM": "Production Stage Manager",
    "SM": "Stage Manager",
    "TD": "Technical Director",
    "TM": "Theatre Manager",
    "Trans.": "Translation",
    "PA": "Production Asst.",
    "PAs": "Production Assts.",
    "TA": "Technical Asst.",
    "TAs": "Technical Assts.",
    "WR": "Wardrobe",
    "AP": "Asst. Producer",
    "APs": "Asst. Producers",
    "MDs": "Musical Directors",
    "PM, HM": "Production Manager, House Manager",
    "AD, SM": "Asst. Director, Stage Manager",
    "Artistic Coord, PM": "Artistic Coordinator, Production Manager",
    "Musical Dir": "Musical Director",
    "Musical Dir.": "Musical Director",
    "Music Dir.": "Musical Director",
    "Music Dir": "Musical Director",
    "Choreo": "Choreography",
    "Production Coord": "Production Coordinator",
    "Set": "Sets",
    "Lighting": "Lights",
    "Original design": "Original Design",
    "Playwright, Dir.": "Playwright & Director",
    # Not in the KEY, but in both cases the same person carries the spelled-out
    # role in neighbouring entries: Stella Holt as Admin Coord (1954-55) and
    # Laurence L. Olvin as Production Coord (1957-58).
    "AC": "Administrative Coordinator",
    "PC": "Production Coordinator",
    "Music Arr. and Dir.": "Music Arrangement & Direction",
    "Musical Arr": "Musical Arrangement",
    "Associate Dir.": "Associate Director",
    "Managing Dir": "Managing Director",
    "DIrector": "Director",
    "Adapted and Arr.": "Adapted & Arranged by",
}

# Titles as printed carry billing copy that belongs in `notes`, not the Title
# column. Left value replaces the title; right value becomes the note.
TITLE_FIXES = {
    '"2 for Fun" Double Bill: The Anniversary / Switch in Time': (
        "The Anniversary / Switch in Time", 'Presented as the "2 for Fun" double bill'),
    '"Musicomedy" Variety Show': ("Musicomedy", "Variety show"),
    "The Prodigal Son, A Gospel Song-Play": ("The Prodigal Son", "A gospel song-play"),
    "Walk Together Children, the black scene in prose, poetry and song": (
        "Walk Together Children", "The black scene in prose, poetry and song"),
    "The Trials of Brother Jero and The Strong Breed": (
        "The Trials of Brother Jero / The Strong Breed", "Double bill"),
    "La Difunta, Cruce de Vías, and Las Pericas": (
        "La Difunta, Cruce de Vías, and Las Pericas",
        "Triple bill. The source lists the cast separately for each play: "
        "La Difunta — Lolina Gutierrez, Inez Ivette, Emilio Rodríguez; "
        "Cruce de Vías — Gay Darlene Bidart, Tony Díaz; "
        "Las Pericas — Miriam Cruz, Milagros Horrego, Linda Monteiro, Shelly Pearson."),
    # 1968 revival; the document spells it "Jerico" here and "Jericho" in 1964.
    "Jerico-Jim Crow": ("Jericho-Jim Crow", "Revival of the 1964 production"),
}

# Authorial credit to use in the Playwright column where the document gives no
# "Playwright" line. The original credit line is kept in `credits`.
PLAYWRIGHT_FALLBACK = {
    "The Student Prince": "Dorothy Donnelly (book & lyrics)",
    "The Mikado": "W.S. Gilbert (libretto)",
    "The World of My America": "Paulene Myers (adapted & arranged)",
    "Carricknabauna": "Padraic Colum, Basil Burwell (adapted)",
}

# One spelling per person. Left side is what the source prints somewhere; right
# side is the form used everywhere. Each entry is either an outright typo or a
# person the source bills inconsistently across productions — collapsing them
# is what makes a name findable from the search box. Names the author could not
# resolve (Joe Liberman/Lieberman, the James Clarks) are deliberately NOT here;
# see the README.
NAME_FIXES = {
    # Typos
    "MacGregor Gibbsss": "MacGregor Gibbs",
    "Archie L. Greshan": "Archie L. Gresham",
    "Antoinnette": "Antoinette",
    "Sally Brickhead": "Sally Birckhead",
    "Maurice Schadad": "Maurice Schaded",
    # The source spells this composer both ways on consecutive credit lines of
    # Carricknabauna; the author confirms Bailin. The two Music lines then
    # collapse into one.
    "Harriet Ballin": "Harriet Bailin",
    # Inconsistent billing of one person. Preferred spellings confirmed by the
    # author except where noted.
    'Antoinette "Toni" Kray': "Antoinette Kray",
    "Ann Fielding": "Anne Fielding",
    "Thomas Vasiloff": "Thomas S. Vasiloff",
    "Fran Drucker": "Frances Drucker",
    # He changed his stage name repeatedly; one form keeps him recognisable.
    "Robert Graham Brown": "R. Graham Brown",
    "Jim Gore": "James Gore",
    "Dave Lucas": "David Lucas",
    "LD Clements": "L.D. Clements",
    "Manolo De Orellana": "Manolo de Orellana",
    "William Schwenck Gilbert": "W.S. Gilbert",
    # Father and son, billed as one word apart. Hyphenated to match the 1955
    # spelling; the "Jr." keeps them distinct.
    "Austin Briggs Hall Jr.": "Austin Briggs-Hall Jr.",
    # Not yet confirmed by the author — see the README.
    "James McMahon": "James B. McMahon",
    # Accents the source drops in one entry but not others
    "Gilberto Zaldivar": "Gilberto Zaldívar",
    "Rene Marqués": "René Marqués",
    # Phrasing the source varies between entries
    "in assoc. with": "in association with",
    ", in association with": " in association with",
    # Name spellings
    "Séan O'Casey": "Seán O'Casey",
    "Sean O'Casey": "Seán O'Casey",
    "Seán O’Casey": "Seán O'Casey",
    # The source omits the comma where this cast list wraps.
    "Jenny Duncan Brendan Fay": "Jenny Duncan, Brendan Fay",
    "William Walsh and Nancy Kendall Stitt, Soloist":
        "William Walsh, Nancy Kendall Stitt (soloist)",
    "and the Hugh Porter Gospel Singers": "The Hugh Porter Gospel Singers",
    "Cruce de Vias": "Cruce de Vías",
}

# Corrections applied after role canonicalisation, keyed by (title, role).
# The source credits Gilbert as a composer of The Mikado; Sullivan wrote the
# music and Gilbert the libretto.
CREDIT_FIXES = {
    ("The Mikado", "Composer"): "Arthur Sullivan",
}

# The source groups this triple bill's cast by play. The per-play attribution is
# kept in `notes`; `cast` holds the plain list so search and display behave.
CAST_OVERRIDES = {
    "La Difunta, Cruce de Vías, and Las Pericas": [
        "Lolina Gutierrez", "Inez Ivette", "Emilio Rodríguez",
        "Gay Darlene Bidart", "Tony Díaz",
        "Miriam Cruz", "Milagros Horrego", "Linda Monteiro", "Shelly Pearson",
    ],
}

# Credit values that list two people with "and" become comma-separated like
# every other multi-name field. Only applied when both sides are full names, so
# "Gary and Timmy Harris" and "in assoc. with ..." clauses are left alone.
FULL_NAME = r"(?:[A-ZÁÉÍÓÚÑ][\w.'’-]*\s+)+[A-ZÁÉÍÓÚÑ][\w.'’-]*"
AND_PAIR = re.compile(rf"^({FULL_NAME}) and ({FULL_NAME})$")

CAST_SPLIT = re.compile(r"[,;](?![^(]*\))")
ABBREV_END = re.compile(r"(\b(?:Jr|Sr|II|III)|\b[A-Z])\.$")

FEATURED = {
    "in-splendid-error-1954":
        "William Branch's drama about Frederick Douglass and the raid on Harpers "
        "Ferry, directed by Salem Ludwig, with William Marshall and Clarice Taylor.",
    "trouble-in-mind-1955":
        "Alice Childress's play about racism inside the theatre industry, "
        "co-directed by the playwright and Clarice Taylor, who also led the cast.",
    "a-land-beyond-the-river-1957":
        "Loften Mitchell's drama of the South Carolina school desegregation fight, "
        "with Diana Sands and Helen Martin. Romare Bearden supplied the original design.",
    "the-cave-dwellers-1961":
        "William Saroyan's parable of a company of outcasts squatting in a condemned "
        "theatre, starring Geraldine Fitzgerald, with Joanna Miles and Anthony Zerbe.",
    "walk-in-darkness-1963":
        "William Hairston's drama, designed by Ming Cho Lee, with a cast that "
        "included Roger Robinson and Clarence Williams III.",
    "jericho-jim-crow-1964":
        "Langston Hughes's gospel song-play on the history of the freedom struggle, "
        "co-directed by Alvin Ailey and William Hairston with the Hugh Porter Gospel Singers.",
    "the-prodigal-son-1965":
        "Hughes's gospel song-play directed by Vinnette Carroll, choreographed by "
        "Syvilla Fort, introducing Hattie Winston.",
    "the-oxcart-la-carreta-1967":
        "René Marqués's account of a Puerto Rican family's migration, directed by "
        "Lloyd Richards, with Míriam Colón, Lucy Boscana and Raúl Juliá.",
    "the-trials-of-brother-jero-the-strong-breed-1967":
        "Wole Soyinka's double bill, directed by Cynthia Belgrave, with Mary Alice, "
        "Roger Robinson and Harold Scott.",
    "yerma-1971":
        "Federico García Lorca's tragedy for the Greenwich Mews Spanish Theatre, "
        "directed by René Buch with choreography by Graciela Daniele.",
}

# Labels that name two jobs at once. Split so each job becomes its own field —
# "Sets, Lights: Frank Wicks" is Sets: Frank Wicks *and* Lights: Frank Wicks.
# Only these exact labels split; anything else with a comma or "and" in it
# ("Music Arr. and Dir.", "Book and Lyrics") is a single role name.
COMPOUND_ROLES = {
    "Sets, Lights": ("Sets", "Lights"),
    "Sets, Lighting": ("Sets", "Lights"),
    "Sets and Lights": ("Sets", "Lights"),
    "Sets, Costumes": ("Sets", "Costumes"),
    "Costumes, Lights": ("Costumes", "Lights"),
    "Lights, Sound": ("Lights", "Sound"),
    "Music, Sound": ("Music", "Sound"),
    "PM, HM": ("PM", "HM"),
    "Artistic Coord, PM": ("Artistic Coord", "PM"),
    "AD, SM": ("AD", "SM"),
    "Producer, Director": ("Producer", "Director"),
    "Playwright, Dir.": ("Playwright", "Director"),
}

# One label per job, so the same role never appears under two spellings.
ROLE_CANONICAL = {
    "Playwrights": "Playwright",
    "Directors": "Director",
    "Producers": "Producer",
    "Composers": "Composer",
    "Set": "Sets",
    "Set Design": "Sets",
    "Set Designer": "Sets",
    "Lighting": "Lights",
    "Light Design": "Lights",
    "Costume Design": "Costumes",
    "Choreo": "Choreography",
    "Book and Lyrics": "Book & Lyrics",
    "Asst. Producers": "Asst. Producer",
    "Production Assts.": "Production Asst.",
    "Technical Assts.": "Technical Asst.",
    "Musical Directors": "Musical Director",
    "Original design": "Original Design",
}

# Credits render in this order in the overlay, so every production reads the
# same way regardless of the order the source happened to print them in.
ROLE_ORDER = [
    "Playwright", "Adapted by", "Adapted & Arranged by", "Book & Lyrics",
    "Lyricist", "Librettist", "Composer", "Translation",
    "Director", "Asst. Director", "Associate Director", "Artistic Director",
    "Managing Director", "Choreography",
    "Music", "Music Arrangement & Direction", "Musical Arrangement",
    "Musical Director", "Music Supervision", "Orchestrations",
    "Producer", "Asst. Producer", "Co-producer", "Presented by", "Sponsors",
    "General Management", "Business Manager", "Theatre Manager",
    "Administrative Coordinator", "Artistic Coordinator",
    "Production Coordinator", "Coordinator",
    "Production Manager", "Production Stage Manager", "Stage Manager",
    "Asst. Stage Manager", "Technical Director", "Production Asst.",
    "Technical Asst.", "House Manager",
    "Sets", "Original Design", "Design", "Costumes", "Costumer", "Wardrobe",
    "Lights", "Sound", "Props",
    "Public Relations", "Press Agent", "Native American Consultant",
    "Understudies",
]

PLAYWRIGHT_ROLES = {"Playwright"}
DIRECTOR_ROLES = {"Director"}


def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def fix_names(value):
    for wrong, right in NAME_FIXES.items():
        value = value.replace(wrong, right)
    pair = AND_PAIR.match(value)
    return f"{pair.group(1)}, {pair.group(2)}" if pair else value


def canonical_roles(role):
    """One source label -> the one or two canonical roles it stands for."""
    out = []
    for part in COMPOUND_ROLES.get(role, (role,)):
        expanded = ROLE_KEY.get(part, part)          # abbreviation -> words
        out.append(ROLE_CANONICAL.get(expanded, expanded))  # -> one spelling
    return out


def main():
    entries = json.load(open("parsed.json", encoding="utf-8"))

    # Ladybug: the label "Native American Consultant" wraps across two blocks,
    # so the parser saw the name as an unlabelled line.
    for e in entries:
        if e["title"] == "Ladybug":
            e["credits"].append(
                {"role": "Native American Consultant", "names": "Suzan Shown (Harjo)"})

    out = []
    for e in entries:
        title, note = e["title"], ""
        if title in TITLE_FIXES:
            title, note = TITLE_FIXES[title]

        playwright = director = None
        cast = []
        # Roles the source lists more than once (e.g. "PR" and "Public Relations"
        # on separate lines) collapse into a single field, in first-seen order.
        credits: "dict[str, list[str]]" = {}

        for c in e["credits"]:
            names = fix_names(c["names"])
            if c["role"] == "Cast":
                cast = CAST_OVERRIDES.get(title)
                if cast is None:
                    cast = []
                    for n in CAST_SPLIT.split(names):
                        n = n.strip()
                        if not n:
                            continue
                        if n.endswith(".") and not ABBREV_END.search(n):
                            n = n[:-1]
                        cast.append(n)
                continue
            for role in canonical_roles(c["role"]):
                value = CREDIT_FIXES.get((title, role), names)
                bucket = credits.setdefault(role, [])
                if value not in bucket:
                    bucket.append(value)

        for role in credits:
            if role in PLAYWRIGHT_ROLES:
                playwright = ", ".join(credits[role])
            elif role in DIRECTOR_ROLES:
                director = ", ".join(credits[role])

        if playwright is None:
            playwright = PLAYWRIGHT_FALLBACK.get(title)

        pid = f"{slugify(title)}-{e['year']}"
        out.append({
            "id": pid,
            "year": e["year"],
            "title": title,
            "company": e["company"],
            "playwright": playwright,
            "director": director,
            "cast": cast,
            "credits": [
                {"role": r, "names": ", ".join(credits[r])}
                for r in sorted(
                    credits,
                    key=lambda r: ROLE_ORDER.index(r) if r in ROLE_ORDER else len(ROLE_ORDER),
                )
            ],
            "notes": note,
            "featured": pid in FEATURED,
            "image": "production-1.png" if pid in FEATURED else None,
            "description": FEATURED.get(pid),
        })

    out.sort(key=lambda p: (p["year"], p["title"]))

    ids = [p["id"] for p in out]
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    missing = set(FEATURED) - set(ids)
    assert not missing, missing

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"wrote {len(out)} productions")
    print("no playwright:", [p["id"] for p in out if not p["playwright"]])
    print("no director:", [p["id"] for p in out if not p["director"]])
    print("no cast:", [p["id"] for p in out if not p["cast"]])


if __name__ == "__main__":
    main()
