# finance_tools/etfs/tefas/repository.py
"""
Repository and database utilities for TEFAS ETF data using SQLAlchemy ORM.

Abstractions:
- DatabaseEngineProvider: creates engine/session based on centralized config
- TefasRepository: upsert and query methods for `TefasFundInfo` and `TefasFundBreakdown`

This module contains no vendor-specific code in the main components, relying
on the central `finance_tools.config` for database URL building.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple
from datetime import date

from sqlalchemy import create_engine, select, inspect, or_, and_, not_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError

from ...config import get_config
from ...logging import get_logger
from .models import Base, TefasFundInfo, TefasFundBreakdown


class DatabaseEngineProvider:
    """Factory for SQLAlchemy engine and sessions using central config."""

    def __init__(self):
        self.config = get_config()
        self.logger = get_logger("db")
        self._engine = None
        self._SessionLocal = None

    def get_engine(self):
        if self._engine is None:
            db_url = self.config.get_database_url()
            echo = bool(self.config.get("DATABASE_ECHO", False))
            self.logger.info(f"Initializing database engine: {db_url}")
            self._engine = create_engine(db_url, echo=echo, future=True)
        return self._engine

    def get_session_factory(self):
        if self._SessionLocal is None:
            engine = self.get_engine()
            self._SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
        return self._SessionLocal

    def create_all(self) -> None:
        engine = self.get_engine()
        Base.metadata.create_all(engine)

    def is_initialized(self) -> bool:
        """Check whether all required tables exist in the database."""
        engine = self.get_engine()
        inspector = inspect(engine)
        required_tables = [
            TefasFundInfo.__tablename__,
            TefasFundBreakdown.__tablename__,
        ]
        return all(inspector.has_table(t) for t in required_tables)

    def ensure_initialized(self) -> None:
        """Create tables only if they are missing."""
        if not self.is_initialized():
            self.create_all()


class TefasRepository:
    """Repository for storing and querying TEFAS fund info and breakdown data."""

    def __init__(self, session: Session):
        self.session = session
        self.logger = get_logger("tefas_repo")

    # Upsert helpers
    def upsert_fund_info_many(self, rows: Iterable[dict]) -> int:
        """Upsert many rows into `tefas_fund_info`. Returns number of inserted/updated rows."""
        count = 0
        for r in rows:
            obj = TefasFundInfo(
                date=r.get("date"),
                code=r.get("code"),
                price=r.get("price"),
                title=r.get("title"),
                market_cap=r.get("market_cap"),
                number_of_shares=r.get("number_of_shares"),
                number_of_investors=r.get("number_of_investors"),
            )
            try:
                self.session.add(obj)
                self.session.commit()
                count += 1
            except IntegrityError:
                self.session.rollback()
                # Update existing row on unique constraint conflict (date, code)
                existing = self.session.execute(
                    select(TefasFundInfo).where(
                        (TefasFundInfo.date == obj.date) & (TefasFundInfo.code == obj.code)
                    )
                ).scalar_one()

                existing.price = obj.price
                existing.title = obj.title
                existing.market_cap = obj.market_cap
                existing.number_of_shares = obj.number_of_shares
                existing.number_of_investors = obj.number_of_investors
                self.session.commit()
                count += 1
        return count

    def upsert_breakdown_many(self, rows: Iterable[dict]) -> int:
        count = 0
        for r in rows:
            obj = TefasFundBreakdown(**r)
            try:
                self.session.add(obj)
                self.session.commit()
                count += 1
            except IntegrityError:
                self.session.rollback()
                existing = self.session.execute(
                    select(TefasFundBreakdown).where(
                        (TefasFundBreakdown.date == obj.date) & (TefasFundBreakdown.code == obj.code)
                    )
                ).scalar_one()

                # Update all float fields from r
                for key, value in r.items():
                    if key in {"date", "code"}:
                        continue
                    setattr(existing, key, value)
                self.session.commit()
                count += 1
        return count

    # Queries
    def get_fund_info(self, code: str, start: Optional[date] = None, end: Optional[date] = None) -> List[TefasFundInfo]:
        stmt = select(TefasFundInfo).where(TefasFundInfo.code == code)
        if start is not None:
            stmt = stmt.where(TefasFundInfo.date >= start)
        if end is not None:
            stmt = stmt.where(TefasFundInfo.date <= end)
        stmt = stmt.order_by(TefasFundInfo.date.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_breakdown(self, code: str, on_date: Optional[date] = None) -> List[TefasFundBreakdown]:
        stmt = select(TefasFundBreakdown).where(TefasFundBreakdown.code == code)
        if on_date is not None:
            stmt = stmt.where(TefasFundBreakdown.date == on_date)
        stmt = stmt.order_by(TefasFundBreakdown.date.asc())
        return list(self.session.execute(stmt).scalars().all())

    def query_fund_info(
        self,
        codes: Optional[List[str]] = None,
        start: Optional[date] = None,
        end: Optional[date] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        case_sensitive: bool = False,
        match_all_includes: bool = False,
    ) -> List[TefasFundInfo]:
        """Flexible query for `TefasFundInfo` with optional filters.

        - codes: restrict to these fund codes
        - start/end: date range inclusive
        - include_keywords: title must include any/all of these (controlled by match_all_includes)
        - exclude_keywords: title must not include any of these
        - case_sensitive: whether keyword matching is case sensitive
        """
        stmt = select(TefasFundInfo)
        if codes:
            stmt = stmt.where(TefasFundInfo.code.in_(codes))
        if start is not None:
            stmt = stmt.where(TefasFundInfo.date >= start)
        if end is not None:
            stmt = stmt.where(TefasFundInfo.date <= end)

        # Title filters
        title_col = TefasFundInfo.title
        if include_keywords:
            patterns = []
            for kw in include_keywords:
                if kw is None or kw == "":
                    continue
                if case_sensitive:
                    patterns.append(title_col.like(f"%{kw}%"))
                else:
                    patterns.append(func.lower(title_col).like(f"%{kw.lower()}%"))
            if patterns:
                include_clause = and_(*patterns) if match_all_includes else or_(*patterns)
                # Ensure title is not NULL for inclusion
                stmt = stmt.where(and_(title_col.is_not(None), include_clause))

        if exclude_keywords:
            patterns = []
            for kw in exclude_keywords:
                if kw is None or kw == "":
                    continue
                if case_sensitive:
                    patterns.append(title_col.like(f"%{kw}%"))
                else:
                    patterns.append(func.lower(title_col).like(f"%{kw.lower()}%"))
            if patterns:
                stmt = stmt.where(or_(title_col.is_(None), not_(or_(*patterns))))

        stmt = stmt.order_by(TefasFundInfo.code.asc(), TefasFundInfo.date.asc())
        return list(self.session.execute(stmt).scalars().all())

    def get_total_records_count(self) -> int:
        """Get total number of records in the database."""
        stmt = select(func.count(TefasFundInfo.id))
        return self.session.execute(stmt).scalar() or 0

    def get_unique_funds_count(self) -> int:
        """Get number of unique fund codes."""
        stmt = select(func.count(func.distinct(TefasFundInfo.code)))
        return self.session.execute(stmt).scalar() or 0

    def get_date_range(self) -> dict:
        """Get the date range of available data."""
        stmt = select(
            func.min(TefasFundInfo.date).label("start"),
            func.max(TefasFundInfo.date).label("end")
        )
        result = self.session.execute(stmt).first()
        return {
            "start": result.start if result else None,
            "end": result.end if result else None,
        }

    def get_last_download_date(self) -> Optional[date]:
        """Get the date of the most recent record."""
        stmt = select(func.max(TefasFundInfo.date))
        return self.session.execute(stmt).scalar()

    def get_paginated_records(
        self,
        page: int = 1,
        page_size: int = 50,
        search: str = "",
        sort_by: Optional[str] = None,
        sort_dir: str = "asc",
        filters: Optional[List[dict]] = None,
    ) -> Tuple[List[TefasFundInfo], int]:
        """Get paginated records with filtering and sorting."""
        stmt = select(TefasFundInfo)
        
        # Apply search
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    TefasFundInfo.code.like(search_term),
                    TefasFundInfo.title.like(search_term),
                )
            )
        
        # Apply filters
        if filters:
            for filter_cond in filters:
                column = filter_cond.get("column")
                operator = filter_cond.get("operator")
                value = filter_cond.get("value")
                value2 = filter_cond.get("value2")
                
                if not column or not operator or value is None:
                    continue
                
                # Get the column attribute
                column_attr = getattr(TefasFundInfo, column, None)
                if column_attr is None:
                    continue
                
                # Apply filter based on operator
                if operator == "equals":
                    if isinstance(value, str) and value.isdigit():
                        stmt = stmt.where(column_attr == int(value))
                    else:
                        stmt = stmt.where(column_attr == value)
                elif operator == "contains":
                    stmt = stmt.where(column_attr.like(f"%{value}%"))
                elif operator == "greater_than":
                    if isinstance(value, str) and value.replace(".", "").isdigit():
                        stmt = stmt.where(column_attr > float(value))
                    else:
                        stmt = stmt.where(column_attr > value)
                elif operator == "less_than":
                    if isinstance(value, str) and value.replace(".", "").isdigit():
                        stmt = stmt.where(column_attr < float(value))
                    else:
                        stmt = stmt.where(column_attr < value)
                elif operator == "between" and value2 is not None:
                    if isinstance(value, str) and value.replace(".", "").isdigit():
                        stmt = stmt.where(
                            and_(
                                column_attr >= float(value),
                                column_attr <= float(value2)
                            )
                        )
                    else:
                        stmt = stmt.where(
                            and_(
                                column_attr >= value,
                                column_attr <= value2
                            )
                        )
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0
        
        # Apply sorting
        if sort_by:
            column_attr = getattr(TefasFundInfo, sort_by, None)
            if column_attr is not None:
                if sort_dir.lower() == "desc":
                    stmt = stmt.order_by(column_attr.desc())
                else:
                    stmt = stmt.order_by(column_attr.asc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        
        records = list(self.session.execute(stmt).scalars().all())
        return records, total

    def get_plot_data(
        self,
        x_column: str,
        y_column: str,
        filters: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Get data for plotting with optional filters."""
        # Get column attributes
        x_attr = getattr(TefasFundInfo, x_column, None)
        y_attr = getattr(TefasFundInfo, y_column, None)
        
        if x_attr is None or y_attr is None:
            return []
        
        stmt = select(x_attr, y_attr)
        
        # Apply filters (same logic as get_paginated_records)
        if filters:
            for filter_cond in filters:
                column = filter_cond.get("column")
                operator = filter_cond.get("operator")
                value = filter_cond.get("value")
                value2 = filter_cond.get("value2")
                
                if not column or not operator or value is None:
                    continue
                
                column_attr = getattr(TefasFundInfo, column, None)
                if column_attr is None:
                    continue
                
                if operator == "equals":
                    if isinstance(value, str) and value.isdigit():
                        stmt = stmt.where(column_attr == int(value))
                    else:
                        stmt = stmt.where(column_attr == value)
                elif operator == "contains":
                    stmt = stmt.where(column_attr.like(f"%{value}%"))
                elif operator == "greater_than":
                    if isinstance(value, str) and value.replace(".", "").isdigit():
                        stmt = stmt.where(column_attr > float(value))
                    else:
                        stmt = stmt.where(column_attr > value)
                elif operator == "less_than":
                    if isinstance(value, str) and value.replace(".", "").isdigit():
                        stmt = stmt.where(column_attr < float(value))
                    else:
                        stmt = stmt.where(column_attr < value)
                elif operator == "between" and value2 is not None:
                    if isinstance(value, str) and value.replace(".", "").isdigit():
                        stmt = stmt.where(
                            and_(
                                column_attr >= float(value),
                                column_attr <= float(value2)
                            )
                        )
                    else:
                        stmt = stmt.where(
                            and_(
                                column_attr >= value,
                                column_attr <= value2
                            )
                        )
        
        # Filter out null values
        stmt = stmt.where(
            and_(
                x_attr.is_not(None),
                y_attr.is_not(None)
            )
        )
        
        # Limit results for performance
        stmt = stmt.limit(10000)
        
        results = self.session.execute(stmt).all()
        
        plot_data = []
        for row in results:
            x_val = row[0]
            y_val = row[1]
            
            # Convert dates to strings for JSON serialization
            if hasattr(x_val, 'isoformat'):
                x_val = x_val.isoformat()
            if hasattr(y_val, 'isoformat'):
                y_val = y_val.isoformat()
            
            plot_data.append({
                "x": x_val,
                "y": float(y_val) if y_val is not None else 0,
                "label": f"{x_val}: {y_val}"
            })
        
        return plot_data


