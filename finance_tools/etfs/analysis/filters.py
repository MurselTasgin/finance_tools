# finance_tools/etfs/analysis/filters.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from .types import KeywordFilter


@dataclass
class TitleFilter:
    """Applies include/exclude keyword filtering to DataFrames by `title`."""

    def apply(self, df: pd.DataFrame, keyword_filter: Optional[KeywordFilter]) -> pd.DataFrame:
        if df is None or df.empty or keyword_filter is None:
            return df

        include_keywords = keyword_filter.include_keywords or []
        exclude_keywords = keyword_filter.exclude_keywords or []
        case_sensitive = keyword_filter.case_sensitive
        match_all_includes = keyword_filter.match_all_includes

        working = df.copy()
        title_series = working["title"].fillna("")
        if not case_sensitive:
            title_series = title_series.str.lower()

        # Include filter
        if include_keywords:
            patterns = [kw for kw in include_keywords if kw]
            if not case_sensitive:
                patterns = [kw.lower() for kw in patterns]
            if patterns:
                masks = [title_series.str.contains(kw, regex=False) for kw in patterns]
                include_mask = masks[0]
                for m in masks[1:]:
                    include_mask = include_mask & m if match_all_includes else include_mask | m
                working = working[include_mask]

        # Exclude filter
        if exclude_keywords:
            patterns = [kw for kw in exclude_keywords if kw]
            if not case_sensitive:
                patterns = [kw.lower() for kw in patterns]
            if patterns:
                exclude_mask = pd.Series(False, index=working.index)
                for kw in patterns:
                    exclude_mask = exclude_mask | title_series.str.contains(kw, regex=False)
                working = working[~exclude_mask]

        return working


