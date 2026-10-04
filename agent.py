"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable
from utils.data_loader import load_listings


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
        "searched": False,           # True once search_listings has run, even if it found nothing
        "tool_calls": [],            # each tool call, in order: {"tool": name, "inputs": {...}}
    }


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE = re.compile(
    r"(?:under|below|less than|max(?:imum)?|up to|<)\s*\$?\s*(\d+(?:\.\d+)?)"
    r"(?:\s*(?:dollars?|bucks))?",
    re.IGNORECASE,
)
_SIZE = re.compile(r"(?:\bin\s+)?\bsize\s+([a-z0-9][a-z0-9./]*)", re.IGNORECASE)
_FILLER = re.compile(
    r"\b(?:i'?m|i am|looking for|i want|i need|find me|show me|can you find|please)\b",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size and a max_price out of plain language, by regex.

        "vintage graphic tee under $30, size M"
        → {"description": "vintage graphic tee", "size": "M", "max_price": 30.0}

    size and max_price are None when the query doesn't give them.
    """
    max_price = None
    price_match = _PRICE.search(query)
    if price_match:
        max_price = float(price_match.group(1))
        query = query[: price_match.start()] + " " + query[price_match.end():]

    size = None
    size_match = _SIZE.search(query)
    if size_match:
        size = size_match.group(1).upper()
        query = query[: size_match.start()] + " " + query[size_match.end():]

    description = _FILLER.sub(" ", query)
    description = re.sub(r"[,;]+", " ", description)
    description = re.sub(r"\s+", " ", description).strip()
    return {"description": description, "size": size, "max_price": max_price}


def _what_to_change(parsed: dict) -> str:
    """
    The message for an empty search. Says which filter to loosen, by checking
    whether the search would find anything without it.
    """
    desc, size, price = parsed["description"], parsed["size"], parsed["max_price"]

    asked = f"'{desc}'" if desc else "your search"
    if size:
        asked += f" in size {size}"
    if price is not None:
        asked += f" under ${price:.0f}"
    message = f"Nothing matched {asked}."

    if not desc:
        return message + " Add a few words about the item, like 'denim jacket' or 'graphic tee'."

    tips = []
    if size and search_listings(desc, None, price):
        tips.append(f"drop the size {size} filter — there are matches in other sizes")
    if price is not None and search_listings(desc, size, None):
        tips.append(f"raise your price above ${price:.0f} — there are matches that cost more")
    if size and price is not None and not tips and search_listings(desc, None, None):
        tips.append("drop both the size and the price limit — there are matches without them")
    if not tips:
        tips.append(
            f"describe the item differently, since no listing mentions '{desc}' "
            "(a type of clothing like tee, jeans, jacket, dress or sneakers, "
            "or a style like vintage, y2k, 90s or grunge)"
        )
        cheapest = min(listing["price"] for listing in load_listings())
        if price is not None and price < cheapest:
            tips.append(f"raise your price: the cheapest listing is ${cheapest:.0f}")
    return message + " Try: " + "; and ".join(tips) + "."


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)

    # Each time round, look at what the session already holds and pick the one
    # step that's missing. The run ends when there's a fit card or an error.
    count = 0
    while session["fit_card"] is None and session["error"] is None:
        count += 1
        trace.check_iterations(count)

        if not session["parsed"]:
            session["parsed"] = parse_query(session["query"])

        elif not session["searched"]:
            parsed = session["parsed"]
            session["tool_calls"].append({"tool": "search_listings", "inputs": dict(parsed)})
            session["search_results"] = search_listings(
                parsed["description"], parsed["size"], parsed["max_price"]
            )
            session["searched"] = True

            # THE BRANCH: nothing found → say what to change, and stop here.
            if not session["search_results"]:
                session["error"] = _what_to_change(parsed)

        elif session["selected_item"] is None:
            session["selected_item"] = session["search_results"][0]

        elif session["outfit_suggestion"] is None:
            item, owned = session["selected_item"], session["wardrobe"]
            session["tool_calls"].append(
                {"tool": "suggest_outfit", "inputs": {"new_item": item, "wardrobe": owned}}
            )
            session["outfit_suggestion"] = suggest_outfit(item, owned)

        else:
            outfit, item = session["outfit_suggestion"], session["selected_item"]
            session["tool_calls"].append(
                {"tool": "create_fit_card", "inputs": {"outfit": outfit, "new_item": item}}
            )
            session["fit_card"] = create_fit_card(outfit, item)

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
