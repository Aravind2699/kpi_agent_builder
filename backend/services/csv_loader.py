"""CSV loader service.

Why this exists:
- Centralizes data loading so all services use the same DataFrame.
- Loads once at module import time so the process never allocates a second copy.
- Keeps views thin and focused on HTTP concerns.
"""

from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "operations_events.csv"

# Load once at import time.  All callers share this single instance.
# lru_cache is intentionally removed: it holds a reference anyway but adds
# overhead; a module-level variable is simpler and equally safe.
_DF: pd.DataFrame | None = None


def load_dataframe() -> pd.DataFrame:
    """Return the shared DataFrame, loading from CSV on first call."""
    global _DF
    if _DF is None:
        df = pd.read_csv(DATA_FILE)
        df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
        _DF = df
    return _DF


def get_column_values(column):
    df = load_dataframe()
    if column not in df.columns:
        return []
    return sorted([v for v in df[column].dropna().unique().tolist()])


def get_schema():
    df = load_dataframe()
    return {
        "columns": df.columns.tolist(),
        "row_count": int(df.shape[0]),
        "date_range": {
            "min": None if df["event_date"].isna().all() else str(df["event_date"].min().date()),
            "max": None if df["event_date"].isna().all() else str(df["event_date"].max().date()),
        },
    }
