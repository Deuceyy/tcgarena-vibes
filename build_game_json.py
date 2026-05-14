"""Build the Vibes-Game.json + CardList + Decks for TCG Arena from /sets/*.json.

Idempotent. Drop a new set file into /sets and rerun.

Usage:
    python build_game_json.py
"""
import json
import os
import shutil
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SETS_DIR = ROOT / "sets"
SETS_PRIVATE_DIR = ROOT / "sets-private"  # gitignored — for unreleased sets
DOCS_DIR = ROOT / "docs"
DIST_DIR = ROOT / "dist"
IMAGES_DIR = DOCS_DIR / "images"
TOKENS_DIR = DOCS_DIR / "tokens"

# Source images shipped in the Vibes Card Shop mod
LOCAL_IMAGE_SRC = Path(
    r"C:\Users\Redux\Downloads\vibes tcg simulator\disabled_mods"
    r"\VibesCardShopMod_DISABLED\images"
)
# Fallback CDN used by vibes.game itself
S3_MIRROR = "https://ocg-card-catalog.s3.us-west-2.amazonaws.com/Spoiler_Previews/{id}.png"

# Public GitHub Pages base URL (set via env or edit here after creating the repo)
BASE_URL = os.environ.get("VIBES_BASE_URL", "https://deuceyy.github.io/tcgarena-vibes")

# Set code -> display name
SET_NAMES = {
    "Eth":  "Enter the Huddle",
    "Lotl": "Legends of the Lils",
    "Birb": "Birb and Pengu",
}

# Cards that exist in data but are tokens (don't count toward 52-deck or 15-permanent)
TOKEN_TYPES = {"Fishsicle"}

# Card types that go to which TCG Arena section when auto-played from hand
AUTOPLAY_FROM_HAND = {
    "Penguin":      "Huddle",
    "Penguin(ish)": "Huddle",
    "Relic":        "Huddle",
    "Action":       "Stack",
    "Rod":          "Stack",
    "???":          "Stack",
}


def load_sets() -> list[dict]:
    cards = []
    files = sorted(SETS_DIR.glob("*.json"))
    if SETS_PRIVATE_DIR.exists():
        priv = sorted(SETS_PRIVATE_DIR.glob("*.json"))
        if priv:
            print(f"  including {len(priv)} private set file(s) from sets-private/ (gitignored)")
            files += priv
    for path in files:
        with path.open(encoding="utf-8") as f:
            cards.extend(json.load(f))
    print(f"  loaded {len(cards)} cards from {len(files)} set file(s)")
    return cards


def assemble_images(cards: list[dict]) -> tuple[list[str], list[str]]:
    """Copy local PNGs into docs/images/, fetch any missing from S3.

    Returns (copied_ids, fetched_ids, missing_ids).
    """
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    copied, fetched, missing = [], [], []

    for card in cards:
        cid = card["id"]
        dest = IMAGES_DIR / f"{cid}.png"
        if dest.exists():
            continue  # idempotent
        local = LOCAL_IMAGE_SRC / f"{cid}.png"
        if local.exists():
            shutil.copy2(local, dest)
            copied.append(cid)
            continue
        url = S3_MIRROR.format(id=cid)
        try:
            with urllib.request.urlopen(url, timeout=20) as resp:
                if resp.status == 200:
                    dest.write_bytes(resp.read())
                    fetched.append(cid)
                    continue
        except Exception:
            pass
        missing.append(cid)

    print(f"  images: copied={len(copied)} fetched_from_s3={len(fetched)} missing={len(missing)}")
    if missing:
        print(f"  missing image ids (will use card-back fallback): {missing}")
    return copied, fetched, missing


def ensure_baron_token():
    """Place a placeholder Baron token image. User can swap later."""
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    dest = TOKENS_DIR / "baron-token.png"
    if dest.exists():
        return
    placeholder = Path(
        r"C:\Users\Redux\Downloads\vibes tcg simulator\VibesCardShopMod\branding\VibesLogoSmall.png"
    )
    if placeholder.exists():
        shutil.copy2(placeholder, dest)
        print(f"  baron-token.png placeholder copied (swap with a real Baron icon later)")


