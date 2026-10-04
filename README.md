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
  ends with up to 3 hashtags. If the listing has no brand, the brand isn't
  mentioned.
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

**One full query**

```
$ python app.py ask '...'

```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

```

```
$ python -c "from tools import suggest_outfit; ..."

```

```
$ python -c "from tools import create_fit_card; ..."

```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

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
