# TCG Arena Custom Game JSON — Reverse-Engineered Schema

Source: [Riftbound-Game.json](reference/Riftbound-Game.json) (1012 lines), [Riftbound-CardList.json](reference/Riftbound-CardList.json) (986 cards), [Riftbound-Decks.json](reference/Riftbound-Decks.json).

Loaded by tcg-arena.fr via `https://tcg-arena.fr/load/<base64(url-to-Game.json)>`.

## Top-level keys of `<Game>.json`

| Key | Type | Required | Purpose |
|---|---|---|---|
| `name` | string | yes | Display name in Games tab |
| `menuBackgroundImage` | URL | no | Banner in game menu |
| `defaultRessources` | object | yes | Backgrounds + decksUrl (see below) |
| `customHelp` | string | no | In-game help text (supports `\n`) |
| `cardRotation` | string `"0"`/`"90"` | no | Default orientation of card art |
| `cards` | object | yes | Card data location + card backs (see below) |
| `translationsUrl` | URL | no | Multi-language pack |
| `deckBuilding` | object | yes | Filters + formats + deck rulesets |
| `gameplay` | object | yes | One key per mode (e.g. `Classic`, `Multiplayer`) |

### `defaultRessources`
```json
{
  "backgrounds": ["url1.png", "url2.png", ...],   // playmat options
  "decksUrl": "https://.../Game-Decks.json"        // optional preset decks
}
```

### `cards`
```json
{
  "dataUrl": "https://.../Game-CardList.json",
  "cardBack": "https://.../cardBack-default.png",
  "cardBackColor": "#03354a",
  "extraCardBacks": {                              // override per category
    "Runes": "url.png",
    "Battlefields": "url.png"
  }
}
```

### Card object (in `dataUrl` file)
The CardList is a **dict keyed by card id** (not a list). Each card:
```json
{
  "id": "OGN-001",
  "isToken": false,
  "face": {
    "front": {
      "name": "Blazing Scorcher",
      "type": "Unit",
      "cost": 5,
      "image": { "en": "url", "zh": "url" },     // per-language URLs
      "isHorizontal": false
    }
    // "back": { ... } for double-faced cards
  },
  "name": "...", "type": "...", "cost": ...,     // top-level copies for filtering
  "Domain": ["Fury"],                             // arbitrary faceted fields, must match `mainFilters` + `categories`
  "Set": ["01 - Origins"],
  "_legal": { "S02": true, "S03": true }         // gates which formats this card is legal in
}
```

**Important:** the `type` field doubles as the *deck-building category* and the *auto-routing destination* (via `autoPlayFromHand`). So if a card has `type: "Runes"` it lands in the Runes section automatically when dragged from hand.

### `deckBuilding`
```json
{
  "mainFilters": ["type","cost","name","Domain","Set"],   // sidebar filters
  "formats": [
    {
      "title": "Classic",
      "gameplay": "Classic",                               // points at gameplay.<key>
      "customCategories": ["Chosen_Champion"],
      "deckRuleset": "Standard",
      "legalityCode": "S02"                                // matches card._legal[code]
    }
  ],
  "deckRulesets": {
    "Standard": {
      "reversedLegality": true,
      "general": { "min": 56, "max": 56, "maxPerCard": 3 },
      "categories": [
        { "category": "Legend",        "min": 1,  "max": 1,  "maxPerCard": 1 },
        { "category": "Battlefields",  "min": 3,  "max": 3,  "maxPerCard": 1 },
        { "category": "Runes",         "min": 12, "max": 12, "maxPerCard": 12 },
        { "category": "Sideboard",     "min": 0,  "max": 8 }
      ]
    }
  }
}
```

### `gameplay.<mode>` (e.g. `Classic`)
```json
{
  "beforeGameStart": {
    "boardCategoriesInSideboard": ["..."],
    "boardCardSelection": [ { "category": "Battlefields", "min": 1, "max": 1, "unselectedDestination": "ExileHidden" } ],
    "chooseAnotherStartingPlayer": true,
    "initialBoardSetup": {
      "0": [                                          // 1st player actions
        { "drawFromTop": "Runes", "count": 2, "destination": "Mana" },
        { "drawFromTop": "Deck",  "count": 1, "destination": "Hand" }
      ],
      "1": [                                          // 2nd player actions
        { "drawFromTop": "Runes", "count": 1, "destination": "Mana", "waitForPlayerTurn": true }
      ]
    }
  },
  "mulligan": {
    "triggeredByButton": true,
    "startingHandSize": 4,
    "mulliganCount": { "min": 0, "max": 1 },          // # of mulligan rounds allowed
    "mulliganCycle": {
      "info": "Helper text shown in dialog",
      "steps": ["toBottom", "draw"],                  // also: "toTop", "shuffle"
      "selectionRange": { "min": 0, "max": 2 },
      "keepCardOrder": false                          // true = no shuffle after toBottom
    }
  },
  "newTurn": {
    "drawOnStart": false,
    "sharedTurn": false,
    "firstPlayerTokenName": "",
    "drawPerTurn": "1"
  },
  "defaultNotes": "",
  "tokens": [],
  "countersStartingValues": [0],
  "hideFacedDownCards": false,
  "draggableTokens": [
    { "id": "stun-token", "name": "Stun", "image": "url.png" }
  ],
  "sections": {
    "layout": { ... },                                // visual flex layout, see below
    "categoriesAlreadyOnBoard": ["Runes","Battlefields","Legend"],   // categories that start on-table not in deck
    "autoPlayFromHand": { "Runes": "Mana", "Spell": "Stack" },       // card.type → destination section
    "autoPlayFromStack": { "Spell": "Discard" },                     // when card leaves Stack
    "sectionsDict": { ... }                            // per-section behavior config
  }
}
```

