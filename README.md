# Finance Analytics Platform

A full-stack financial analytics platform built to demonstrate practical **data engineering, Python development, SQL analytics, PostgreSQL, REST APIs, data visualization, performance optimization, and AI integration**.

The platform processes customer, account, and 1M+ financial transaction records and converts them into interactive business and financial insights.

---

# 🚀 Key Features

### Financial Analytics

* Customer, account, and transaction KPIs
* Transaction value and volume analysis
* Daily/monthly transaction trends
* Transaction type analysis
* Channel analysis
* Merchant category analysis
* Account portfolio analysis
* Customer 360 analytics
* Income vs transaction activity
* Transaction risk/threat analysis

### Advanced SQL Analytics

SQL Insights demonstrates practical PostgreSQL techniques including:

* `INNER JOIN` / `LEFT JOIN`
* `GROUP BY`
* Aggregate functions
* `CASE` expressions
* Common Table Expressions (CTEs)
* Subqueries
* Window functions
* Ranking
* Date-based aggregation
* Conditional aggregation
* Customer-level financial analysis
* Account-to-customer relationship analysis

### Python Analytics

Python is used for:

* Data transformation
* Data validation
* ETL processing
* Analytics services
* API development
* Financial calculations
* Backend data processing

Pandas is used primarily during data preparation and transformation, while PostgreSQL handles large-scale database aggregation.

---

# 🏗️ System Architecture

```text
                 Excel Financial Data
                         │
                         ▼
                ┌─────────────────┐
                │   Python ETL    │
                │ Extract         │
                │ Validate        │
                │ Transform       │
                │ Load            │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   PostgreSQL    │
                │                 │
                │ Customers       │
                │ Accounts        │
                │ Transactions    │
                └────────┬────────┘
                         │
                         ▼
             ┌───────────────────────┐
             │ Analytics Serving     │
             │ Tables                │
             │                       │
             │ Daily Analytics       │
             │ Dimension Analytics   │
             │ Customer Analytics    │
             │ Account Analytics     │
             └───────────┬───────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │   FastAPI    │
                  │ REST API     │
                  └──────┬───────┘
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
       Python Insights          SQL Insights
             │                       │
             └───────────┬───────────┘
                         ▼
                 HTML / CSS / JS
                    Plotly.js
                         │
                         ▼
                  Interactive UI

                         +
                         
                   AI Assistant
                         │
                         ▼
                    LLM API
```

The frontend communicates with PostgreSQL **only through the FastAPI backend**.

---

# 📂 Project Structure

```text
finance-analytics-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── analytics.py
│   │   │   ├── customers.py
│   │   │   ├── accounts.py
│   │   │   ├── transactions.py
│   │   │   └── ai.py
│   │   │
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   │
│   │   ├── schemas/
│   │   │   └── analytics.py
│   │   │
│   │   ├── services/
│   │   │   ├── analytics_service.py
│   │   │   ├── sql_service.py
│   │   │   └── ai_service.py
│   │   │
│   │   └── main.py
│   │
│   └── requirements.txt
│
├── data_pipeline/
│   ├── data/raw/
│   ├── extract.py
│   ├── transform.py
│   ├── validate.py
│   ├── load.py
│   ├── build_analytics.py
│   ├── refresh_analytics.py
│   └── run_pipeline.py
│
├── frontend/
│   ├── css/
│   ├── js/
│   │   ├── python-dashboard.js
│   │   └── sql-dashboard.js
│   ├── index.html
│   ├── python-analytics.html
│   ├── sql-analytics.html
│   ├── ai-assistant.html
│   └── about.html
│
├── sql/
│   ├── schema.sql
│   ├── indexes.sql
│   └── analytics_schema.sql
│
├── tests/
├── README.md
└── PERFORMANCE_UPDATE_V4.md
```

---

# 🗄️ Data Model

The core relational model follows:

```text
Customers
    │
    │ customer_id
    ▼
Accounts
    │
    │ account_id
    ▼
Transactions
```

### Customers

Contains customer-level information such as:

* Customer ID
* Demographic attributes
* Occupation
* Annual income
* Join date
* Credit score

### Accounts

Contains:

* Account ID
* Customer ID
* Branch
* Account type
* Balance
* Status
* Open date

### Transactions

Contains:

* Transaction ID
* Account ID
* Transaction date
* Transaction type
* Amount
* Channel
* Merchant category

The database uses **primary keys, foreign keys and indexes** to maintain relational integrity and improve query performance.

---

# ⚙️ ETL & Data Engineering

The project implements a repeatable ETL pipeline:

```text
Extract
   ↓
Validate
   ↓
Transform
   ↓
Load
   ↓
Analytics Build
```

### Extract

Reads the Excel source files using Python.

### Validate

Validates incoming datasets and relationships before loading them into PostgreSQL.

### Transform

Normalizes data types, dates and analytical fields before database insertion.

### Load

Loads the data into PostgreSQL using batch processing.

Large transaction datasets are processed in batches to avoid unnecessarily consuming local or database memory.

### Analytics Build

After the raw tables are loaded, derived analytics tables are generated for high-performance dashboard queries.

---

# ⚡ Performance Engineering

Performance is a major part of the system because the platform processes **1M+ transaction records**.

