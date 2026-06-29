"""Retail customer support agent (MVP).

Concepts this file demonstrates:
  * Agent          -> identity + instruction + tools (the root_agent)
  * Function tools  -> plain Python functions the model can call
  * ToolContext     -> lets a tool read/write session state (see add_to_cart)

Run it:
  adk web          # then pick "shop_agent" in the top-left dropdown
"""

from google.adk.agents.llm_agent import Agent
from google.adk.tools.tool_context import ToolContext

from .data import PRODUCTS, ORDERS, POLICIES, FAQS, BRANCHES, INSTALLMENT_APPS


# --- Tools -------------------------------------------------------------------
# Every tool returns a dict. The docstring + type hints are what the model
# sees, so write them like you are explaining the tool to the model.

def search_products(query: str) -> dict:
    """Search the product catalog by name, brand, or category.

    Args:
        query: A keyword such as a product name, brand, partial name, or
            category (for example "Samsung", "headphones", or "air fryer").

    Returns:
        A dict with a list of matching products, each including its SKU,
        name, brand, price, currency, available colors, and stock.
    """
    q = query.lower().strip()
    matches = []
    for sku, p in PRODUCTS.items():
        if q in p["name"].lower() or q in p["category"].lower() or q in p.get("brand", "").lower():
            matches.append({"sku": sku, **p})

    if not matches:
        return {"status": "no_results", "query": query, "products": []}
    return {"status": "success", "count": len(matches), "products": matches}


def get_product_details(sku: str) -> dict:
    """Look up full details for a single product by its SKU.

    Args:
        sku: The product SKU, e.g. "SKU-1003".

    Returns:
        The product record, or an error status if the SKU is unknown.
    """
    sku = sku.upper().strip()
    product = PRODUCTS.get(sku)
    if not product:
        return {"status": "not_found", "sku": sku}
    return {"status": "success", "sku": sku, **product}


def check_order_status(order_id: str) -> dict:
    """Check the status, carrier, and tracking number for an order.

    Args:
        order_id: The order reference, e.g. "ORD-55012".

    Returns:
        The order record including status and tracking, or an error status
        if the order ID is not found.
    """
    order_id = order_id.upper().strip()
    order = ORDERS.get(order_id)
    if not order:
        return {"status": "not_found", "order_id": order_id}
    return {"status": "success", "order_id": order_id, **order}


def get_policy(topic: str) -> dict:
    """Return the store policy for a given topic.

    Args:
        topic: One of "returns", "exchange", "shipping", "pickup", "warranty",
            "payment", "installments", "discounts", "gaming", or "contact".

    Returns:
        The policy text, or the list of valid topics if the topic is unknown.
    """
    topic = topic.lower().strip()
    policy = POLICIES.get(topic)
    if not policy:
        return {"status": "unknown_topic", "valid_topics": list(POLICIES.keys())}
    return {"status": "success", "topic": topic, "policy": policy}


def get_faq_response(query: str) -> dict:
    """Answer a general/FAQ question about the shop (ordering, shipping,
    returns, warranty, payment, accounts).

    Use this for "how does it work" style questions that are not about a
    specific product, order, or cart. The question is matched against a small
    FAQ knowledge base by keyword, and only a confident match is returned.

    Args:
        query: The customer's question, in their own words, e.g. "how long
            does shipping take?" or "can I pay cash on delivery?".

    Returns:
        On a confident match, a dict with status "success", the matched
        FAQ id, the answer to relay, and a confidence score. Otherwise a
        "low_confidence" or "no_match" status so you can ask a clarifying
        question instead of guessing.
    """
    # Modelled on Maestro's get_faq_response: score each FAQ and only return a
    # match the agent should trust. Maestro scores with semantic embeddings;
    # this MVP keeps it simple with keyword/substring matching.
    q = (query or "").lower().strip()
    if not q:
        return {"status": "no_match", "message": "Empty question — ask the customer to rephrase."}

    q_words = set(q.split())
    scored = []
    for faq in FAQS:
        score = 0
        for kw in faq["keywords"]:
            kw = kw.lower()
            # Phrase appears in the question, or the keyword is a single word
            # the customer used.
            if kw in q or (" " not in kw and kw in q_words):
                score += 1
        # A nudge if words from the canonical question overlap the query.
        score += len(q_words & set(faq["question"].lower().split())) * 0.25
        if score > 0:
            scored.append((score, faq))

    if not scored:
        return {
            "status": "no_match",
            "message": "No FAQ match — ask a clarifying question or offer to help another way.",
        }

    scored.sort(key=lambda s: s[0], reverse=True)
    best_score, best = scored[0]
    # Normalise to a rough 0-1 confidence; 2+ keyword hits reads as confident.
    confidence = min(best_score / 2.0, 1.0)
    if confidence < 0.5:
        return {
            "status": "low_confidence",
            "confidence": round(confidence, 2),
            "faq_id": best["faq_id"],
            "message": "No confident FAQ match — ask a clarifying question before answering.",
        }
    return {
        "status": "success",
        "faq_id": best["faq_id"],
        "category": best["category"],
        "confidence": round(confidence, 2),
        "answer": best["answer"],
    }


