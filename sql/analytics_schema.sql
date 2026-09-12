CREATE TABLE IF NOT EXISTS analytics_daily (
    txn_date DATE NOT NULL,
    txn_type VARCHAR(80),
    channel VARCHAR(80),
    merchant_category VARCHAR(120),
    account_type VARCHAR(50),
    threat_level VARCHAR(10) NOT NULL,
    transaction_count BIGINT NOT NULL,
    total_value NUMERIC(24,2) NOT NULL,
    high_count BIGINT NOT NULL,
    high_value NUMERIC(24,2) NOT NULL,
    PRIMARY KEY (txn_date, txn_type, channel, merchant_category, account_type, threat_level)
);

CREATE INDEX IF NOT EXISTS idx_analytics_daily_date
    ON analytics_daily (txn_date);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_filters
    ON analytics_daily (txn_date, txn_type, channel, merchant_category, account_type);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_channel
    ON analytics_daily (channel, txn_date);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_threat_date
    ON analytics_daily (threat_level, txn_date);

CREATE TABLE IF NOT EXISTS analytics_customer (
    customer_id INTEGER PRIMARY KEY,
    annual_income NUMERIC(15,2),
    credit_score INTEGER,
    account_count BIGINT NOT NULL,
    total_balance NUMERIC(24,2) NOT NULL,
    transaction_count BIGINT NOT NULL,
    total_transaction_value NUMERIC(24,2) NOT NULL,
    average_transaction_value NUMERIC(24,2) NOT NULL,
    transaction_value_rank BIGINT
);

CREATE INDEX IF NOT EXISTS idx_analytics_customer_value
    ON analytics_customer (total_transaction_value DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_customer_income
    ON analytics_customer (annual_income);
