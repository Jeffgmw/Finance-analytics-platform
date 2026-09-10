CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    name VARCHAR(150),
    gender VARCHAR(30),
    date_of_birth DATE,
    city VARCHAR(100),
    state VARCHAR(100),
    phone VARCHAR(30),
    email VARCHAR(255),
    occupation VARCHAR(100),
    annual_income NUMERIC(15,2),
    join_date DATE,
    credit_score INTEGER
);

CREATE TABLE IF NOT EXISTS accounts (
    account_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    branch_id INTEGER,
    account_type VARCHAR(50),
    balance NUMERIC(18,2),
    open_date DATE,
    status VARCHAR(30)
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id BIGINT PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES accounts(account_id),
    txn_date DATE,
    txn_type VARCHAR(80),
    amount NUMERIC(18,2),
    channel VARCHAR(80),
    merchant_category VARCHAR(120)
);
