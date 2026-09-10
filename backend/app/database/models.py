from sqlalchemy import BigInteger, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str | None] = mapped_column(String(150))
    gender: Mapped[str | None] = mapped_column(String(30))
    date_of_birth: Mapped[object | None] = mapped_column(Date)
    city: Mapped[str | None] = mapped_column(String(100))
    state: Mapped[str | None] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(255))
    occupation: Mapped[str | None] = mapped_column(String(100))
    annual_income: Mapped[object | None] = mapped_column(Numeric(15, 2))
    join_date: Mapped[object | None] = mapped_column(Date)
    credit_score: Mapped[int | None] = mapped_column(Integer)


class Account(Base):
    __tablename__ = "accounts"
    account_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.customer_id"), nullable=False
    )
    branch_id: Mapped[int | None] = mapped_column(Integer)
    account_type: Mapped[str | None] = mapped_column(String(50))
    balance: Mapped[object | None] = mapped_column(Numeric(18, 2))
    open_date: Mapped[object | None] = mapped_column(Date)
    status: Mapped[str | None] = mapped_column(String(30))


class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.account_id"), nullable=False
    )
    txn_date: Mapped[object | None] = mapped_column(Date)
    txn_type: Mapped[str | None] = mapped_column(String(80))
    amount: Mapped[object | None] = mapped_column(Numeric(18, 2))
    channel: Mapped[str | None] = mapped_column(String(80))
    merchant_category: Mapped[str | None] = mapped_column(String(120))