Instead of repeatedly executing expensive aggregations against the raw transaction table whenever a dashboard loads, the application uses an **analytics serving layer**.

```text
Raw Transaction Data
        ↓
Batch Analytics Processing
        ↓
Precomputed Analytics
        ↓
Fast Dashboard Queries
```

The serving layer contains summarized datasets for:

* Daily transaction activity
* Transaction dimensions
* Customer analytics
* Account analytics

This reduces repeated full-table scans and keeps dashboard API requests lightweight.

### Database Optimization

The project uses:

* PostgreSQL indexes
* Composite indexes
* Foreign-key indexes
* Batch processing
* Pre-aggregation
* Connection-pool controls
* Parameterized queries
* Database-side aggregation
* `ANALYZE` after analytics refresh

The design separates **analytics computation** from **analytics serving**, allowing expensive processing to occur during an analytics refresh rather than during every dashboard request.

---

# 🔌 REST API

FastAPI provides the application API layer.

Example API responsibilities include:

```text
/api/analytics
/api/customers
/api/accounts
/api/transactions
/api/ai
```

The analytics API provides dashboard-ready responses rather than transferring the entire transaction dataset to the browser.

This reduces:

* Database workload
* Network traffic
* Browser processing
* Frontend rendering time

---

# 📊 Python Insights

Python Insights provides an interactive financial analytics dashboard.

### Dashboard Metrics

* Total Customers
* Total Accounts
* Total Transactions
* Total Transaction Amount
* Transaction activity
* Risk/threat indicators

### Visual Analysis

Interactive Plotly.js charts display:

* Transaction trends
* Transaction types
* Channels
* Merchant categories
* Risk levels
* Income/activity relationships

Users can apply analytical filters such as:

```text
Date Range
Transaction Type
Channel
Merchant Category
Account Type
```

---

# 🧮 SQL Insights

SQL Insights focuses on demonstrating practical financial SQL development.

The dashboard uses PostgreSQL to generate:

* Transaction summaries
* Account portfolios
* Customer-level analytics
* Transaction rankings
* Aggregated financial metrics
* Customer 360 views

Example analytical concepts:

```sql
JOIN
GROUP BY
CASE
CTE
WINDOW FUNCTIONS
RANK()
COUNT()
SUM()
AVG()
DATE AGGREGATION
CONDITIONAL AGGREGATION
```

The objective is to demonstrate how SQL can transform normalized financial data into useful business intelligence.

---

# 👤 Customer 360

The Customer 360 feature combines customer, account and transaction information.

Example metrics include:

```text
Customer
 ├── Annual Income
 ├── Credit Score
 ├── Number of Accounts
 ├── Total Balance
 ├── Transaction Count
 ├── Transaction Value
 ├── Average Transaction Value
 └── Transaction Value Rank
```

This provides a consolidated view of customer financial activity without requiring the frontend to perform database joins.

---

# 🤖 AI Assistant

The platform includes a backend-controlled AI Assistant.

```text
User Question
      ↓
Frontend
      ↓
FastAPI
      ↓
Trusted Analytics Context
      ↓
LLM API
      ↓
AI Response
```

The AI service is separated from the frontend so that API credentials are not exposed to the browser.

The design also avoids exposing unrestricted SQL execution through the AI interface.

---

# 🔐 Security & Reliability

The application incorporates basic production-oriented practices:

* Environment-based configuration
* Database credentials stored outside source code
* `.env` excluded from Git
* Parameterized database queries
* Backend-only AI credentials
* CORS configuration
* Input validation
* Relational database constraints
* No direct frontend-to-database connection
* No unrestricted SQL execution endpoint

---

# 🧪 Testing

The project includes automated tests for key application functionality.

Validation includes:

* Python compilation
* Backend tests
* API behavior
* Dashboard JavaScript syntax
* Analytics functionality

The application is designed so that performance improvements do not change the expected analytical results.

---

# ☁️ Deployment

The application is designed for deployment using **GitHub and Render**.

```text
GitHub
  │
  ├── Render Static Site
  │       └── Frontend
  │
  └── Render Web Service
          └── FastAPI
                │
                ▼
          Render PostgreSQL
```

The backend uses Render's internal database connection when deployed, while local development can use the external PostgreSQL connection.

---

# 🛠️ Technology Stack

| Layer           | Technologies                  |
| --------------- | ----------------------------- |
| Frontend        | HTML, CSS, Vanilla JavaScript |
| Visualization   | Plotly.js                     |
| Backend         | Python, FastAPI               |
| Data Processing | Pandas                        |
| Database        | PostgreSQL                    |
| ORM / DB Access | SQLAlchemy, Psycopg           |
| Validation      | Pydantic                      |
| Analytics       | Python + SQL                  |
| AI              | LLM API                       |
| Testing         | Pytest                        |
| Version Control | Git / GitHub                  |
| Deployment      | Render                        |

---

# 🎯 Project Objectives

This project demonstrates practical capability in:

* Financial data analytics
* Python development
* Advanced SQL
* PostgreSQL
* ETL and data pipelines
* REST API development
* Data modeling
* Database optimization
* Analytics serving architecture
* Interactive visualization
* Customer 360 analysis
* AI integration
* Cloud deployment
* Performance engineering

The overall objective is to demonstrate how **financial data, software engineering, data analytics, automation and AI can be combined into a practical production-style analytics application**.
