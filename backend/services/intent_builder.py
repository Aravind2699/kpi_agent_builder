"""KPI intent builder service.

Why this exists:
- Produces a stable, structured KPI intent contract from user answers.
- Keeps transformation rules isolated from API transport details.
- Enables future migration from rule-based logic to LLM planning.
"""

from services.kpi_parser import generate_description


def _build_filters(answers, metric_type):
    filter_keys = [
        "business_unit",
        "location",
        "event_type",
        "status",
        "priority",
        "impact_type",
    ]
    filters = {}
    for key in filter_keys:
        # Ratio uses numerator/denominator event types as aggregation operands,
        # so do not apply a global event_type filter.
        if metric_type == "ratio" and key == "event_type":
            continue
        value = answers.get(key)
        if key == "status" and not value:
            # Backward compatibility for older clients that still send event_status.
            value = answers.get("event_status")
        if value and value != "All":
            filters[key] = value
    return filters


def _build_time_period(answers):
    period_type = answers.get("time_period_type", "all")
    period_value = answers.get("time_period_value")
    if period_type == "all":
        return {"type": "all", "value": None}
    return {"type": period_type, "value": period_value}


def build_intent(kpi_name, metric_type, answers):
    intent = {
        "kpi_name": kpi_name,
        "metric_type": metric_type,
        "filters": _build_filters(answers, metric_type),
        "time_period": _build_time_period(answers),
    }

    if metric_type == "ratio":
        intent["aggregation"] = {
            "numerator": {
                "type": "count",
                "event_type": answers.get("numerator_event_type"),
            },
            "denominator": {
                "type": "count",
                "event_type": answers.get("denominator_event_type"),
            },
        }
    elif metric_type in {"sum", "average"}:
        intent["aggregation"] = {
            "type": metric_type,
            "column": answers.get("measure_column", "cost_amount"),
        }
    else:
        intent["aggregation"] = {"type": "count", "column": "event_id"}

    intent["description"] = generate_description(intent)

    return intent