def add_to_cart(sku: str, quantity: int, tool_context: ToolContext) -> dict:
    """Add a product to the customer's cart, stored in session state.

    This tool writes to session state via tool_context. Open the State tab in
    adk web after calling it to watch the "cart" key update across turns.

    Args:
        sku: The product SKU to add, e.g. "SKU-1001".
        quantity: How many units to add (must be 1 or more).
        tool_context: Injected by ADK; gives access to session state.

    Returns:
        The updated cart contents and a running total.
    """
    sku = sku.upper().strip()
    product = PRODUCTS.get(sku)
    if not product:
        return {"status": "not_found", "sku": sku}
    if quantity < 1:
        return {"status": "invalid_quantity", "quantity": quantity}
    if product["in_stock"] < quantity:
        return {
            "status": "insufficient_stock",
            "sku": sku,
            "requested": quantity,
            "available": product["in_stock"],
        }

    # Read existing cart from state (default to empty list), then update it.
    cart = tool_context.state.get("cart", [])
    cart.append({
        "sku": sku,
        "name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
    })
    tool_context.state["cart"] = cart

    total = sum(item["unit_price"] * item["quantity"] for item in cart)
    return {
        "status": "success",
        "added": {"sku": sku, "name": product["name"], "quantity": quantity},
        "cart": cart,
        "cart_total": round(total, 2),
        "currency": product["currency"],
    }


def find_store(query: str = "") -> dict:
    """Find XPRS store branches, or the branch nearest to an area the customer mentions.

    Args:
        query: An area, district, city, or mall name to match against, e.g.
            "Nasr City", "Zamalek", "Madinaty", or "Mall of Arabia". Leave it
            empty to list every branch.

    Returns:
        A dict with a list of matching branches, each including its name, area,
        city, and hotline.
    """
    q = query.lower().strip()
    matches = []
    for b in BRANCHES:
        if (not q or q in b["name"].lower() or q in b["area"].lower()
                or q in b["city"].lower() or q in b.get("notes", "").lower()):
            matches.append(b)

    if not matches:
        return {"status": "no_results", "query": query, "branches": []}
    return {"status": "success", "count": len(matches), "branches": matches}


def get_installment_apps(query: str = "") -> dict:
    """List installment-app hotlines, or look up one app's hotline.

    Customers call an app's hotline to open an account and get an available
    spending limit, then contact XPRS (19857) to complete the order.

    Args:
        query: An app name to look up (for example "Valu" or "Halan"). Leave it
            empty to list every installment app and its hotline.

    Returns:
        A dict with the matching installment apps, each with its name and hotline.
    """
    q = query.lower().strip()
    matches = [a for a in INSTALLMENT_APPS if not q or q in a["app"].lower()]
    if not matches:
        return {"status": "no_results", "query": query, "apps": []}
    return {"status": "success", "count": len(matches), "apps": matches}


# --- Agent -------------------------------------------------------------------

root_agent = Agent(
    model="gemini-3-flash-preview",
    name="xprs_support",
    description="Customer support agent for XPRS, an electronics retailer in Egypt (powered by Tradeline).",
    instruction=(
        "You are a friendly, concise customer support agent for XPRS, a consumer "
        "electronics retailer in Egypt (powered by Tradeline). XPRS sells a wide "
        "range of electronics and home appliances — phones, laptops, tablets, "
        "gaming, TVs, audio, accessories, plus appliances like air conditioners, "
        "air fryers and refrigerators — online and across 9 stores in Greater "
        "Cairo, Giza and the North Coast. All prices are in Egyptian Pounds (EGP)."
        "\n\n"
        "Your job:\n"
        "- Help customers find products, check prices and stock, and compare "
        "options. Use search_products and get_product_details.\n"
        "- Look up order status and tracking with check_order_status when a "
        "customer gives an order ID (they look like 'XPRS-100231').\n"
        "- Answer questions about returns, exchange, shipping, store pickup, "
        "warranty, payment, installments, discounts, gaming and contact details "
        "using get_policy. Do not invent policy details; if get_policy returns an "
        "unknown topic, tell the customer the topics you can help with.\n"
        "- Tell customers where XPRS stores are, or find the branch nearest to an "
        "area they mention, using find_store.\n"
        "- For installment app hotlines (so a customer can open an account and "
        "get a limit), use get_installment_apps.\n"
        "- For general 'how does it work' questions about the shop (ordering, "
        "delivery times, returns, warranty, payment, installments, cancelling, "
        "accounts, stores), use get_faq_response. Pass the customer's question "
        "through roughly as they asked it. Only relay the answer when the status "
        "is 'success'; on 'low_confidence' or 'no_match', do NOT relay anything — "
        "ask a clarifying question or offer to help another way.\n"
        "- When a customer wants to buy something, use add_to_cart and then "
        "confirm what is in their cart and the running total.\n\n"
        "Key facts to use: customers pay by cash or in installments (a Visa "
        "'Purchases' card from Banque Misr, NBE, CIB or QNB, or apps like Valu, "
        "Souhoola and Halan; minimum age 21; InstaPay, Vodafone Cash and Meeza "
        "are not accepted). Delivery is about 7 to 10 working days (10 to 15 for "
        "large appliances) to all governorates, and store pickup is not "
        "available. Every purchase has warranty and XPRS offers price-matching. "
        "For anything you can't resolve, point customers to the hotline 19857 or "
        "sales@myxprs.com.\n\n"
        "Always rely on the tools for facts. If a tool returns 'not_found' or "
        "'no_results', say so plainly and offer to help another way. Never make "
        "up a price, stock level, tracking number, store address, or policy."
    ),
    tools=[
        search_products,
        get_product_details,
        check_order_status,
        get_policy,
        get_faq_response,
        add_to_cart,
        find_store,
        get_installment_apps,
    ],
)
