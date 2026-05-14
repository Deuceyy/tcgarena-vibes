# TCG Arena — Vibes TCG

A loader for [Vibes TCG](https://vibes.game) on [tcg-arena.fr](https://tcg-arena.fr), the JSON-driven multiplayer card simulator.

Once hosted, anyone can add Vibes to their Games tab by clicking a single load link.

## Quick start (using a published build)

Open this link in a browser. It will add Vibes TCG to your Games tab on tcg-arena.fr:

```
https://tcg-arena.fr/load/aHR0cHM6Ly9kZXVjZXl5LmdpdGh1Yi5pby90Y2dhcmVuYS12aWJlcy9WaWJlcy1HYW1lLmpzb24=
```

(That's `base64("https://deuceyy.github.io/tcgarena-vibes/Vibes-Game.json")`.)

## Repo layout

```
.
├── sets/                       # source card data, one file per set (drop new set in here)
│   ├── eth.json                # Enter the Huddle (201 cards incl. Fishsicle token)
│   └── lotl.json               # Legends of the Lils (151 cards)
├── docs/                       # GitHub Pages root — served at deuceyy.github.io/tcgarena-vibes/
│   ├── Vibes-Game.json         # top-level game config (rules, zones, deck rules)
│   ├── Vibes-CardList.json     # all cards in TCG Arena format
│   ├── Vibes-Decks.json        # preset decks (empty list to start)
│   ├── images/                 # one PNG per card, named <id>.png
│   └── tokens/                 # Baron's Favor + other draggable token art
├── dist/                       # local-inspection copy of the main Game.json
├── reference/                  # downloaded reference Game JSONs (Riftbound)
├── scripts/
│   └── make_load_link.py       # prints the tcg-arena.fr/load/<base64> URL
├── build_game_json.py          # the build script
├── SCHEMA.md                   # reverse-engineered TCG Arena JSON schema
└── SOURCE_SCHEMA.md            # the Vibes source data schema
```

## Adding a new set (Set 3 "Birb and Pengu")

1. Drop the new JSON into `sets/` (e.g. `sets/birb.json`). Cards must use the same schema as `sets/eth.json` (see [SOURCE_SCHEMA.md](SOURCE_SCHEMA.md)).
2. If the new set uses a new set code, add it to `SET_NAMES` in [build_game_json.py](build_game_json.py).
3. Run the build:
   ```
   python build_game_json.py
   ```
   This is idempotent — it only copies/fetches images that aren't already in `docs/images/`.
4. Commit and push:
   ```
   git add -A
   git commit -m "Add set: Birb and Pengu"
   git push
   ```
5. GitHub Pages will redeploy automatically. Existing load links keep working.

## Republishing

The hosted URL never changes, so users who already added Vibes to their Games tab will automatically pick up new cards on their next session.

If you change the schema or zone layout (i.e. edit `build_game_json.py`'s `build_game_json()` or `build_gameplay_mode()`), users may need to re-load via the load link — but their decks stay intact (decks reference card ids, not the full Game.json).

## Getting the load link

```
python scripts/make_load_link.py
```

For a non-default URL:
```
python scripts/make_load_link.py https://my-fork.github.io/tcgarena-vibes/Vibes-Game.json
```

## Game rules baked into Vibes-Game.json

| Rule | Value |
|---|---|
| Deck size | exactly 52 |
| Max copies per card | 4 |
| Starting hand | 5 |
| Mulligan | any number of cards → bottom of deck, no shuffle, redraw to 5 |
| Per-turn auto-draw | 0 (manual, driven by vibe check outcomes) |
| Shared turn / cycle | yes |
| Tokens (Fishsicle) | excluded from the 52-card count and the 15-permanent win condition |

## Image sources

329 PNGs come from the Card Shop Simulator mod (`disabled_mods/VibesCardShopMod_DISABLED/images/`). The remaining 22 fall back to the `vibes.game` public CDN at `ocg-card-catalog.s3.us-west-2.amazonaws.com/Spoiler_Previews/<id>.png`. The build script copies + caches both into `docs/images/`.

If a card's image is missing from both sources, the build prints a warning and the card falls back to the default card back.

## Baron's Favor token

`docs/tokens/baron-token.png` is currently a **placeholder** (the Vibes logo). Replace it with a proper Baron icon to fix.

## Publishing this repo

This repo was scaffolded locally. To publish:

1. Create an empty repo at https://github.com/new named `tcgarena-vibes` (public).
2. From this directory:
   ```
   git remote add origin https://github.com/Deuceyy/tcgarena-vibes.git
   git branch -M main
   git push -u origin main
   ```
3. On the repo's **Settings → Pages**, set source to `Deploy from a branch` → branch `main` → folder `/docs`.
4. After ~1 minute, `https://deuceyy.github.io/tcgarena-vibes/Vibes-Game.json` will be live.
5. Run `python scripts/make_load_link.py` to print the user-facing load link.

(Or, if you have the GitHub CLI: `gh repo create tcgarena-vibes --public --source=. --push` then enable Pages.)
