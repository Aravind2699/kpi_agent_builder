"""Intent validation service.

Why this exists:
- Protects calculator from malformed or unsupported intents.
- Verifies both schema-level correctness and value-level correctness against CSV data.
- Provides deterministic rule-based validation for offline operation.
"""

ALLOWED_AGGREGATIONS = {"count", "sum", "average", "ratio"}
ALLOWED_FILTER_COLUMNS = {
    "business_unit",
    "location",
    "event_type",
    "status",
    "priority",
    "impact_type",
}

FILTER_COLUMN_MAP = {
    "status": "event_status",
}


def _apply_common_filters(df, intent):
    working_df = df.copy()
    filters = intent.get("filters", {})

    for key, value in filters.items():
        column = FILTER_COLUMN_MAP.get(key, key)
        if column in working_df.columns:
            working_df = working_df[working_df[column] == value]

    time_period = intent.get("time_period", {})
    period_type = time_period.get("type", "all")
    period_value = time_period.get("value")

    if period_type in {"year", "month", "quarter"} and period_value:
        try:
            period_int = int(str(period_value).strip())
        except (ValueError, TypeError):
            # Return df unfiltered; the period value error is caught in validate_intent.
            return working_df
        if period_type == "year":
            working_df = working_df[working_df["event_date"].dt.year == period_int]
        elif period_type == "month":
            working_df = working_df[working_df["event_date"].dt.month == period_int]
        elif period_type == "quarter":
            working_df = working_df[working_df["event_date"].dt.quarter == period_int]

    return working_df


def validate_intent(intent, df):
    errors = []

    metric_type = intent.get("metric_type")
    if metric_type not in ALLOWED_AGGREGATIONS:
        errors.append(f"Unsupported aggregation type: {metric_type}")

    filters = intent.get("filters", {})
    for key, value in filters.items():
        if key not in ALLOWED_FILTER_COLUMNS:
            errors.append(f"Invalid column: {key}")
            continue
        column = FILTER_COLUMN_MAP.get(key, key)
        if column in df.columns and value not in set(df[column].dropna().unique().tolist()):
            errors.append(f"Invalid value '{value}' for {key}")

    aggregation = intent.get("aggregation", {})

    if metric_type in {"sum", "average"}:
        column = aggregation.get("column")
        if column not in df.columns:
            errors.append(f"Invalid column: {column}")

    if metric_type == "ratio":
        numerator_type = aggregation.get("numerator", {}).get("event_type")
        denominator_type = aggregation.get("denominator", {}).get("event_type")

        valid_event_types = set(df["event_type"].dropna().unique().tolist())
        if numerator_type not in valid_event_types:
            errors.append(f"Invalid value '{numerator_type}' for event_type")
        if denominator_type not in valid_event_types:
            errors.append(f"Invalid value '{denominator_type}' for event_type")

        filtered = _apply_common_filters(df, intent)
        denominator_count = filtered[filtered["event_type"] == denominator_type].shape[0]
        if denominator_count == 0:
            errors.append("Ratio denominator resolves to zero with current filters")

    time_period = intent.get("time_period", {})
    period_type = time_period.get("type", "all")
    period_value = time_period.get("value")
    if period_type not in {"all", "year", "month", "quarter"}:
        errors.append(f"Unsupported time period type: {period_type}")
    if period_type in {"year", "month", "quarter"}:
        if period_value in {None, ""}:
            errors.append(f"Missing time period value for type: {period_type}")
        else:
            try:
                int(str(period_value).strip())
            except (ValueError, TypeError):
                errors.append(
                    f"Invalid time period value '{period_value}' for type '{period_type}'. "
                    "Enter a single integer (e.g. 2026 for year, 1-12 for month, 1-4 for quarter)."
                )

    return {"valid": len(errors) == 0, "errors": errors}
