-- Task 4: restore the missing index
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
-- Task 6: remove duplicate payments (keep the first row) and prevent it happening again
DELETE FROM payments a USING payments b
WHERE a.provider_txn_id = b.provider_txn_id AND a.payment_id > b.payment_id;
ALTER TABLE payments ADD CONSTRAINT uq_payments_provider_txn_id UNIQUE (provider_txn_id);
