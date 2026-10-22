"""
ShopFast Orders API
-------------------
Internal API used by the ShopFast website, mobile app and partner integrations.

Endpoints
  GET  /health                         liveness + database check
  GET  /api/orders/<order_id>          order with items and totals
  GET  /api/customers/<id>/orders      a customer's order history
  GET  /api/products/<product_id>      product details
  GET  /api/reports/daily-sales?date=YYYY-MM-DD   finance report
  POST /api/orders                     create an order (partners, needs X-API-Key)
"""
import logging
import os
import time
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from flask import Flask, g, jsonify, request

DB_DSN = os.environ.get("DB_DSN", "host=db dbname=shop user=shop_app password=shop_app_pw")
API_KEY = os.environ.get("API_KEY", "")
LOG_FILE = os.environ.get("LOG_FILE", "/var/log/shopfast/app.log")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
log = logging.getLogger("orders-api")

app = Flask(__name__)

# Reports are expensive, so keep their connections around for re-use.
_report_connections = []


def get_conn():
    return psycopg.connect(DB_DSN, row_factory=dict_row, connect_timeout=5)


def money(x):
    return float(Decimal(str(x)).quantize(Decimal("0.01")))


@app.before_request
def _start_timer():
    g.start = time.time()


@app.after_request
def _log_request(resp):
    ms = (time.time() - g.start) * 1000
    log.info("%s %s -> %s in %.1fms", request.method, request.path, resp.status_code, ms)
    return resp


@app.errorhandler(Exception)
def _unhandled(e):
    log.exception("Unhandled error on %s %s", request.method, request.path)
    return jsonify(error="internal_error", detail=str(e)), 500


@app.get("/health")
def health():
    with get_conn() as conn:
        conn.execute("SELECT 1")
    return jsonify(status="ok")


@app.get("/api/orders/<int:order_id>")
def get_order(order_id):
    with get_conn() as conn:
        order = conn.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,)).fetchone()
        if not order:
            return jsonify(error="not_found"), 404
        items = conn.execute(
            "SELECT product_id, quantity, unit_price FROM order_items WHERE order_id = %s ORDER BY order_item_id",
            (order_id,),
        ).fetchall()

    subtotal = sum(Decimal(i["quantity"]) * i["unit_price"] for i in items)
    discount_amount = subtotal * order["discount_pct"] / 100
    total = subtotal - discount_amount + order["shipping_fee"]
    return jsonify(
        order_id=order["order_id"],
        customer_id=order["customer_id"],
        status=order["status"],
        order_ts=order["order_ts"].isoformat(),
        items=[{"product_id": i["product_id"], "quantity": i["quantity"], "unit_price": money(i["unit_price"])} for i in items],
        subtotal=money(subtotal),
        discount=money(discount_amount),
        shipping_fee=money(order["shipping_fee"]),
        total=money(total),
    )


@app.get("/api/customers/<int:customer_id>/orders")
def customer_orders(customer_id):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT order_id, order_ts, status, channel FROM orders WHERE customer_id = %s ORDER BY order_ts DESC",
            (customer_id,),
        ).fetchall()
    return jsonify(customer_id=customer_id, count=len(rows),
                   orders=[{**r, "order_ts": r["order_ts"].isoformat()} for r in rows])


@app.get("/api/products/<int:product_id>")
def get_product(product_id):
    with get_conn() as conn:
        p = conn.execute("SELECT * FROM products WHERE product_id = %s", (product_id,)).fetchone()
    if not p:
        return jsonify(error="not_found"), 404
    return jsonify({**p, "unit_price": money(p["unit_price"]), "cost_price": money(p["cost_price"])})


@app.get("/api/reports/daily-sales")
def daily_sales():
    day = request.args.get("date")
    if not day:
        return jsonify(error="date query parameter required, e.g. ?date=2026-10-05"), 400
    conn = get_conn()
    _report_connections.append(conn)
    row = conn.execute(
        """SELECT COUNT(*) AS payments, COALESCE(SUM(amount), 0) AS revenue
           FROM payments WHERE status = 'captured' AND paid_ts::date = %s""",
        (day,),
    ).fetchone()
    return jsonify(date=day, payments=row["payments"], revenue=money(row["revenue"]))


@app.post("/api/orders")
def create_order():
    if request.headers.get("X-API-Key") != API_KEY:
        log.warning("Rejected order: invalid API key from %s", request.remote_addr)
        return jsonify(error="unauthorized"), 401
    body = request.get_json(silent=True) or {}
    items = body.get("items") or []
    if not body.get("customer_id") or not items:
        return jsonify(error="customer_id and items are required"), 400
    with get_conn() as conn:
        with conn.transaction():
            oid = conn.execute(
                """INSERT INTO orders (order_id, customer_id, order_ts, status, channel, discount_pct, shipping_fee, currency)
                   VALUES ((SELECT COALESCE(MAX(order_id), 0) + 1 FROM orders), %s, NOW(), 'placed', 'marketplace', NULL, 0, 'EUR')
                   RETURNING order_id""",
                (body["customer_id"],),
            ).fetchone()["order_id"]
            for it in items:
                price = conn.execute("SELECT unit_price FROM products WHERE product_id = %s", (it["product_id"],)).fetchone()
                if not price:
                    raise ValueError(f"unknown product {it['product_id']}")
                conn.execute(
                    """INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
                       VALUES ((SELECT COALESCE(MAX(order_item_id), 0) + 1 FROM order_items), %s, %s, %s, %s)""",
                    (oid, it["product_id"], it.get("quantity", 1), price["unit_price"]),
                )
    log.info("Created order %s for customer %s", oid, body["customer_id"])
    return jsonify(order_id=oid, status="placed"), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
