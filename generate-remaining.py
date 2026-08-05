#!/usr/bin/env python3
"""
Generate remaining placeholder images (ones that failed due to rate limiting)
"""

import requests
import base64
import subprocess
from pathlib import Path
import time

PROJECT_ID = "841145654214"
API_URL = f"https://aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/global/publishers/google/models/gemini-3-pro-image-preview:generateContent"

def get_access_token():
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


def generate_image(prompt: str, output_path: str, retries: int = 3) -> bool:
    for attempt in range(retries):
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
            if response.status_code == 429:
                wait_time = 30 * (attempt + 1)
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
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
            if "429" in str(e):
                wait_time = 30 * (attempt + 1)
                print(f"  Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            print(f"✗ Error generating {output_path}: {e}")
            return False
    return False


# Remaining images that failed
REMAINING_IMAGES = [
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
        "path": "public/images/people/portrait-4.png",
        "prompt": """A 1950s black and white portrait photograph of an African American female actress.
        Elegant, poised, with expressive eyes that suggest depth of character.
        Glamorous yet accessible, theatrical lighting.
        Classic Hollywood portrait style of the Civil Rights era."""
    },
    {
        "path": "public/images/docs/document-fbi.png",
        "prompt": """A close-up photograph of a declassified FBI surveillance document from the 1950s.
        Typewritten text on aged, yellowed paper with official stamps and redaction marks.
        Some text blacked out with heavy marker. Official letterhead visible.
        The aesthetic of Cold War era government documents, slightly crumpled paper texture."""
    },
    {
        "path": "public/images/docs/document-letter.png",
        "prompt": """A vintage typed letter on cream-colored paper from the 1950s.
        Professional correspondence on letterhead, visible typewriter imperfections.
        Aged paper texture, perhaps a coffee stain in the corner.
        The personal quality of mid-century business correspondence."""
    },
    {
        "path": "public/images/productions/production-1.png",
        "prompt": """A dramatic 1950s black and white theatrical production photograph.
        Actors on a minimal stage set, dramatic spotlight creating strong shadows.
        The intensity of serious dramatic theater, emotional scene.
        High contrast theatrical photography from the Off-Broadway era."""
    },
    {
        "path": "public/images/book-cover.png",
        "prompt": """An academic book cover design with the title "Brotherhood or the New Hell"
        and subtitle "The Greenwich Mews Theater, 1951-1973".
        Sophisticated scholarly design with a vintage photograph incorporated.
        Deep brown and gold color scheme suggesting archival materials.
        University press aesthetic, dignified and historically significant."""
    },
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
    print("Generating remaining images (with longer delays)")
    print("=" * 60)
    print()

    success_count = 0

    for i, img in enumerate(REMAINING_IMAGES, 1):
        print(f"[{i}/{len(REMAINING_IMAGES)}] Generating: {img['path']}")
        if generate_image(img["prompt"], img["path"]):
            success_count += 1

        # Longer pause between requests
        if i < len(REMAINING_IMAGES):
            print("  Waiting 15s before next request...")
            time.sleep(15)

    print()
    print("=" * 60)
    print(f"Complete: {success_count}/{len(REMAINING_IMAGES)} images generated")
    print("=" * 60)


if __name__ == "__main__":
    main()
