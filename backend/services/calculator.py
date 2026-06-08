"""KPI calculation engine with strategy pattern.

Why this exists:
- Separates metric-specific math into clear strategies.
- Supports extension for new KPI types without changing API views.
- Guarantees all calculations use pandas from the CSV source only.
"""

from abc import ABC, abstractmethod

from services.status_engine import compute_status


FILTER_COLUMN_MAP = {
    "status": "event_status",
}


def _filter_clauses(intent):
    filters = intent.get("filters", {})
    clauses = []
    for key, value in filters.items():
        if value in (None, "", "All"):
            continue
        clauses.append(f"{key}='{value}'")
    return clauses


def _with_where(base_formula, intent):
    clauses = _filter_clauses(intent)
    if not clauses:
        return base_formula
    return f"{base_formula[:-1]} WHERE {' AND '.join(clauses)})"


class BaseStrategy(ABC):
    @abstractmethod
    def execute(self, df, intent):
        raise NotImplementedError


def _apply_filters(df, intent):
    filtered = df.copy()
    filters = intent.get("filters", {})

    for key, value in filters.items():
        column = FILTER_COLUMN_MAP.get(key, key)
        filtered = filtered[filtered[column] == value]

    period = intent.get("time_period", {})
    period_type = period.get("type", "all")
    period_value = period.get("value")

    if period_type in {"year", "month", "quarter"} and period_value:
        try:
            period_int = int(str(period_value).strip())
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid time period value '{period_value}' for type '{period_type}'. "
                "Please enter a single integer (e.g. 2026 for year, 1-12 for month, 1-4 for quarter)."
            )
        if period_type == "year":
            filtered = filtered[filtered["event_date"].dt.year == period_int]
        elif period_type == "month":
            filtered = filtered[filtered["event_date"].dt.month == period_int]
        elif period_type == "quarter":
            filtered = filtered[filtered["event_date"].dt.quarter == period_int]

    return filtered


class CountStrategy(BaseStrategy):
    def execute(self, df, intent):
        filtered = _apply_filters(df, intent)
        value = int(filtered.shape[0])

        event_type_filter = intent.get("filters", {}).get("event_type")
        base_formula = f"COUNT({event_type_filter})" if event_type_filter else "COUNT(events)"
        formula = _with_where(base_formula, intent)

        return {
            "value": value,
            "formula": formula,
            "unit": "count",
            "numerator": None,
            "denominator": None,
        }


class SumStrategy(BaseStrategy):
    def execute(self, df, intent):
        filtered = _apply_filters(df, intent)
        column = intent["aggregation"]["column"]
        value = float(filtered[column].fillna(0).sum())
        return {
            "value": value,
            "formula": _with_where(f"SUM({column})", intent),
            "unit": column,
            "numerator": None,
            "denominator": None,
        }


class AverageStrategy(BaseStrategy):
    def execute(self, df, intent):
        filtered = _apply_filters(df, intent)
        column = intent["aggregation"]["column"]
        value = float(filtered[column].fillna(0).mean()) if filtered.shape[0] else 0.0
        return {
            "value": value,
            "formula": _with_where(f"AVG({column})", intent),
            "unit": column,
            "numerator": None,
            "denominator": None,
        }


class RatioStrategy(BaseStrategy):
    def execute(self, df, intent):
        filtered = _apply_filters(df, intent)
        numerator_type = intent["aggregation"]["numerator"]["event_type"]
        denominator_type = intent["aggregation"]["denominator"]["event_type"]

        numerator = int(filtered[filtered["event_type"] == numerator_type].shape[0])
        denominator = int(filtered[filtered["event_type"] == denominator_type].shape[0])

        # Guard against zero-division explicitly — validator should prevent this,
        # but strategy must also be safe if called directly.
        if denominator == 0:
            raise ZeroDivisionError(
                f"Denominator event type '{denominator_type}' has zero matching rows "
                "with the applied filters and time period."
            )

        value = round(float(numerator / denominator), 4)

        return {
            "value": value,
            "formula": (
                f"{_with_where(f'COUNT({numerator_type})', intent)} / "
                f"{_with_where(f'COUNT({denominator_type})', intent)}"
            ),
            "unit": "ratio",
            "numerator": numerator,
            "denominator": denominator,
        }


STRATEGIES = {
    "count": CountStrategy(),
    "sum": SumStrategy(),
    "average": AverageStrategy(),
    "ratio": RatioStrategy(),
}


def calculate_kpi(df, intent):
    metric_type = intent.get("metric_type")
    if metric_type not in STRATEGIES:
        raise ValueError(f"Unsupported metric_type: '{metric_type}'. Allowed: {list(STRATEGIES.keys())}")

    strategy = STRATEGIES[metric_type]
    try:
        payload = strategy.execute(df, intent)
    except ZeroDivisionError as exc:
        raise ZeroDivisionError(str(exc)) from exc
    except KeyError as exc:
        raise ValueError(f"Intent is missing required field: {exc}") from exc

    status_result = compute_status(metric_type, payload["value"])

    return {
        "kpi_name": intent.get("kpi_name"),
        "description": intent.get("description", ""),
        "value": None if payload["value"] is None else round(payload["value"], 2),
        "formula": payload["formula"],
        "numerator": payload["numerator"],
        "denominator": payload["denominator"],
        "unit": payload["unit"],
        "status": status_result["status"],
        "status_reason": status_result["reason"],
    }
