# finance_tools/etfs/tefas/models.py
"""
SQLAlchemy ORM models for TEFAS ETF data.

- `TefasFundInfo`: General info per fund per date
- `TefasFundBreakdown`: Portfolio allocation breakdown per fund per date

Schema mirrors `InfoSchema` and `BreakdownSchema` fields.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TefasFundInfo(Base):
    __tablename__ = "tefas_fund_info"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[Optional[float]] = mapped_column(Float)
    title: Mapped[Optional[str]] = mapped_column(String(256))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    number_of_shares: Mapped[Optional[float]] = mapped_column(Float)
    number_of_investors: Mapped[Optional[float]] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("date", "code", name="uq_info_date_code"),
        Index("ix_info_code_date", "code", "date"),
    )


class TefasFundBreakdown(Base):
    __tablename__ = "tefas_fund_breakdown"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    code: Mapped[str] = mapped_column(String(16), index=True)

    bank_bills: Mapped[Optional[float]] = mapped_column(Float)
    exchange_traded_fund: Mapped[Optional[float]] = mapped_column(Float)
    other: Mapped[Optional[float]] = mapped_column(Float)
    fx_payable_bills: Mapped[Optional[float]] = mapped_column(Float)
    government_bond: Mapped[Optional[float]] = mapped_column(Float)
    foreign_currency_bills: Mapped[Optional[float]] = mapped_column(Float)
    eurobonds: Mapped[Optional[float]] = mapped_column(Float)
    commercial_paper: Mapped[Optional[float]] = mapped_column(Float)
    fund_participation_certificate: Mapped[Optional[float]] = mapped_column(Float)
    real_estate_certificate: Mapped[Optional[float]] = mapped_column(Float)
    venture_capital_investment_fund_participation: Mapped[Optional[float]] = mapped_column(Float)
    real_estate_investment_fund_participation: Mapped[Optional[float]] = mapped_column(Float)
    treasury_bill: Mapped[Optional[float]] = mapped_column(Float)
    stock: Mapped[Optional[float]] = mapped_column(Float)
    government_bonds_and_bills_fx: Mapped[Optional[float]] = mapped_column(Float)
    participation_account: Mapped[Optional[float]] = mapped_column(Float)
    participation_account_au: Mapped[Optional[float]] = mapped_column(Float)
    participation_account_d: Mapped[Optional[float]] = mapped_column(Float)
    participation_account_tl: Mapped[Optional[float]] = mapped_column(Float)
    government_lease_certificates: Mapped[Optional[float]] = mapped_column(Float)
    government_lease_certificates_d: Mapped[Optional[float]] = mapped_column(Float)
    government_lease_certificates_tl: Mapped[Optional[float]] = mapped_column(Float)
    government_lease_certificates_foreign: Mapped[Optional[float]] = mapped_column(Float)
    precious_metals: Mapped[Optional[float]] = mapped_column(Float)
    precious_metals_byf: Mapped[Optional[float]] = mapped_column(Float)
    precious_metals_kba: Mapped[Optional[float]] = mapped_column(Float)
    precious_metals_kks: Mapped[Optional[float]] = mapped_column(Float)
    public_domestic_debt_instruments: Mapped[Optional[float]] = mapped_column(Float)
    private_sector_lease_certificates: Mapped[Optional[float]] = mapped_column(Float)
    private_sector_bond: Mapped[Optional[float]] = mapped_column(Float)
    repo: Mapped[Optional[float]] = mapped_column(Float)
    derivatives: Mapped[Optional[float]] = mapped_column(Float)
    tmm: Mapped[Optional[float]] = mapped_column(Float)
    reverse_repo: Mapped[Optional[float]] = mapped_column(Float)
    asset_backed_securities: Mapped[Optional[float]] = mapped_column(Float)
    term_deposit: Mapped[Optional[float]] = mapped_column(Float)
    term_deposit_au: Mapped[Optional[float]] = mapped_column(Float)
    term_deposit_d: Mapped[Optional[float]] = mapped_column(Float)
    term_deposit_tl: Mapped[Optional[float]] = mapped_column(Float)
    futures_cash_collateral: Mapped[Optional[float]] = mapped_column(Float)
    foreign_debt_instruments: Mapped[Optional[float]] = mapped_column(Float)
    foreign_domestic_debt_instruments: Mapped[Optional[float]] = mapped_column(Float)
    foreign_private_sector_debt_instruments: Mapped[Optional[float]] = mapped_column(Float)
    foreign_exchange_traded_funds: Mapped[Optional[float]] = mapped_column(Float)
    foreign_equity: Mapped[Optional[float]] = mapped_column(Float)
    foreign_securities: Mapped[Optional[float]] = mapped_column(Float)
    foreign_investment_fund_participation_shares: Mapped[Optional[float]] = mapped_column(Float)
    private_sector_international_lease_certificate: Mapped[Optional[float]] = mapped_column(Float)
    private_sector_foreign_debt_instruments: Mapped[Optional[float]] = mapped_column(Float)

    __table_args__ = (
        UniqueConstraint("date", "code", name="uq_breakdown_date_code"),
        Index("ix_breakdown_code_date", "code", "date"),
    )


