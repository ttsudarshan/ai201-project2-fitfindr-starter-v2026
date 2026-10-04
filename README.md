# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

You type what you're thrifting for in plain language, like
`python app.py ask 'vintage graphic tee under $30, size M'`. FitFindr pulls the
description, size and price ceiling out of that, searches 40 listings from
Depop, thredUp and Poshmark, and picks the best match. It then suggests two
outfits that pair the find with pieces already in your wardrobe, and writes a
short caption you could post with it. If nothing matches, it stops before the
outfit step and tells you which part of your request to change: the size, the
price, or the words you used.


---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

Every listing in `data/listings.json` has these fields: `id`, `title`,
`description`, `category`, `style_tags` (list), `size`, `condition`, `price`
(float), `colors` (list), `brand` (str or None, and None for most of them), and
`platform`. A wardrobe is `{"items": [...]}`, where each item has `id`, `name`,
`category`, `colors`, `style_tags`, `notes`. An empty wardrobe is
`{"items": []}`.

### `search_listings`

- **What it does:** Filters the 40 listings by price and size, then ranks
  what's left by how many of the description's keywords appear in each listing.
- **Inputs:** `description` (str): keywords such as `"vintage graphic tee"`.
  `size` (str or None): a size such as `"M"`, `"8"` or `"W30"`, or None to skip
  the size filter. `max_price` (float or None): a price ceiling, inclusive, or
  None to skip the price filter.
- **Returns:** a `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10)
  whole listing dicts, each with all 11 fields above (`id`, `title`, `price`,
  `size`, `platform`, `brand`, and so on), best match first. Ties go to the
  cheaper listing.
  - **Size rule:** the listing's size string is split on `/`, spaces and
    parentheses, and the user's size has to equal one of those pieces, ignoring
    case. So `M` matches `S/M` and `M/L` but not `XL`. `8` matches `US 8` but
    not `US 8.5`, and `W30` matches `W30 L30`. A listing whose size says
    `One Size` matches any size.
  - **Scoring:** the description is lowercased, stop words like "a", "for" and
    "looking" are dropped, and a trailing "s" is stripped so "sneakers" matches
    "sneaker". Each remaining keyword scores 3 if it's in the title, 2 if it's
    in `style_tags` or `category`, and 1 if it's only in the `description`,
    `colors` or `brand`. Anything that scores 0 is dropped.
- **When it has nothing:** an empty list `[]`. It never returns None and never
  raises. An empty `description` also gives `[]`.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the new
  item, using pieces the user already owns.
- **Inputs:** `new_item` (dict): one listing dict, the one in
  `session["selected_item"]`. `wardrobe` (dict): `{"items": list[dict]}` with
  the wardrobe item fields above. The list may be empty.
- **Returns:** a non-empty `str`: two short outfits, each naming the new item
  and two or more wardrobe pieces by their `name`, with a line on why it works.
- **When it has nothing:** if `wardrobe["items"]` is empty (or missing), it
  asks the model for general styling advice instead: two outfits made of
  everyday pieces, labelled as general ideas. It doesn't raise and doesn't
  return `""`. If the model sends back blank text, it returns a fixed fallback
  sentence naming the item's category and style tags. If the model can't be
  reached, `generate.ModelUnavailable` is raised for the loop to deal with.

### `create_fit_card`

- **What it does:** Asks the model for a short caption someone would post
  about the find, worked out from the outfit suggestion.
- **Inputs:** `outfit` (str): the text from `suggest_outfit`, taken from
  `session["outfit_suggestion"]`. `new_item` (dict): the same listing dict,
  taken from `session["selected_item"]`.
- **Returns:** a `str` caption of 2 to 4 sentences and under 400 characters.
  It names the item, says its price as `$NN` and its platform once each, and
  ends with up to 3 hashtags. It's written as the person who bought the item,
  not a seller. If the listing has no brand, the brand isn't mentioned.
- **When it has nothing:** if `outfit` is empty or only whitespace, it returns
  `"Can't write a fit card: no outfit suggestion was given for <title>."`
  without calling the model. The loop never calls it that way, because it
  stops before this step when the search is empty.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` saying which filter to change, and stop: `suggest_outfit`
and `create_fit_card` are never called and `session["fit_card"]` stays `None`.
Otherwise take the first (best-scoring) result as `session["selected_item"]`
and go on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** with regex, in `agent.py::parse_query`, without a
model call. `max_price` comes from `under $30`, `below 30`, `less than $30`,
`max $30`, `up to $30` or `<$30`. `size` comes from `size M` or `in size 8`.
Whatever is left, with filler words removed, is the `description`.

**What moves through the session:** `query`, then `parsed`
(`description`/`size`/`max_price`), then `search_results`, then
`selected_item`, then `outfit_suggestion`, then `fit_card`. Each tool reads
its inputs from the session, not from the previous call's return value.
`session["tool_calls"]` records each tool's name and the exact arguments it was
called with, so it's possible to check that the item `suggest_outfit` received
is the same one in `selected_item`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query** (happy path, example wardrobe)

```
$ python app.py ask 'vintage graphic tee under $30, size M'


  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1: Y2K Butterfly Tee, Baggy straight-leg jeans, Chunky white sneakers
Why it works: Balances the fitted crop top with loose denim for an authentic 2000s streetwear silhouette.

Outfit 2: Y2K Butterfly Tee, Wide-leg khaki trousers, Brown leather belt
Why it works: Anchors the pastel graphic tee with earthy neutrals for a grounded, everyday look.

  Fit card: Scored this adorable Y2K butterfly tee on depop for just $18! Obsessed with the pastel print, especially paired with baggy jeans for that ultimate early 2000s streetwear vibe. Can't wait to live in this all summer. 

#y2k #thrifthaul #babytee

2 model calls this session, 732 prompt + 156 output tokens
```

