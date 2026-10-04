# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

*How it's checked:* a try passes when `session["error"]` is `None`,
`session["tool_calls"]` lists `search_listings`, `suggest_outfit`,
`create_fit_card` in that order, and `session["fit_card"]` is a non-empty
string. Tested with `'vintage graphic tee under $30'`.

**Why this target:**
`search_listings` is a plain keyword match on single words. A query that
describes a listing in words the listing doesn't use ("tshirt" when the data
says "tee", or "trainers" when it says "sneakers") can score 0 and end the run
early even though a match exists. Also, two of the three steps call the model
over the network, and one rate-limit failure or timeout in five runs is
realistic on the free tier. 5 of 5 would assume both problems never happen.
I didn't go lower than 4 because the example queries were checked against the
data and use the same words the listings do.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

*How it's checked:* a try passes when `session["tool_calls"]` holds only
`search_listings`, `session["outfit_suggestion"]` and `session["fit_card"]` are
both `None`, and `session["error"]` names at least one of the size, the price
or the words used and says what to do about it. Tested with
`'designer ballgown size XXS under $5'`.

**Why this target:**
This path never touches the model. The query is parsed with regex, the search
is a filter over a local file, and the branch is a plain `if not results`
check. The same input gives the same output every time, so nothing random can
excuse a miss. If it fails once, it'll fail every time, and that's a bug and
not bad luck. "Names what to change" is checked by reading the message: it has
to name at least one of the filters (the price, the size or the keywords) and
say what to do with it. "No results found" alone fails.

---

## 3. The item search found is the item the later tools received

For 5 different matching queries (the five non-empty queries from
`python app.py examples`), every run satisfies all of the following, checked
in the returned session: `session["selected_item"]["id"]` equals
`session["search_results"][0]["id"]`, and it also equals the `id` of the
`new_item` argument recorded in `session["tool_calls"]` for **both**
`suggest_outfit` and `create_fit_card`. Also, the user's query text appears
nowhere in either of those recorded arguments, because the item comes from
state and not from the user retyping it. Target: 5 of 5 queries.

**Why this target:**
Passing the item along is my own code reading and writing a dict, with no model
involved. Once it works it should work every time, so anything below 5 of 5
would be accepting a known bug. I picked comparing `id`s at three points
instead of reading the outfit text and judging "does this sound like the same
item", because the model sometimes paraphrases a title, and that would make a
state check depend on the model's wording.

---

---

## 4. The fit card is postable, accurate and not a template

Run `'vintage graphic tee under $30'` 5 times with the cache off
(`AI201_CACHE=0`). A run's card passes if it meets all three of these:
(a) the whole card, hashtags included, is 400 characters or fewer, (b) it contains the selected item's price
written as `$` followed by the whole-dollar amount (for example `$24`; `$24.00`
also counts), and (c) it contains the selected item's `platform` name, ignoring
case. Target: at least 4 of 5 cards pass. Also, none of the 5 cards may be
word-for-word identical to another (5 of 5 distinct).

**Why this target:**
The model gets the price and platform in the prompt and is told to use them,
but at temperature 0.9 it sometimes rewrites a price ("under 25 bucks") or
leaves out the platform, so I expect the odd miss, and 5 of 5 on (a)–(c) would
be a claim about the model I can't back up. I didn't go below 4 because the
prompt asks for these exact things, so missing two out of five would mean the
prompt isn't working. The "all 5 distinct" part is strict on purpose. If two
cards come out identical, caching is on or the temperature is 0, and either
one means the test isn't testing anything.

---

---

## 5. The price ceiling and size the user typed are the ones actually applied

For each of these 5 queries:

| Query | Expected `max_price` | Expected `size` |
|---|---|---|
| `vintage graphic tee under $30` | 30.0 | None |
| `90s track jacket in size M` | None | `M` |
| `platform sneakers size 8` | None | `8` |
| `denim jacket below 50 dollars` | 50.0 | None |
| `knit cardigan, size M, max $40` | 40.0 | `M` |

`session["parsed"]` holds exactly the expected `max_price` and `size`, **and**
every listing in `session["search_results"]` has `price <= max_price` (when
there is one) and a size that passes the size rule in the README's Tool
Inventory (when there is one). Target: 5 of 5 queries.

**Why this target:**
A filter that's quietly ignored is the failure I'd be most annoyed by as a
user: I say "under $30" and get shown a $45 jacket, with nothing telling me
why. The starter even warns that PowerShell double quotes can eat `$30`. The
parsing is regex and the filter is arithmetic, so there's no randomness to
allow for, and a miss on any of these five phrasings is a real bug. I picked
five different ways of writing a price and a size ("under $", "below …
dollars", "max $", "in size", ", size X,") so the target can't be met by a
parser that only handles the one phrasing in the examples.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
