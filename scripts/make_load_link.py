"""Print the tcg-arena.fr load link for a hosted Vibes-Game.json URL.

Usage:
    python scripts/make_load_link.py [URL]

If URL is omitted, uses the default GitHub Pages URL.
"""
import base64
import sys

DEFAULT_URL = "https://deuceyy.github.io/tcgarena-vibes/Vibes-Game.json"


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    encoded = base64.b64encode(url.encode("utf-8")).decode("ascii")
    load_link = f"https://tcg-arena.fr/load/{encoded}"
    print(f"Source URL:  {url}")
    print(f"Base64:      {encoded}")
    print(f"Load link:   {load_link}")


if __name__ == "__main__":
    main()