**The same agent on a query nothing matches** (the branch: it stops after
`search_listings`, makes no model calls, and `fit_card` stays `None`)

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched 'designer ballgown' in size XXS under $5. Try: describe the item differently, since no listing mentions 'designer ballgown' (a type of clothing like tee, jeans, jacket, dress or sneakers, or a style like vintage, y2k, 90s or grunge); and raise your price: the cheapest listing is $12.

0 model calls this session
```

**Checking the state:** for each matching example query, the `id` of the first
search result, `selected_item`, and the `new_item` each later tool was called
with (from `session["tool_calls"]`):

```
vintage graphic tee under $30 | lst_033 lst_033 lst_033 lst_033 | fit_card: True ['search_listings', 'suggest_outfit', 'create_fit_card']
90s track jacket in size M | lst_004 lst_004 lst_004 lst_004 | fit_card: True ['search_listings', 'suggest_outfit', 'create_fit_card']
silk slip dress in midi length under $40 | lst_013 lst_013 lst_013 lst_013 | fit_card: True ['search_listings', 'suggest_outfit', 'create_fit_card']
platform sneakers size 8 | lst_019 lst_019 lst_019 lst_019 | fit_card: True ['search_listings', 'suggest_outfit', 'create_fit_card']
denim jacket under $50 | lst_007 lst_007 lst_007 lst_007 | fit_card: True ['search_listings', 'suggest_outfit', 'create_fit_card']
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_012', 'title': 'Oversized Crewneck Sweatshirt — Vintage Navy', 'description': 'Perfectly faded navy crewneck. Genuinely vintage — not manufactured distressed. Ribbed cuffs and hem. No graphics, clean.', 'category': 'tops', 'style_tags': ['vintage', 'basics', 'oversized', 'classic'], 'size': 'XL (fits oversized)', 'condition': 'good', 'price': 20.0, 'colors': ['navy'], 'brand': None, 'platform': 'thredUp'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]

$ python -c "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"
[]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[5], get_example_wardrobe()))"
Outfit 1: Graphic Tee — 2003 Tour Bootleg Style + Baggy straight-leg jeans, dark wash + Black combat boots
Why it works: Leans fully into the grunge aesthetic with matching dark tones and relaxed silhouettes.

Outfit 2: Graphic Tee — 2003 Tour Bootleg Style + Wide-leg khaki trousers + Chunky white sneakers
Why it works: The boxy black tee grounds the earthy trousers, creating an easy streetwear balance.

$ python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[5], get_empty_wardrobe()))"
General ideas:

Outfit 1:
Pieces: Oversized black tee, light-wash straight-leg jeans, beat-up white canvas sneakers, silver chain necklace.
Why it works: The light denim cuts the darkness of the top and keeps the grunge look effortless.

Outfit 2:
Pieces: Black tee tucked into olive green cargo pants, black combat boots, a canvas crossbody bag.
Why it works: It leans into the streetwear aesthetic with utilitarian textures that match the boxy cut.
```

Three runs with the cache off (`AI201_CACHE=0`) on the same item, to check
the cards really vary:

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('baggy dark-wash jeans, chunky white sneakers and a black denim jacket', load_listings()[5]))"
Scored this 2003 tour graphic tee on depop for $24 and it's already my favorite shirt. The boxy fit gives off the best grunge streetwear energy, especially paired with my chunky white sneakers. #thrifted #depopfinds #vintagestyle
---
Scored this vintage-style tour graphic tee on depop for $24 and I'm obsessed with the grunge vibe. The cotton is super soft and worn-in. Throwing it on with chunky white sneakers for the easiest everyday fit. 

#depopfinds #graphictee #streetwear
---
Scored this vintage-style tour graphic tee on depop for just $24 and I'm obsessed with the grunge vibe. The worn-in cotton feels amazing and it has the best boxy fit. Throwing it on with my chunky white sneakers and calling it a day. 

#thrifted #graphictree #depopfinds
---

$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"
Can't write a fit card: no outfit suggestion was given for Vintage Levi's 501 Jeans — Medium Wash.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* Claude Code wrote `create_fit_card` from my spec, and I
  had it run the tool three times on the same item with the cache off to check
  the cards vary.
- *What came back:* three different captions, each with `$24` and `depop` in
  them, but every one was written as the **seller**: "Grab it on depop for $24
  before I change my mind." The prompt said "a post about this thrift find",
  and the model took that as a sales listing.
- *What I changed:* the system prompt now says the caption is from the person
  who just bought the item, not the seller, and that it should never tell
  readers to buy it. The platform is now mentioned "as where they found it".
  The re-run cards read "Scored this 2003 tour graphic tee on depop for $24…".
  <!-- TODO: put this in your own words -->

**Moment 2**

- *What I asked for:* a message for the empty-search branch that tells the
  user what to change, not just "No results".
- *What came back:* the first version only told the user to try different
  words. For `'designer ballgown size XXS under $5'` that's half the story,
  because nothing in the data costs $5 (the cheapest listing is $12), so
  changing the words alone would still find nothing.
- *What I changed:* the message now re-runs the search without the size, then
  without the price, and says which filter is the problem. When the words
  match nothing, it also says if the price is below the cheapest listing.
  <!-- TODO: put this in your own words, and add anything you changed -->

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