### `sections.layout` — flex-style board layout

Recursive `{direction: row|column, style: {...}|false, content: [...]}` tree. Leaves are `{section: "<name>", style: {...}}`. CSS-like styles using vh units. Top-level layout describes one player's half; the opponent gets a mirrored copy unless `isSymetricalForOpponents: false`.

Riftbound has a 2-row layout:
1. Row 1 (battlefields): 3 columns, each a `Battlefields` thumbnail above its `B1`/`B2`/`B3` units zone.
2. Row 2 (resources/leader): `Runes` (hidden deck) | `Mana` | `Base` | `Legend` | `Chosen_Champion`.

`optional.key` on a column lets a section group be toggled on/off (Riftbound uses it for "Baron Pit").

### `sections.sectionsDict.<name>` — per-section config

| Key | Values | Meaning |
|---|---|---|
| `isHidden` | `"yes"`/`"no"` | Cards face-down to opponent |
| `height` | `"SMALL"` / `"HUGE"` / number (vh) | Visual height |
| `alignment` | `"DECK"` / `"CENTER"` / `"NONE"` | Stack as deck, splay, or free |
| `displayedTitle` | string | Label on the zone |
| `enterTapped` | bool | New cards enter rotated 90° |
| `enterSpun` | bool | New cards enter rotated 180° |
| `keepTappedNewTurn` | bool | Don't auto-untap at turn start |
| `isHorizontalAllowed` | bool | Cards may be placed horizontally |
| `noQuickActions` | bool | Disable right-click menu |
| `noAutoPayTo` | bool | Excludes from "auto-pay" cost mechanic |
| `drawPerTurn` | number | Auto-draw N from this section each turn |
| `cardBackColor` | hex | Override card back color for this section |
| `cardActionShortcut` | object | One-click action button (e.g. recycle) |
| `reverseZOrder` | bool | Newer cards render below older |
| `isDefaultSection` | bool | Where untyped cards land (usually Stack) |
| `isGroupForbidden` | bool | Disallow grouping/stacking |
| `opponentAlignment` | bool/string | Override layout on opponent side |

### Implicit / built-in section names
TCG Arena provides these without declaration: `Hand`, `Deck`, `Discard`, `Exile`, `ExileHidden`, `Mana` (often custom though), `Stack`.

### Deck JSON format (in `defaultRessources.decksUrl`)
List of:
```json
{
  "title": "Jinx Trial Deck",
  "id": "<uuid>",
  "game": "Riftbound",
  "format": ["Classic", "Multiplayer"],
  "cardCount": 56,
  "createdAt": "ISO-8601",
  "lastModifiedAt": "ISO-8601",
  "deckList": {
    "categoriesOrder": ["Chosen_Champion","Unit","Legend","Runes","Battlefields","Gear","Spell"],
    "Unit": [ { "count": 3, "id": "OGN-001" }, ... ],
    "Legend": [ ... ],
    "Sideboard": []
  }
}
```

## Mental model summary

1. The Game JSON declares **categories** (= card types) and **sections** (= board zones).
2. Cards have a `type` matching a category; that drives both deck-building rules AND auto-routing to a section.
3. The board is a recursive flex layout of named sections.
4. `gameplay.<mode>` defines start-of-game, mulligan, per-turn rules.
5. Card art / data lives in a separate `dataUrl` JSON keyed by card id.
6. Decks live in another JSON, referenced by `categoriesOrder` and per-category `[{count, id}]` lists.

## Loading mechanism
`https://tcg-arena.fr/load/<base64(url-to-Game.json)>` — a one-shot link that adds the game to the user's Games tab. URL must be publicly fetchable (HTTPS, CORS-friendly — GitHub Pages works).
