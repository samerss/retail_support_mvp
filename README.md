# Retail Support Agent (MVP)

A customer-support agent for **XPRS** ([myxprs.com](https://myxprs.com)), a real
Egyptian consumer-electronics retailer (powered by Tradeline), built with
[Google ADK](https://google.github.io/adk-docs/) (the `google-adk` framework).
The focus is on ADK concepts — agents, function tools, session state, and
tool-result handling. The store's "database" is a set of **CSV sheets** in
`shop_agent/data/` that you can edit in Excel or Google Sheets without touching
any code.

The agent can search products, look up orders, quote store policies, find store
branches, answer general FAQs, and manage a shopping cart. Prices are in EGP.

## Quick start

```bash
cd ~/retail_support_mvp
.venv/bin/adk web        # then pick "shop_agent" in the top-left dropdown
```

Open the URL it prints (usually http://localhost:8000). Prefer a terminal chat?
Use `.venv/bin/adk run shop_agent`.

**Prerequisites** (already set up here):
- `google-adk` 2.3.0 installed in `.venv/`.
- `shop_agent/.env` contains `GOOGLE_API_KEY=...`, which ADK auto-loads.

While testing in `adk web`, two panels are worth watching:
- **Events / trace** — shows which tool fired and the raw dict it returned. This
  is how you confirm a tool was actually called (vs. the model answering from
  memory).
- **State** — shows the `cart` key update after `add_to_cart`.

## Project structure

```
retail_support_mvp/
├── .venv/                  # virtualenv — has google-adk 2.3.0
└── shop_agent/             # THE AGENT PACKAGE (folder name = agent name in the UI)
    ├── __init__.py         # makes it a package; exposes the agent to ADK
    ├── agent.py            # tools + the root_agent  ← the heart of it
    ├── data.py             # loads the CSV sheets into PRODUCTS/ORDERS/POLICIES/FAQS/BRANCHES
    ├── data/               # ← THE DATA SHEETS (edit these to change the store)
    │   ├── products.csv    #     sku, name, price, currency, in_stock, category
    │   ├── orders.csv      #     order_id, status, carrier, tracking, eta_days, items, total
    │   ├── policies.csv    #     topic, policy
    │   ├── faqs.csv        #     faq_id, category, question, answer, keywords
    │   └── branches.csv    #     branch_id, name, area, city, hotline
    ├── .env                # GOOGLE_API_KEY=... (auto-loaded by ADK)
    └── .adk/               # scratch dir adk web creates (sessions/state) — ignore it
```

`shop_agent/` is an **ADK agent package**. When you run `adk web` from the parent
directory, ADK scans subfolders and any package exposing a `root_agent` shows up
in the dropdown. Three conventions make the wiring work:

1. **`__init__.py`** contains just `from . import agent`, which runs `agent.py`
   on import so `root_agent` becomes reachable. Boilerplate, but required.
2. **`root_agent`** (bottom of `agent.py`) is the *magic variable name* ADK looks
   for. Rename it and ADK won't find your agent.
3. **`.env`** next to the agent is auto-loaded — that's where `GOOGLE_API_KEY`
   comes from, so no key is ever hardcoded.

Import chain: `adk web` → imports `shop_agent` → `__init__.py` runs → imports
`agent.py` → defines `root_agent`.

## `data.py` and the CSV data sheets

The store's "database" lives in **CSV files** under `shop_agent/data/` — your
data sheets. `data.py` reads them once at startup (Python's stdlib `csv`) and
builds the in-memory structures the tools use. **To change the store you edit
the CSVs, not the code:**

- **`products.csv`** → **`PRODUCTS`**, a dict keyed by SKU (`"XPRS-1007"`) →
  `{name, price, currency, in_stock, category}`.
- **`orders.csv`** → **`ORDERS`**, a dict keyed by order id (`"XPRS-100231"`) →
  `{status, carrier, tracking, eta_days, items, total}`. The `items` column
  holds one or more product names joined with `|`; an empty `carrier`/`tracking`
  cell becomes `None`.
- **`policies.csv`** → **`POLICIES`**, a dict keyed by topic (`returns`,
  `shipping`, `warranty`, `payment`, `installments`) → the policy text.
  *Exact-key* lookup.
- **`faqs.csv`** → **`FAQS`**, a **list** of records
  (`faq_id, category, question, answer, keywords`); the `keywords` column is
  `|`-joined. It's a list (not a dict) because you don't look it up by a known
  key — you *search* across all entries by keyword.
- **`branches.csv`** → **`BRANCHES`**, a list of XPRS store locations
  (`branch_id, name, area, city, hotline`).

### Editing / adding data

Open any file in `shop_agent/data/` in Excel or Google Sheets (or a plain text
editor), add or change rows, **save as CSV**, and restart `adk web` — the new
data loads automatically. A few rules:

- Keep the **header row** and the column names exactly as they are.
- If a value contains a comma (most product names do), the spreadsheet wraps it
  in quotes automatically — that's expected and correct.
- For `orders.items` and `faqs.keywords`, separate multiple values with `|`.
- `price`/`total` are numbers (e.g. `11499.00`); `in_stock`/`eta_days` are whole
  numbers.

> **Heads-up on accuracy:** products, prices, policies and branches were taken
> from myxprs.com, but prices and stock change over time — verify before relying
> on them. The orders are **sample/test data** (real orders aren't public) and
> stock levels are placeholders.

## `agent.py` — the tools and the agent

### The tool contract (the core concept)

> A tool is a plain Python function. **Its docstring and type hints are sent to
> the model** as the tool's "API documentation." The model reads them to decide
> *when* to call it and *what arguments* to pass.

That's why every function has typed params and a detailed `Args:` / `Returns:`
docstring — you're writing the prompt the model sees, not just human docs. Two
more rules the code follows everywhere:

- **Every tool returns a `dict`** (never a bare string) — structured data the
  model can reason over.
- **Every dict has a `"status"` field** (`"success"`, `"not_found"`,
  `"no_results"`, `"unknown_topic"`, `"low_confidence"`, `"no_match"`, …). This
  lets the agent distinguish "here's your answer" from "I couldn't find it," and
  the instruction tells it how to handle each.

Tools also normalize input (`.lower().strip()`, `.upper().strip()`) because the
model passes human-ish text.

### The tools

| Tool | Signature | What it does | Lookup style |
|---|---|---|---|
| `search_products` | `(query)` | substring-matches name/category | fuzzy (loops all) |
| `get_product_details` | `(sku)` | one product by SKU | exact key |
| `check_order_status` | `(order_id)` | one order by id | exact key |
| `get_policy` | `(topic)` | one policy string by topic | exact key |
| `get_faq_response` | `(query)` | keyword-scored FAQ search | fuzzy + confidence gate |
| `add_to_cart` | `(sku, quantity, tool_context)` | adds to cart **in session state** | writes state |
| `find_store` | `(query="")` | branches matching an area/mall (all if empty) | fuzzy (loops all) |

**`add_to_cart` and session state.** It takes a third param,
`tool_context: ToolContext`, which ADK *injects* automatically — the model never
sees or fills it (it's excluded from the schema by its type). Through it the tool
reads and writes **session state**, which persists across turns:

```python
cart = tool_context.state.get("cart", [])   # read what's there
cart.append({...})                            # mutate
tool_context.state["cart"] = cart             # write back — survives to next turn
```

The State tab in `adk web` is literally showing this `state` dict.

### `get_faq_response` — keyword-matched FAQ

Modelled on Maestro's (an internal app) `get_faq_response`, which answers general
"how does it work" questions from a structured FAQ knowledge base and gates the
answer on a confidence score. Maestro scores matches with **semantic embeddings**;
this MVP keeps it lightweight with **keyword/substring matching** — the interface,
data shape, and confidence gating are identical, only the scoring engine differs.

The body:

1. Normalize the query; guard against empty input.
2. **Score every FAQ entry**: +1 per keyword hit (multi-word keywords match as a
   phrase anywhere; single words match as whole words), plus a small `0.25` nudge
   for overlap with the canonical question's words.
3. **Pick the best** and convert to a rough 0–1 confidence (`best_score / 2.0`,
   capped at 1.0 — so ~2 keyword hits reads as confident).
4. **Gate on confidence**, returning one of three statuses:
   - `success` — confidence ≥ 0.5; includes `answer`, `faq_id`, `category`.
   - `low_confidence` — a weak match; returns **no answer text**.
   - `no_match` — nothing scored.

Returning no answer on a weak match is the **anti-hallucination guardrail**: the
model has nothing to relay, so it must ask a clarifying question instead of
guessing. The instruction enforces this ("Only relay the answer when the status
is 'success'").

### The `Agent` object

```python
root_agent = Agent(
    model="gemini-3-flash-preview",   # the LLM that reasons and picks tools
    name="xprs_support",
    description="...",                 # used when one agent delegates to another
    instruction="...",                 # the system prompt — persona + routing + hard rules
    tools=[search_products, get_product_details, check_order_status,
           get_policy, get_faq_response, add_to_cart, find_store],
)
```

- **`model`** — the Gemini model driving the agent.
- **`tools`** — the toolbox. **A tool exists to the model only if it's in this
  list.** Adding a tool means three edits: define the function, add it here, and
  mention it in the instruction.
- **`instruction`** — the system prompt: persona ("friendly, concise… in Egypt,
  for XPRS in Egypt, prices in EGP"), which tool to use for what, and hard rules ("Never make up a
  price…"; "Only relay the FAQ answer when status is 'success'").

## How a question flows through

For *"How long does delivery take?"*:

1. ADK builds the request: your message + the `instruction` + the
   **auto-generated JSON schemas** of all 7 tools (from their docstrings/hints) +
   conversation history.
2. Gemini decides: *general shop question → call
   `get_faq_response(query="How long does delivery take?")`.*
3. ADK runs the Python function; it scores the FAQs, F2 wins, returns
   `{"status": "success", "answer": "We deliver across Egypt, usually within
   about 48 hours…", "confidence": 1.0}`.
4. That dict is fed **back into the model** as the tool result.
5. The model turns it into a natural reply and sends it to you.

The model orchestrates; the tools supply facts. The Events panel in `adk web`
lets you watch steps 2–4 for each message.

## Testing — questions to ask

**FAQ tool → `success`, relays the answer**
- "How long does delivery take?"
- "Can I pay cash on delivery?"
- "Can I pay in monthly installments?"
- "What's your return policy?"
- "Do I need an account to buy something?"
- "Can I cancel my order after placing it?"

**FAQ guardrails**
- "What's the meaning of life?" → no confident match; the agent should *not*
  invent an answer, just offer to help with shop topics.
- "Tell me about it" (vague) → likely `low_confidence`; should ask to clarify.
- "Do you offer gift wrapping?" → no confident match; should say it doesn't know.

**The other tools**
- "Show me your laptops" → `search_products` (try "tablet" or "phone" too)
- "What's the price and stock of XPRS-1007?" → `get_product_details`
  (Samsung Galaxy S26 Ultra)
- "Where's my order XPRS-100231?" → `check_order_status` (shipped, with tracking)
- "Status of XPRS-99999?" → `not_found`, handled gracefully
- "Add 2 of XPRS-1002 to my cart" → `add_to_cart` (check the State tab)
- "Do you have a store in Madinaty?" / "Nearest branch to Zamalek?" → `find_store`

**Boundary probes (tool choice)**
- "How does shipping work?" vs. "What is your shipping policy?" → both should give
  consistent shipping info even though one tends to hit `get_faq_response` and the
  other `get_policy`.
- "I want to buy a laptop and also — how long until it arrives?" → a product
  lookup *and* the FAQ in one turn.
- "Is the Infinix Hot 60 5G in stock?" → seeded as out-of-stock (`in_stock: 0`),
  so the agent should say it's unavailable rather than offer to add it.

## Notes

- `get_faq_response` and `get_policy` overlap (both cover shipping/returns/
  warranty/payment): the FAQ tool is the broad, fuzzy entry point; `get_policy` is
  the exact-topic lookup. Kept separate for now; could be consolidated.
- This is an MVP — no persistence beyond the in-memory ADK session, no auth, and
  the data lives in CSV sheets in `shop_agent/data/` (loaded at startup, no live
  backend).
