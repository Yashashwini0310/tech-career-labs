-- ShopFast core schema (shared by all labs)

CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,
    first_name   TEXT NOT NULL,
    last_name    TEXT NOT NULL,
    email        TEXT NOT NULL UNIQUE,
    country      TEXT NOT NULL,
    city         TEXT NOT NULL,
    signup_date  DATE NOT NULL,
    segment      TEXT NOT NULL
);

CREATE TABLE products (
    product_id  INTEGER PRIMARY KEY,
    sku         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    unit_price  NUMERIC(10,2) NOT NULL,
    cost_price  NUMERIC(10,2) NOT NULL,
    supplier    TEXT NOT NULL,
    active      BOOLEAN NOT NULL
);

CREATE TABLE orders (
    order_id      INTEGER PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    order_ts      TIMESTAMP NOT NULL,
    status        TEXT NOT NULL,
    channel       TEXT NOT NULL,
    discount_pct  INTEGER,              -- NULL means "no discount code used"
    shipping_fee  NUMERIC(10,2) NOT NULL,
    currency      CHAR(3) NOT NULL
);

CREATE TABLE order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(order_id),
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL,
    unit_price     NUMERIC(10,2) NOT NULL
);

CREATE TABLE payments (
    payment_id       INTEGER PRIMARY KEY,
    order_id         INTEGER NOT NULL REFERENCES orders(order_id),
    provider         TEXT NOT NULL,
    provider_txn_id  TEXT NOT NULL,
    amount           NUMERIC(10,2) NOT NULL,
    paid_ts          TIMESTAMP NOT NULL,
    status           TEXT NOT NULL
);

CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_order_ts    ON orders(order_ts);
CREATE INDEX idx_items_order_id     ON order_items(order_id);
CREATE INDEX idx_payments_order_id  ON payments(order_id);
CREATE INDEX idx_payments_paid_ts   ON payments(paid_ts);