def transform_card(card: dict) -> dict:
    cid = card["id"]
    name = card["name"]
    ctype = card["type"]
    is_token = ctype in TOKEN_TYPES

    cost_obj = card.get("cost") or {}
    cost_amount = cost_obj.get("amount") if isinstance(cost_obj, dict) else None
    cost_color = cost_obj.get("color") if isinstance(cost_obj, dict) else None

    pudge_obj = card.get("pudge") or {}
    pudge_amount = pudge_obj.get("amount") if isinstance(pudge_obj, dict) else None
    pudge_color = pudge_obj.get("color") if isinstance(pudge_obj, dict) else None

    # Split dual-color like "Blue, Red" into list
    colors_raw = card.get("color", "")
    colors = [c.strip() for c in colors_raw.split(",")] if colors_raw else []

    # Render | line-breaks; leave _R_/_F_/_T_ symbols intact (TCG Arena tooltip displays them)
    rules_text = (card.get("cardText") or "").replace("|", "\n").rstrip()

    image_url = f"{BASE_URL}/images/{cid}.png"

    return {
        "id": cid,
        "isToken": is_token,
        "face": {
            "front": {
                "name": name,
                "type": ctype,
                "cost": cost_amount if cost_amount is not None else 0,
                "image": {"en": image_url},
                "isHorizontal": False,
            }
        },
        "name": name,
        "type": ctype,
        "cost": cost_amount if cost_amount is not None else 0,
        "costColor": cost_color or "",
        "color": colors,
        "rarity": card.get("rarity", ""),
        "set": SET_NAMES.get(card.get("set", ""), card.get("set", "")),
        "vibe": card.get("vibe"),
        "pudgeAmount": pudge_amount,
        "pudgeColor": pudge_color,
        "rulesText": rules_text,
        "_legal": {"VIBES": True},
    }


def build_game_json() -> dict:
    """Build the top-level Vibes-Game.json structure."""
    return {
        "name": "Vibes TCG",
        "menuBackgroundImage": f"{BASE_URL}/vibes-logo.png",
        "defaultRessources": {
            "backgrounds": [],
            "decksUrl": f"{BASE_URL}/Vibes-Decks.json",
        },
        "customHelp": (
            "VIBES TCG QUICK REFERENCE\n"
            "(1) PLAY-AS-ROD: any card in hand may be played face-down to your Rods section to "
            "become a Rod (mana). Drag any hand card to Rods and flip it face-down.\n"
            "(2) FISH COST: flop (tap) Rods to pay cost.color = 'Fish'. Right-click a Rod -> tap.\n"
            "(3) PUDGE COST: flop a Penguin in the Huddle whose pudge.color matches to pay colored "
            "cost. The Penguin produces its pudge for the rest of the cycle.\n"
            "(4) NEW CYCLE: all flopped (tapped) cards in Rods + Huddle auto-unflop. Both players "
            "share the cycle (sharedTurn).\n"
            "(5) VIBE CHECK: at the end of each cycle, compare highest-vibe Penguin between "
            "players. Winner gets the Baron's Favor token. Winner then manually moves top of "
            "their deck to Rods; loser manually draws top card to Hand.\n"
            "(6) WIN: at the START of a cycle, if you hold the Baron's Favor AND have 15+ "
            "permanents in play (Rods + Huddle, tokens excluded), you win.\n"
            "(7) BARON TOKEN: drag the Baron's Favor token between players to track who holds it."
        ),
        "cardRotation": "90",
        "cards": {
            "dataUrl": f"{BASE_URL}/Vibes-CardList.json",
            "cardBack": f"{BASE_URL}/tokens/card-back.png",
            "cardBackColor": "#1a3a5c",
        },
        "deckBuilding": {
            "mainFilters": ["type", "color", "cost", "rarity", "set", "name"],
            "formats": [
                {
                    "title": "Standard",
                    "gameplay": "Classic",
                    "customCategories": [],
                    "deckRuleset": "Standard",
                    "legalityCode": "VIBES",
                }
            ],
            "deckRulesets": {
                "Standard": {
                    "reversedLegality": False,
                    "general": {"min": 52, "max": 52, "maxPerCard": 4},
                    "categories": [],
                }
            },
        },
        "gameplay": {
            "Classic": build_gameplay_mode(),
        },
    }


