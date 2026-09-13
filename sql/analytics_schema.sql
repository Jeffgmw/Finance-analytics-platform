CREATE TABLE IF NOT EXISTS analytics_daily_summary (
    txn_date DATE PRIMARY KEY,
    transaction_count BIGINT NOT NULL,
    total_value NUMERIC(24,2) NOT NULL,
    high_count BIGINT NOT NULL,
    high_value NUMERIC(24,2) NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analytics_daily_summary_date ON analytics_daily_summary (txn_date);

CREATE TABLE IF NOT EXISTS analytics_dimension_summary (
    dimension_name VARCHAR(30) NOT NULL,
    dimension_value VARCHAR(120) NOT NULL,
    transaction_count BIGINT NOT NULL,
    total_value NUMERIC(24,2) NOT NULL,
    high_count BIGINT NOT NULL,
    high_value NUMERIC(24,2) NOT NULL,
    PRIMARY KEY (dimension_name, dimension_value)
);
CREATE INDEX IF NOT EXISTS idx_analytics_dimension_name_value ON analytics_dimension_summary (dimension_name, dimension_value);

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
CREATE INDEX IF NOT EXISTS idx_analytics_customer_value ON analytics_customer (total_transaction_value DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_customer_income ON analytics_customer (annual_income);

CREATE TABLE IF NOT EXISTS analytics_account_summary (
    account_type VARCHAR(50),
    status VARCHAR(30),
    account_count BIGINT NOT NULL,
    total_balance NUMERIC(24,2) NOT NULL,
    average_balance NUMERIC(24,2) NOT NULL,
    PRIMARY KEY (account_type, status)
);
