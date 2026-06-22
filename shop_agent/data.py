"""Mock "database" for the retail shop.

In a real app these functions would hit a real backend. For this MVP they
return canned data so you can focus on learning ADK concepts.
"""

# --- Product catalog ---------------------------------------------------------

PRODUCTS = {
    "SKU-1001": {
        "name": "Aurora Wireless Headphones",
        "price": 1899.00,
        "currency": "EGP",
        "in_stock": 12,
        "category": "audio",
    },
    "SKU-1002": {
        "name": "Nimbus Mechanical Keyboard",
        "price": 2450.00,
        "currency": "EGP",
        "in_stock": 0,
        "category": "accessories",
    },
    "SKU-1003": {
        "name": "Pulse 27\" 1440p Monitor",
        "price": 12900.00,
        "currency": "EGP",
        "in_stock": 5,
        "category": "displays",
    },
    "SKU-1004": {
        "name": "Drift USB-C Hub 7-in-1",
        "price": 690.00,
        "currency": "EGP",
        "in_stock": 33,
        "category": "accessories",
    },
}

# --- Orders ------------------------------------------------------------------

ORDERS = {
    "ORD-55012": {
        "status": "shipped",
        "carrier": "Bosta",
        "tracking": "BST-9921044",
        "eta_days": 2,
        "items": ["Aurora Wireless Headphones", "Drift USB-C Hub 7-in-1"],
        "total": 2589.00,
    },
    "ORD-55013": {
        "status": "processing",
        "carrier": None,
        "tracking": None,
        "eta_days": 5,
        "items": ["Pulse 27\" 1440p Monitor"],
        "total": 12900.00,
    },
    "ORD-55099": {
        "status": "delivered",
        "carrier": "Bosta",
        "tracking": "BST-7741200",
        "eta_days": 0,
        "items": ["Nimbus Mechanical Keyboard"],
        "total": 2450.00,
    },
}

# --- Store policies ----------------------------------------------------------

POLICIES = {
    "returns": (
        "Items can be returned within 14 days of delivery if unused and in "
        "original packaging. Refunds are processed within 5 business days."
    ),
    "shipping": (
        "Standard shipping is 2 to 5 business days inside Egypt. Orders above "
        "2000 EGP ship free; otherwise a flat 60 EGP fee applies."
    ),
    "warranty": (
        "All electronics carry a 1-year limited warranty covering manufacturing "
        "defects. Accidental damage is not covered."
    ),
    "payment": (
        "We accept Visa, Mastercard, Meeza, and cash on delivery. Installment "
        "plans are available on orders above 5000 EGP."
    ),
}

# --- FAQs --------------------------------------------------------------------
# Structured FAQ knowledge base, modelled on Maestro's `customer_faqs`: each
# entry has an id, a category, the canonical question, the answer to relay, and
# a list of keywords used for matching. Maestro scores matches with semantic
# embeddings; this MVP keeps it lightweight with a plain keyword match.

FAQS = [
    {
        "faq_id": "F1",
        "category": "ordering",
        "question": "How do I place an order?",
        "answer": (
            "Add the items you want to your cart, then head to checkout. You can "
            "pay by card, Meeza, or choose cash on delivery."
        ),
        "keywords": ["order", "place order", "buy", "checkout", "purchase", "how to order"],
    },
    {
        "faq_id": "F2",
        "category": "shipping",
        "question": "How long does delivery take?",
        "answer": (
            "Standard delivery takes 2 to 5 business days inside Egypt. Orders "
            "above 2000 EGP ship free; otherwise a flat 60 EGP fee applies."
        ),
        "keywords": ["delivery", "shipping", "how long", "ship", "arrive", "eta", "delivery time"],
    },
    {
        "faq_id": "F3",
        "category": "returns",
        "question": "What is your return policy?",
        "answer": (
            "Items can be returned within 14 days of delivery if unused and in "
            "their original packaging. Refunds are processed within 5 business days."
        ),
        "keywords": ["return", "refund", "exchange", "send back", "money back"],
    },
    {
        "faq_id": "F4",
        "category": "warranty",
        "question": "Do products come with a warranty?",
        "answer": (
            "All electronics carry a 1-year limited warranty covering "
            "manufacturing defects. Accidental damage is not covered."
        ),
        "keywords": ["warranty", "guarantee", "defect", "broken", "repair"],
    },
    {
        "faq_id": "F5",
        "category": "payment",
        "question": "What payment methods do you accept?",
        "answer": (
            "We accept Visa, Mastercard, Meeza, and cash on delivery. Installment "
            "plans are available on orders above 5000 EGP."
        ),
        "keywords": ["payment", "pay", "card", "visa", "mastercard", "meeza", "cash", "installment"],
    },
    {
        "faq_id": "F6",
        "category": "ordering",
        "question": "Can I cancel or change my order?",
        "answer": (
            "You can cancel or change an order while it is still 'processing'. "
            "Once it has shipped it can no longer be changed, but you can return "
            "it after delivery under our 14-day return policy."
        ),
        "keywords": ["cancel", "change order", "modify", "edit order", "cancel order"],
    },
    {
        "faq_id": "F7",
        "category": "account",
        "question": "Do I need an account to shop?",
        "answer": (
            "You can browse and check prices without an account. To place an order "
            "and track it you'll need to sign in or check out as a guest with your "
            "email and phone number."
        ),
        "keywords": ["account", "sign up", "register", "login", "guest", "sign in"],
    },
    {
        "faq_id": "F8",
        "category": "shipping",
        "question": "Which areas do you deliver to?",
        "answer": (
            "We deliver to all governorates across Egypt. Delivery to Cairo and "
            "Giza is usually fastest, typically within 2 business days."
        ),
        "keywords": ["deliver to", "areas", "location", "governorate", "cairo", "where", "coverage"],
    },
]
