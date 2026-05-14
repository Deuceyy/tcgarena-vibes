# Vibes TCG Source Schema

Source files:
- `C:/Users/Redux/Downloads/vibes_cards.json` — 353 cards, both sets combined (canonical)
- `C:/Users/Redux/Downloads/vibes tcg simulator/VibesCardShopMod/VibesCards.json` — 351 cards (older snapshot, missing `BasicRod` + `Fishsicle`)
- `C:/Users/Redux/Downloads/vibes tcg simulator/disabled_mods/VibesCardShopMod_DISABLED/images/` — 329 PNG card images keyed by card `id`

Per the build script's "drop a file in /sets" model, we split the canonical file into:
- `sets/eth.json` — Enter the Huddle (set 1, 202 cards)
- `sets/lotl.json` — Legends of the Lils (set 2, 151 cards)
- `sets/birb.json` — Birb and Pengu (set 3, future)

## Card object schema

Every card has exactly these 14 keys:

| Field | Type | Notes |
|---|---|---|
| `id` | string | PascalCase, no spaces (e.g. `ContemplationPenguin`). Matches image filename. |
| `name` | string | Display name with spaces, punctuation (e.g. `"Contemplation Penguin"`) |
| `set` | enum | `"Eth"` (Enter the Huddle, 202) or `"Lotl"` (Legends of the Lils, 151) |
| `type` | enum | See type distribution below |
| `color` | enum | Single color OR comma-pair (e.g. `"Blue, Red"`) |
| `border` | enum | Same set as `color` minus pairs |
| `rarity` | enum | `Common` / `Uncommon` / `Rare` / `Mythic` / `""` (BasicRod, Fishsicle) |
| `vibe` | int or null | Penguin's vibe value. `null` for non-Penguins. |
| `cost` | `{amount: int, color: string}` | Fish cost = paid with Rods. Colored cost = paid with Pudge from huddle. |
| `pudge` | `{amount: int, color: string}` | Pudge this card produces when in huddle |
| `cardText` | string | Rules text; `|` = line break; `_R_`/`_Y_`/`_G_`/`_B_`/`_P_`/`_F_`/`_T_` = mana symbols; `[ACT]` = activated ability |
| `artUrl` | string (digits) | Used internally by the simulator mod; NOT a URL. Image lookup is by `id`. |
| `turnedOn` | bool | Always `true` in current data; presumably a feature toggle |
| `comments` | string[] | Author notes; usually `[""]` |

## Distributions (from `vibes_cards.json`)

### Sets
| Code | Name | Cards |
|---|---|---|
| Eth  | Enter the Huddle    | 202 |
| Lotl | Legends of the Lils | 151 |
| —    | **Total**           | **353** |

### Types
| Type | Count | Role |
|---|---|---|
| Penguin       | 209 | Battlefield permanent. Has vibe. Plays to **Huddle**. |
| Action        | 103 | One-shot effect. Plays from hand, resolves, goes to **Ice**. |
| Relic         | 25  | Battlefield permanent (non-Penguin). Plays to **Huddle**. |
| Rod           | 12  | Special: only playable face-down as a Rod; flips up with effect (e.g. *Not a Rod Anymore!*). |
| Penguin(ish)  | 1   | Variant Penguin. |
| ???           | 2   | Unknown — likely tokens. |
| Fishsicle     | 1   | Token. *"A Fishsicle produces one F, then goes away."* Not deckable. |
| **BasicRod**  | — listed under type `Rod` | Token-like default rod. |

### Colors
58 each of `Red`, `Yellow`, `Green`, `Blue`, `Purple` + 53 `Colorless` + 10 dual-color cards (2 each of every adjacent pair).

### Rarities
Common 158, Uncommon 94, Rare 79, Mythic 20, "" (tokens) 2.

## Image source

**Local PNGs** (recommended for `/docs/images/`):
`C:/Users/Redux/Downloads/vibes tcg simulator/disabled_mods/VibesCardShopMod_DISABLED/images/<id>.png` — 329 files. Filenames exactly match card `id`. 24 cards (353 − 329) have no local image; will need to either:
- Pull from the live S3 mirror: `https://ocg-card-catalog.s3.us-west-2.amazonaws.com/Spoiler_Previews/<id>.png`
- Or list as missing during build.

The S3 mirror is what `vibes.game` itself uses (seen in `C:/Users/Redux/vibes-tcg/public/cards.json`).

## Game rules (from user, not in data)

| Rule | Value |
|---|---|
| Deck size | exactly **52** |
| Max copies per card | **4** |
| Starting hand | **5** |
| Mulligan | up to 5 cards → bottom of deck, **no shuffle**, redraw to 5 |
| Per-cycle draw | (winner of vibe check rods top of deck, loser draws top of deck) — **not** a fixed per-turn draw |
| Win condition | At start of a cycle, hold Baron's Favor AND have ≥15 permanents in play (Rods + Huddle combined) |

## Zones (from user screenshot)

| Zone | Visibility | Role |
|---|---|---|
| **Deck** | Hidden (face-down stack) | Library of 52 cards |
| **Hand** | Private | Drawn cards |
| **Huddle** | Public | Battlefield for Penguins / Relics |
| **Rods** | Face-down, public (count visible) | Mana pile. Any card may be played here face-down to be a Rod. |
| **Ice** | Public | Graveyard — iced Penguins, resolved Actions, etc. |
| **Baron's Favor** | Shared (between players) | Token indicating who won last cycle's vibe check |

Cost model:
- **Fish cost** (cards with `cost.color = "Fish"`) is paid by *flopping* Rods.
- **Colored cost** (cards with `cost.color` = Red/Yellow/Green/Blue/Purple) is paid by *flopping* Penguins whose `pudge.color` matches.
- Flop = tap. "Unfloppening" = untap at start of each cycle.

## Field name mapping cheatsheet (Vibes → MTG-ish vocab)

| Vibes | MTG analogue |
|---|---|
| Huddle | Battlefield |
| Ice | Graveyard / exile |
| Rod | Land (face-down, any card) |
| Flop / Unflop | Tap / Untap |
| Cycle | Turn |
| Vibe | Power |
| Pudge | Colored mana symbol |
| Fish | Generic mana |
| Baron's Favor | Priority/initiative token (with win-condition trigger) |
