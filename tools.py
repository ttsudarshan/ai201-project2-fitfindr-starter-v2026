"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings

# Words that say nothing about the item. Dropped from the description before
# scoring, so "looking for a tee" scores on "tee" alone.
_STOP_WORDS = {
    "a", "an", "and", "any", "for", "i", "im", "in", "is", "it", "looking",
    "me", "my", "need", "of", "on", "or", "some", "something", "the", "to",
    "want", "with", "find", "dollars", "dollar", "size", "please",
}

# Listings whose size says this fit any size the user asks for.
_ONE_SIZE = "one size"


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    keywords = _keywords(description or "")
    if not keywords:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not size_matches(size, listing["size"]):
            continue
        score = _score(listing, keywords)
        if score > 0:
            scored.append((score, listing))

    # Best score first; the cheaper listing wins a tie.
    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


def size_matches(wanted: str, listing_size: str) -> bool:
    """
    True if the size the user asked for fits a listing's size string.

    The listing's size is split on "/", spaces and parentheses, and the wanted
    size has to equal one piece exactly, ignoring case. So "M" matches "S/M"
    and "M/L" but not "XL"; "8" matches "US 8" but not "US 8.5"; "W30" matches
    "W30 L30". "One Size" listings match anything.
    """
    listing_size = listing_size.lower()
    if _ONE_SIZE in listing_size:
        return True
    pieces = [p for p in re.split(r"[/\s()]+", listing_size) if p]
    return wanted.strip().lower() in pieces


def _words(text: str) -> list[str]:
    """Lowercase words, with a trailing "s" dropped so plurals match."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]


def _keywords(description: str) -> list[str]:
    return [w for w in _words(description) if w not in _STOP_WORDS]


def _score(listing: dict, keywords: list[str]) -> int:
    """3 per keyword in the title, 2 in tags/category, 1 anywhere else."""
    title = set(_words(listing["title"]))
    tagged = set(_words(" ".join(listing["style_tags"]) + " " + listing["category"]))
    other = set(_words(" ".join([
        listing["description"],
        " ".join(listing["colors"]),
        listing.get("brand") or "",
    ])))

    score = 0
    for word in keywords:
        if word in title:
            score += 3
        elif word in tagged:
            score += 2
        elif word in other:
            score += 1
    return score


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    items = (wardrobe or {}).get("items") or []
    system = (
        "You are a thrift-savvy stylist. Be concrete and brief. Plain text, "
        "no markdown headings."
    )

    if not items:
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n"
            f"{_describe_item(new_item)}\n\n"
            "They haven't told you anything about their wardrobe. Suggest two "
            "outfits built around this item using common everyday pieces "
            "(for example plain tees, jeans, sneakers). Start with "
            "'General ideas:'. For each outfit, one line listing the pieces "
            "and one short line on why it works."
        )
    else:
        owned = "\n".join(
            f"- {item['name']} ({item['category']}; colors: "
            f"{', '.join(item.get('colors') or [])}; "
            f"style: {', '.join(item.get('style_tags') or [])})"
            for item in items
        )
        prompt = (
            f"Someone is thinking about buying this thrifted item:\n"
            f"{_describe_item(new_item)}\n\n"
            f"Here is what they already own:\n{owned}\n\n"
            "Suggest two outfits built around the new item. Each outfit must "
            "use at least two pieces from their wardrobe, named exactly as "
            "written above. For each outfit, one line listing the pieces and "
            "one short line on why it works."
        )

    response = generate(prompt, system=system).strip()
    if response:
        return response
    # The model answered with nothing. Still return something usable.
    return (
        f"Pair this {new_item['category']} with simple basics that match its "
        f"{', '.join(new_item.get('style_tags') or ['casual'])} feel."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return (
            f"Can't write a fit card: no outfit suggestion was given for "
            f"{new_item.get('title', 'this item')}."
        )

    price = f"${new_item['price']:.0f}"
    system = (
        "You write short, casual social media captions about thrift finds. "
        "Sound like a real person, not a product listing."
    )
    prompt = (
        f"Write a caption for a post about this thrift find:\n"
        f"{_describe_item(new_item)}\n\n"
        f"How it's being styled:\n{outfit.strip()}\n\n"
        "Rules:\n"
        "- 2 to 4 sentences, under 400 characters in total.\n"
        f"- Mention the item, the price written exactly as {price}, and the "
        f"platform {new_item['platform']} — each once.\n"
        "- Be specific about the vibe and pick one detail from the styling.\n"
        "- End with at most 3 hashtags.\n"
        "- Output only the caption."
    )
    return generate(prompt, system=system).strip()


def _describe_item(item: dict) -> str:
    """The listing as prompt text. Leaves brand out when there isn't one."""
    lines = [
        f"Title: {item['title']}",
        f"Description: {item['description']}",
        f"Category: {item['category']}",
        f"Style: {', '.join(item.get('style_tags') or [])}",
        f"Colors: {', '.join(item.get('colors') or [])}",
        f"Size: {item['size']}",
        f"Condition: {item['condition']}",
        f"Price: ${item['price']:.0f}",
        f"Platform: {item['platform']}",
    ]
    if item.get("brand"):
        lines.insert(1, f"Brand: {item['brand']}")
    return "\n".join(lines)