def build_gameplay_mode() -> dict:
    return {
        "beforeGameStart": {
            "boardCategoriesInSideboard": [],
            "boardCardSelection": [],
            "chooseAnotherStartingPlayer": True,
            "initialBoardSetup": {"0": [], "1": []},
        },
        "mulligan": {
            "triggeredByButton": True,
            "startingHandSize": 5,
            "mulliganCount": {"min": 0, "max": 1},
            "mulliganCycle": {
                "info": "Pick any cards to send to the bottom of your deck (no shuffle). You will redraw up to 5.",
                "steps": ["toBottom", "draw"],
                "selectionRange": {"min": 0, "max": 5},
                "keepCardsOrder": True,
            },
        },
        "newTurn": {
            "drawOnStart": False,
            "sharedTurn": True,
            "firstPlayerTokenName": "",
            "drawPerTurn": "0",
        },
        "defaultNotes": "Track permanents (Rods + Huddle) and vibe totals here.",
        "tokens": [],
        "countersStartingValues": [0],
        "hideFacedDownCards": True,
        "draggableTokens": [
            {
                "id": "vibe-counter",
                "name": "Vibe Counter",
                "image": f"{BASE_URL}/tokens/vibe-counter.png",
            },
        ],
        "sections": {
            "layout": {
                "direction": "column",
                "isSymetricalForOpponents": True,
                "content": [
                    {
                        "direction": "row",
                        "style": False,
                        "content": [
                            {"section": "Huddle", "style": {"flex": "1"}},
                        ],
                        "isSymetricalForOpponents": True,
                    },
                    {
                        "direction": "row",
                        "style": False,
                        "content": [
                            {"section": "Deck",  "style": {"width": "12vh"}},
                            {"section": "Rods",  "style": {"flex": "1"}},
                            {"section": "Baron", "style": {"width": "22vh", "background": "rgba(255, 180, 0, 0.35)", "border": "0.4vh solid rgba(255, 200, 60, 0.95)", "borderRadius": "1vh", "boxShadow": "0 0 2vh rgba(255, 180, 0, 0.6)"}},
                            {"section": "Ice",   "style": {"width": "16vh"}},
                        ],
                        "isSymetricalForOpponents": True,
                    },
                ],
            },
            "categoriesAlreadyOnBoard": [],
            "autoPlayFromHand": AUTOPLAY_FROM_HAND,
            "autoPlayFromStack": {
                "Action": "Ice",
                "Rod":    "Ice",
                "???":    "Ice",
            },
            "sectionsDict": {
                "Huddle": {
                    "isHidden": "no",
                    "height": "16",
                    "alignment": "CENTER",
                    "opponentAlignment": False,
                    "noAutoPayTo": False,
                    "isHorizontalAllowed": True,
                    "displayedTitle": "Huddle",
                    "noQuickActions": False,
                    "enterTapped": False,
                    "enterSpun": False,
                    "isGroupForbidden": False,
                    "keepTappedNewTurn": False,
                    "showHiddenCardInHistory": False,
                },
                "Rods": {
                    "isHidden": "opponent-only",
                    "height": "12",
                    "alignment": "CENTER",
                    "opponentAlignment": False,
                    "noAutoPayTo": False,
                    "isHorizontalAllowed": True,
                    "displayedTitle": "Rods",
                    "noQuickActions": False,
                    "enterTapped": False,
                    "enterSpun": False,
                    "isGroupForbidden": False,
                    "keepTappedNewTurn": False,
                    "showHiddenCardInHistory": False,
                    "cardBackColor": "#1a3a5c",
                },
                "Ice": {
                    "isHidden": "no",
                    "height": "SMALL",
                    "alignment": "DECK",
                    "opponentAlignment": False,
                    "noAutoPayTo": True,
                    "isHorizontalAllowed": False,
                    "displayedTitle": "Ice",
                    "noQuickActions": False,
                    "enterTapped": False,
                    "enterSpun": False,
                    "isGroupForbidden": False,
                    "keepTappedNewTurn": False,
                    "showHiddenCardInHistory": False,
                },
                "Baron": {
                    "isHidden": "no",
                    "height": "MEDIUM",
                    "alignment": "CENTER",
                    "opponentAlignment": False,
                    "noAutoPayTo": True,
                    "isHorizontalAllowed": True,
                    "displayedTitle": "Baron's Favor",
                    "noQuickActions": False,
                    "enterTapped": False,
                    "enterSpun": False,
                    "isGroupForbidden": True,
                    "keepTappedNewTurn": False,
                    "showHiddenCardInHistory": False,
                },
                "Stack": {
                    "isDefaultSection": True,
                    "isHidden": "no",
                    "height": "HUGE",
                    "alignment": "NONE",
                    "isHorizontalAllowed": False,
                    "isGroupForbidden": True,
                    "displayedTitle": "Resolving",
                    "opponentAlignment": False,
                    "noAutoPayTo": True,
                    "noQuickActions": False,
                    "enterTapped": False,
                    "enterSpun": False,
                    "keepTappedNewTurn": False,
                    "showHiddenCardInHistory": False,
                },
            },
        },
    }


