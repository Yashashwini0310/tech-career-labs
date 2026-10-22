#!/usr/bin/env python3
"""
ShopFast data generator.

Creates a realistic, deterministic e-commerce dataset (same output every run)
used by every lab in this repo:

  customers.csv   ~20,000 rows
  products.csv    500 rows
  orders.csv      ~200,000 rows  (Jan 2025 - Oct 2026)
  order_items.csv ~450,000 rows
  payments.csv    one per order (captured / refunded / failed)

Usage:
  python3 shared/generate_data.py --out lab1-support/db/data
"""
import argparse
import csv
import os
import random
from datetime import date, datetime, timedelta

SEED = 42
N_CUSTOMERS = 20_000
N_PRODUCTS = 500
N_ORDERS = 200_000
START = datetime(2025, 1, 1)
END = datetime(2026, 10, 20, 23, 59, 59)

FIRST = ["Aoife", "Sean", "Niamh", "Conor", "Ciara", "Liam", "Emma", "Jack", "Sophie", "Darragh",
         "Priya", "Arjun", "Wei", "Li", "Maria", "Jose", "Anna", "Tomas", "Fatima", "Omar",
         "Grace", "Cian", "Saoirse", "Oisin", "Chloe", "Adam", "Ella", "Noah", "Zoe", "Ethan"]
LAST = ["Murphy", "Kelly", "O'Brien", "Walsh", "Byrne", "Ryan", "O'Connor", "Doyle", "McCarthy",
        "Gallagher", "Sharma", "Patel", "Chen", "Wang", "Garcia", "Silva", "Nowak", "Kowalski",
        "Khan", "Ali", "Smith", "Brennan", "Quinn", "Nolan", "Kavanagh", "Lynch", "Farrell"]
LOCATIONS = [("Ireland", "Dublin", 40), ("Ireland", "Cork", 12), ("Ireland", "Galway", 8),
             ("Ireland", "Limerick", 6), ("United Kingdom", "London", 10), ("United Kingdom", "Belfast", 5),
             ("Germany", "Berlin", 6), ("France", "Paris", 5), ("Spain", "Madrid", 4), ("Netherlands", "Amsterdam", 4)]
SEGMENTS = [("consumer", 80), ("small_business", 15), ("enterprise", 5)]
CATEGORIES = {
    "Electronics": (25, 900), "Home & Kitchen": (8, 250), "Books": (5, 45), "Fashion": (10, 180),
    "Sports": (12, 300), "Beauty": (6, 90), "Toys": (8, 120), "Grocery": (2, 40),
}
SUPPLIERS = ["Emerald Wholesale", "Liffey Distribution", "EuroGoods BV", "Atlantic Supply Co",
             "Celtic Imports", "NorthStar Trading", "Shannon Logistics", "BlueHarbour Ltd"]
CHANNELS = [("web", 55), ("app", 35), ("marketplace", 10)]
PROVIDERS = [("stripe", 60), ("adyen", 30), ("paypal", 10)]


def weighted(rng, pairs):
    total = sum(p[-1] for p in pairs)
    r = rng.uniform(0, total)
    upto = 0
    for p in pairs:
        upto += p[-1]
        if upto >= r:
            return p
    return pairs[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    rng = random.Random(SEED)

    # customers
    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        fn, ln = rng.choice(FIRST), rng.choice(LAST)
        country, city, _ = weighted(rng, LOCATIONS)
        signup = START - timedelta(days=rng.randint(0, 900)) + timedelta(days=rng.randint(0, 600))
        email = f"{fn}.{ln}{cid}@example.com".lower().replace("'", "")
        customers.append((cid, fn, ln, email, country, city, signup.date().isoformat(), weighted(rng, SEGMENTS)[0]))
    with open(os.path.join(args.out, "customers.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["customer_id", "first_name", "last_name", "email", "country", "city", "signup_date", "segment"])
        w.writerows(customers)

    # products
    products = []
    cats = list(CATEGORIES)
    for pid in range(1, N_PRODUCTS + 1):
        cat = cats[(pid - 1) % len(cats)]
        lo, hi = CATEGORIES[cat]
        price = round(rng.uniform(lo, hi), 2)
        cost = round(price * rng.uniform(0.45, 0.75), 2)
        products.append((pid, f"SKU-{cat[:3].upper()}-{pid:04d}", f"{cat} item {pid}", cat, price, cost,
                         rng.choice(SUPPLIERS), "true" if rng.random() > 0.05 else "false"))
    with open(os.path.join(args.out, "products.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["product_id", "sku", "name", "category", "unit_price", "cost_price", "supplier", "active"])
        w.writerows(products)

    # orders, items, payments
    span = int((END - START).total_seconds())
    of = open(os.path.join(args.out, "orders.csv"), "w", newline="")
    itf = open(os.path.join(args.out, "order_items.csv"), "w", newline="")
    pf = open(os.path.join(args.out, "payments.csv"), "w", newline="")
    ow, iw, pw = csv.writer(of), csv.writer(itf), csv.writer(pf)
    ow.writerow(["order_id", "customer_id", "order_ts", "status", "channel", "discount_pct", "shipping_fee", "currency"])
    iw.writerow(["order_item_id", "order_id", "product_id", "quantity", "unit_price"])
    pw.writerow(["payment_id", "order_id", "provider", "provider_txn_id", "amount", "paid_ts", "status"])

    # generate timestamps sorted so order_id follows time
    stamps = sorted(rng.randint(0, span) for _ in range(N_ORDERS))
    item_id = 0
    for oid, s in enumerate(stamps, start=1):
        ts = START + timedelta(seconds=s)
        cust = rng.randint(1, N_CUSTOMERS)
        r = rng.random()
        status = ("delivered" if r < 0.78 else "shipped" if r < 0.86 else "placed" if r < 0.90
                  else "cancelled" if r < 0.95 else "refunded")
        channel = weighted(rng, CHANNELS)[0]
        discount = "" if rng.random() < 0.30 else rng.choice([0, 0, 5, 10, 15, 20])
        shipping = rng.choice([0.0, 0.0, 4.99, 6.99, 9.99])
        ow.writerow([oid, cust, ts.isoformat(sep=" "), status, channel, discount, shipping, "EUR"])

        subtotal = 0.0
        for _ in range(rng.choice([1, 1, 2, 2, 2, 3, 3, 4])):
            item_id += 1
            p = products[rng.randint(0, N_PRODUCTS - 1)]
            qty = rng.choice([1, 1, 1, 2, 2, 3])
            iw.writerow([item_id, oid, p[0], qty, p[4]])
            subtotal += qty * p[4]
        d = discount if discount != "" else 0
        total = round(subtotal * (1 - d / 100) + shipping, 2)

        pstatus = "failed" if status == "cancelled" else "refunded" if status == "refunded" else "captured"
        provider = weighted(rng, PROVIDERS)[0]
        paid = ts + timedelta(seconds=rng.randint(5, 600))
        pw.writerow([oid, oid, provider, f"{provider[:2]}_{oid:08d}{rng.randint(100, 999)}", total,
                     paid.isoformat(sep=" "), pstatus])
    of.close(); itf.close(); pf.close()
    print(f"Generated {N_CUSTOMERS} customers, {N_PRODUCTS} products, {N_ORDERS} orders, {item_id} order items -> {args.out}")


if __name__ == "__main__":
    main()
