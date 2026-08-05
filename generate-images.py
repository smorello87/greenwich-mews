#!/usr/bin/env python3
"""
Generate placeholder images for Greenwich Mews Theater website
using Gemini 3 Pro Image via Vertex AI (nano-banana-pro skill)
"""

import requests
import base64
import subprocess
from pathlib import Path
import time

PROJECT_ID = "841145654214"
API_URL = f"https://aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/publishers/google/models/gemini-3-pro-image-preview:generateContent"

def get_access_token():
    """Get OAuth access token from gcloud CLI."""
    result = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()

    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get access token: {result.stderr}")
    return result.stdout.strip()


def generate_image(prompt: str, output_path: str) -> bool:
    """Generate an image from a text prompt."""

    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json"
    }

    payload = {
        "contents": {
            "role": "user",
            "parts": [{"text": prompt}]
        },
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"]
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=180)
        response.raise_for_status()
        result = response.json()

        for candidate in result.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    image_data = base64.b64decode(part["inlineData"]["data"])
                    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                    Path(output_path).write_bytes(image_data)
                    print(f"✓ Generated: {output_path}")
                    return True

        print(f"✗ No image in response for: {output_path}")
        return False
    except Exception as e:
        print(f"✗ Error generating {output_path}: {e}")
        return False