def main():
    print("== Vibes-Game.json build ==")
    SETS_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)
    DIST_DIR.mkdir(exist_ok=True)

    print("\n[1/4] loading sets")
    cards = load_sets()
    by_id = {}
    dupes = []
    for c in cards:
        if c["id"] in by_id:
            dupes.append(c["id"])
        by_id[c["id"]] = c
    if dupes:
        print(f"  WARN: duplicate ids dropped (kept last): {dupes}")
    cards = list(by_id.values())

    print("\n[2/4] assembling images")
    assemble_images(cards)
    ensure_baron_token()

    print("\n[3/4] transforming card data")
    cardlist = {c["id"]: transform_card(c) for c in cards}

    # Inject the synthetic Baron's Favor token. Not part of any set, never in
    # a deck — spawned via right-click -> Create Tokens, then dragged into the
    # Baron section of whichever player wins the cycle's vibe check.
    cardlist["BaronFavor"] = {
        "id": "BaronFavor",
        "isToken": True,
        "face": {
            "front": {
                "name": "Baron's Favor",
                "type": "Token",
                "cost": 0,
                "image": {"en": f"{BASE_URL}/tokens/baron-token.png"},
                "isHorizontal": False,
            }
        },
        "name": "Baron's Favor",
        "type": "Token",
        "cost": 0,
        "costColor": "",
        "color": [],
        "rarity": "",
        "set": "Tokens",
        "vibe": None,
        "pudgeAmount": None,
        "pudgeColor": None,
        "rulesText": "Indicates which player currently holds the Baron's Favor. Does not count toward the 15-permanent win condition.",
        "_legal": {"VIBES": False},
    }

    token_count = sum(1 for c in cardlist.values() if c["isToken"])
    deckable = len(cardlist) - token_count
    print(f"  cards: {len(cardlist)} ({deckable} deckable + {token_count} tokens)")

    print("\n[4/4] writing output files")
    game = build_game_json()
    (DOCS_DIR / "Vibes-Game.json").write_text(json.dumps(game, indent=2), encoding="utf-8")
    (DOCS_DIR / "Vibes-CardList.json").write_text(json.dumps(cardlist, indent=2), encoding="utf-8")
    if not (DOCS_DIR / "Vibes-Decks.json").exists():
        (DOCS_DIR / "Vibes-Decks.json").write_text("[]", encoding="utf-8")
    # Mirror the main game file to /dist for local inspection
    shutil.copy2(DOCS_DIR / "Vibes-Game.json", DIST_DIR / "Vibes-Game.json")

    print(f"\nDone. Hosted URL once published: {BASE_URL}/Vibes-Game.json")


if __name__ == "__main__":
    main()
