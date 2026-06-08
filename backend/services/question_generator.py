"""Dynamic question generation service.

Why this exists:
- Converts a free-text KPI name into structured interview questions.
- Supports multiple KPI categories (count/sum/average/ratio) without hardcoding one KPI.
- Keeps interpretation and question logic reusable outside HTTP views.
"""

from services.csv_loader import get_column_values
from services.kpi_parser import parse_kpi_name

DIMENSION_OPTIONS = {
    "business_unit": "Business Unit",
    "location": "Location",
    "event_type": "Event Type",
    "status": "Status",
    "priority": "Priority",
    "impact_type": "Impact Type",
}


def infer_description(kpi_name, metric_type):
    descriptions = {
        "count": "Counts matching events after applying selected filters.",
        "sum": "Sums a numeric column for matching events after applying filters.",
        "average": "Computes the average of a numeric column for matching events.",
        "ratio": "Divides one event count by another after applying shared filters.",
    }
    return f"{kpi_name}: {descriptions.get(metric_type, '')}".strip()


def _build_dimension_questions(metric_type):
    questions = []
    for key, label in DIMENSION_OPTIONS.items():
        # Ratio KPIs already define event_type in numerator/denominator.
        # Adding a shared event_type filter can force denominator to zero.
        if metric_type == "ratio" and key == "event_type":
            continue
        option_key = "event_status" if key == "status" else key
        questions.append(
            {
                "id": key,
                "label": f"Select {label}",
                "type": "single_select",
                "required": False,
                "allow_all": True,
                "options": ["All"] + [str(v) for v in get_column_values(option_key)],
            }
        )

    # Time period is always relevant and keeps stateful filtering consistent.
    questions.append(
        {
            "id": "time_period_type",
            "label": "Select Time Period Granularity",
            "type": "single_select",
            "required": True,
            "allow_all": False,
            "options": ["all", "year", "month", "quarter"],
        }
    )

    if metric_type in {"sum", "average"}:
        questions.append(
            {
                "id": "measure_column",
                "label": "Select Numeric Measure Column",
                "type": "single_select",
                "required": True,
                "allow_all": False,
                "options": ["cost_amount", "processing_hours", "customer_count"],
            }
        )

    if metric_type == "ratio":
        event_type_options = [str(v) for v in get_column_values("event_type")]
        questions.insert(
            0,
            {
                "id": "numerator_event_type",
                "label": "Select Numerator Event Type",
                "type": "single_select",
                "required": True,
                "allow_all": False,
                "options": event_type_options,
            },
        )
        questions.insert(
            1,
            {
                "id": "denominator_event_type",
                "label": "Select Denominator Event Type",
                "type": "single_select",
                "required": True,
                "allow_all": False,
                "options": event_type_options,
            },
        )

    return questions


def generate_questions(kpi_name):
    parsed = parse_kpi_name(kpi_name)
    metric_type = parsed["metric_type"]

    # Propagate None metric_type to caller; the view rejects it with a 400.
    if metric_type is None:
        return {
            "metric_type": None,
            "description": "",
            "default_measure_column": "cost_amount",
            "interpretation": parsed["interpretation"],
            "default_answers": {},
            "questions": [],
        }

    default_answers = {}

    if metric_type == "ratio":
        numerator = parsed["parsed_operands"].get("numerator_event_type")
        denominator = parsed["parsed_operands"].get("denominator_event_type")
        if numerator:
            default_answers["numerator_event_type"] = numerator
        if denominator:
            default_answers["denominator_event_type"] = denominator

    elif metric_type == "count":
        # Pre-select dropdown defaults from parsed hints so user sees
        # confirmable values rather than blank selects.
        hints = parsed["parsed_operands"]
        if hints.get("event_type"):
            default_answers["event_type"] = hints["event_type"]
        if hints.get("priority"):
            default_answers["priority"] = hints["priority"]
        if hints.get("status"):
            default_answers["status"] = hints["status"]

    return {
        "metric_type": metric_type,
        "description": infer_description(kpi_name, metric_type),
        "default_measure_column": parsed["default_measure_column"],
        "interpretation": parsed["interpretation"],
        "default_answers": default_answers,
        "questions": _build_dimension_questions(metric_type),
    }
