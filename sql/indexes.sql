CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_accounts_type ON accounts(account_type);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(txn_date);
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(txn_type);
CREATE INDEX IF NOT EXISTS idx_transactions_channel ON transactions(channel);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant_category ON transactions(merchant_category);