# Image definitions for Greenwich Mews Theater website
IMAGES = [
    # Hero image
    {
        "path": "public/images/narrative/hero-theater.png",
        "prompt": """A vintage sepia-toned photograph of a small Off-Broadway theater facade in 1950s Greenwich Village, New York City.
        The building has a modest marquee, brick facade, and shows the intimate scale of a community theater.
        Period-appropriate details: vintage cars parked on cobblestone street, old-fashioned street lamps.
        Atmospheric, documentary photography style, slightly grainy like archival photos.
        Warm brown and cream tones reminiscent of aged photographs."""
    },

    # Narrative section images
    {
        "path": "public/images/narrative/origins-1951.png",
        "prompt": """Black and white archival photograph of a 1950s church basement being converted into a small theater space.
        Workers setting up folding chairs, hanging simple curtains, exposed brick walls.
        The image has the feeling of grassroots community organizing.
        Documentary photography style, high contrast, grainy texture like vintage newsprint."""
    },
    {
        "path": "public/images/narrative/breaking-barriers.png",
        "prompt": """A powerful 1950s black and white photograph showing an integrated theater rehearsal -
        Black and white actors working together on stage, some sitting on the edge of the stage, others standing.
        The intimacy of a small theater space. Period-appropriate clothing and hairstyles.
        Documentary Civil Rights era photography aesthetic, high contrast, emotionally resonant."""
    },
    {
        "path": "public/images/narrative/productions-era.png",
        "prompt": """Dramatic black and white production still from a 1950s Off-Broadway play.
        A Black actress in the spotlight on a minimal stage set, expressing powerful emotion.
        The image captures the intensity of serious dramatic theater.
        High contrast theatrical lighting, deep shadows, the intimacy of a small theater.
        Archival photography quality with slight grain."""
    },
    {
        "path": "public/images/narrative/network-artists.png",
        "prompt": """A candid 1960s black and white photograph of a group of theater artists gathered backstage.
        Diverse group of actors, directors, playwrights in casual conversation.
        The warmth of creative community. Period-appropriate 1960s clothing and styling.
        Documentary photography style capturing an informal moment between performances."""
    },
    {
        "path": "public/images/narrative/decline-1973.png",
        "prompt": """A melancholy sepia-toned photograph of an empty theater space, circa 1970s.
        Vacant seats, a bare stage with a single work light, dust particles visible in the light beam.
        The feeling of an era ending, memories lingering in an abandoned space.
        Nostalgic, atmospheric, with the patina of aged photographs."""
    },

    # Portrait placeholders
    {
        "path": "public/images/people/portrait-1.png",
        "prompt": """A formal 1950s black and white portrait photograph of an African American male poet and playwright.
        Distinguished, intellectual appearance, wearing a suit and tie.
        Studio lighting in the style of James Van Der Zee portraits.
        High contrast, professional headshot quality from the mid-20th century."""
    },
    {
        "path": "public/images/people/portrait-2.png",
        "prompt": """A 1950s black and white portrait photograph of a white female theater director.
        Confident, artistic appearance, simple elegant clothing.
        The determined look of a pioneering woman in theater.
        Professional studio portrait style of the era."""
    },
    {
        "path": "public/images/people/portrait-3.png",
        "prompt": """A 1950s black and white portrait photograph of an African American male actor.
        Dignified, theatrical presence, wearing professional attire.
        The gravitas of a serious dramatic actor.
        Classic Hollywood portrait lighting style."""
    },
    {
        "path": "public/images/people/portrait-4.png",
        "prompt": """A 1950s black and white portrait photograph of an African American female actress.
        Elegant, poised, with expressive eyes that suggest depth of character.
        Glamorous yet accessible, theatrical lighting.
        Classic Hollywood portrait style of the Civil Rights era."""
    },

    # Document placeholders
    {
        "path": "public/images/docs/document-fbi.png",
        "prompt": """A close-up photograph of a declassified FBI surveillance document from the 1950s.
        Typewritten text on aged, yellowed paper with official stamps and redaction marks.
        Some text blacked out with heavy marker. Official letterhead visible.
        The aesthetic of Cold War era government documents, slightly crumpled paper texture."""
    },
    {
        "path": "public/images/docs/document-playbill.png",
        "prompt": """A vintage 1950s theater playbill cover photographed on a wooden table.
        Simple typography, art deco influenced design, the name of a play in bold letters.
        Aged paper with slight yellowing and foxing marks.
        The charming graphic design aesthetic of mid-century Off-Broadway theater programs."""
    },
    {
        "path": "public/images/docs/document-letter.png",
        "prompt": """A vintage typed letter on cream-colored paper from the 1950s.
        Professional correspondence on letterhead, visible typewriter imperfections.
        Aged paper texture, perhaps a coffee stain in the corner.
        The personal quality of mid-century business correspondence."""
    },

    # Production stills
    {
        "path": "public/images/productions/production-1.png",
        "prompt": """A dramatic 1950s black and white theatrical production photograph.
        Actors on a minimal stage set, dramatic spotlight creating strong shadows.
        The intensity of serious dramatic theater, emotional scene.
        High contrast theatrical photography from the Off-Broadway era."""
    },
    {
        "path": "public/images/productions/production-2.png",
        "prompt": """A 1960s black and white production still showing actors in an experimental theater piece.
        Avant-garde staging, unusual angles, theatrical masks or stylized costumes.
        The bold artistic choices of 1960s experimental Black theater.
        Documentary theatrical photography with dramatic lighting."""
    },

    # Book cover
    {
        "path": "public/images/book-cover.png",
        "prompt": """An academic book cover design with the title "Brotherhood or the New Hell"
        and subtitle "The Greenwich Mews Theater, 1951-1973".
        Sophisticated scholarly design with a vintage photograph incorporated.
        Deep brown and gold color scheme suggesting archival materials.
        University press aesthetic, dignified and historically significant."""
    },

    # Author portrait
    {
        "path": "public/images/author-portrait.png",
        "prompt": """A professional contemporary academic portrait photograph.
        A female professor in her office or library setting, warm natural lighting.
        Approachable yet scholarly appearance, surrounded by books.
        Modern academic photography style, high quality professional headshot."""
    }
]


def main():
    print("=" * 60)
    print("Generating images for Greenwich Mews Theater website")
    print("Using Gemini 3 Pro Image via Vertex AI")
    print("=" * 60)
    print()

    success_count = 0

    for i, img in enumerate(IMAGES, 1):
        print(f"[{i}/{len(IMAGES)}] Generating: {img['path']}")
        if generate_image(img["prompt"], img["path"]):
            success_count += 1

        # Brief pause between requests to avoid rate limiting
        if i < len(IMAGES):
            time.sleep(2)

    print()
    print("=" * 60)
    print(f"Complete: {success_count}/{len(IMAGES)} images generated")
    print("=" * 60)


if __name__ == "__main__":
    main()
