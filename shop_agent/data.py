"""Data layer for the XPRS retail support agent.

The "database" is a set of CSV files in ./data/ that you can edit in Excel or
Google Sheets — no code changes needed to update the catalog, orders, policies,
FAQs, or store branches. This module loads those CSVs at import time into the
in-memory structures the agent's tools expect:

    PRODUCTS         dict  sku       -> {name, brand, price, currency, in_stock, category, colors}
    ORDERS           dict  order_id  -> {status, carrier, tracking, eta_days, items, total}
    POLICIES         dict  topic     -> policy text
    FAQS             list  of        {faq_id, category, question, answer, keywords}
    BRANCHES         list  of        {branch_id, name, area, city, hotline, notes}
    INSTALLMENT_APPS list  of        {app, hotline}

Data source: products, prices, policies and branches are real (from myxprs.com).
Orders are sample/test data and stock levels are placeholders — edit the CSVs in
shop_agent/data/ to match your real backend.
"""

import csv
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _read_rows(filename):
    """Read a CSV file in DATA_DIR and return its rows as a list of dicts."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _split(value):
    """Split a '|'-joined CSV cell into a clean list (empty cell -> [])."""
    if not value:
        return []
    return [part.strip() for part in value.split("|") if part.strip()]


def _load_products():
    products = {}
    for row in _read_rows("products.csv"):
        products[row["sku"].strip()] = {
            "name": row["name"],
            # brand/colors are optional columns (.get) so older sheets still load.
            "brand": row.get("brand", ""),
            "price": float(row["price"]),
            "currency": row["currency"],
            "in_stock": int(row["in_stock"]),
            "category": row["category"],
            "colors": _split(row.get("colors", "")),
        }
    return products


def _load_orders():
    orders = {}
    for row in _read_rows("orders.csv"):
        orders[row["order_id"].strip()] = {
            "status": row["status"],
            # Empty cells become None (e.g. an order with no carrier yet).
            "carrier": row["carrier"] or None,
            "tracking": row["tracking"] or None,
            "eta_days": int(row["eta_days"]) if row["eta_days"] else None,
            "items": _split(row["items"]),
            "total": float(row["total"]),
        }
    return orders


def _load_policies():
    # Keys are lower-cased so lookups are case-insensitive (matches get_policy).
    return {
        row["topic"].strip().lower(): row["policy"]
        for row in _read_rows("policies.csv")
    }


def _load_faqs():
    faqs = []
    for row in _read_rows("faqs.csv"):
        faqs.append({
            "faq_id": row["faq_id"],
            "category": row["category"],
            "question": row["question"],
            "answer": row["answer"],
            "keywords": _split(row["keywords"]),
        })
    return faqs


def _load_branches():
    branches = []
    for row in _read_rows("branches.csv"):
        branches.append({
            "branch_id": row["branch_id"],
            "name": row["name"],
            "area": row["area"],
            "city": row["city"],
            "hotline": row["hotline"],
            "notes": row.get("notes", ""),
        })
    return branches


def _load_installment_apps():
    apps = []
    for row in _read_rows("installment_apps.csv"):
        apps.append({"app": row["app"], "hotline": row["hotline"]})
    return apps


# Loaded once at import. agent.py imports these names directly, so the tools see
# the same shapes they always have — only the source (CSV vs. hardcoded) changed.
PRODUCTS = _load_products()
ORDERS = _load_orders()
POLICIES = _load_policies()
FAQS = _load_faqs()
BRANCHES = _load_branches()
INSTALLMENT_APPS = _load_installment_apps()
