"""Deterministic KPI parser.

Why this exists:
- Parses KPI name into deterministic hints without using an LLM.
- Never substitutes unknown event types with guessed values.
- Produces interpretation text for the UI step-by-step agent flow.
- Returns None metric_type for unrecognised KPI names so callers can reject them.
"""

import re

from services.csv_loader import get_column_values

# Explicit keyword sets for each metric type.
# Unknown KPI names that match none of these are rejected - never guessed.
_RATIO_KEYWORDS = {"ratio"}
_AVERAGE_KEYWORDS = {"average", "avg"}
_SUM_KEYWORDS = {"total", "sum"}
_COUNT_KEYWORDS = {"count"}


def infer_metric_type(kpi_name):
    """Return metric_type string or None if the name is unrecognised.

    Rules (in priority order):
      ratio   - contains 'ratio' OR matches '<X> / <Y>'
      average - contains 'average' or 'avg'
      sum     - contains 'total' or 'sum'
      count   - contains 'count'
      None    - none of the above matched (caller must reject the input)
    """
    text = (kpi_name or "").strip().lower()
    if not text:
        return None
    if any(kw in text for kw in _RATIO_KEYWORDS):
        return "ratio"
    if "/" in text:
        return "ratio"
    if any(kw in text for kw in _AVERAGE_KEYWORDS):
        return "average"
    if any(kw in text for kw in _SUM_KEYWORDS):
        return "sum"
    if any(kw in text for kw in _COUNT_KEYWORDS):
        return "count"
    return None


def infer_default_measure_column(kpi_name):
    text = (kpi_name or "").lower()
    if "cost" in text:
        return "cost_amount"
    if "hour" in text or "processing" in text:
        return "processing_hours"
    if "customer" in text:
        return "customer_count"
    return "cost_amount"


def _normalize_phrase(text):
    """Lower-case, collapse whitespace, strip trailing event/events."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip().lower())
    cleaned = re.sub(r"\s+events?$", "", cleaned)
    return cleaned


def _extract_event_type_phrase(raw):
    """Return the matching CSV event_type value for raw phrase, or None."""
    normalized = _normalize_phrase(raw)
    event_types = [str(v) for v in get_column_values("event_type")]
    for candidate in event_types:
        if normalized == _normalize_phrase(candidate):
            return candidate
    return None


def _parse_ratio_operands(kpi_name):
    """Extract numerator/denominator event types from '<X> to <Y> Ratio' pattern.

    Only returns values that exist as event_type values in the CSV.
    Never guesses or substitutes.
    """
    cleaned = re.sub(r"\s+", " ", (kpi_name or "").strip())
    cleaned = re.sub(r"\s+ratio$", "", cleaned, flags=re.IGNORECASE)
    match = re.search(r"(.+?)\s*(?:to|/)\s*(.+)", cleaned, flags=re.IGNORECASE)
    if not match:
        return {"numerator_event_type": None, "denominator_event_type": None}
    numerator_raw = match.group(1).strip()
    denominator_raw = match.group(2).strip()
    denominator_raw = re.sub(r"\s+events?$", "", denominator_raw, flags=re.IGNORECASE)
    numerator = _extract_event_type_phrase(numerator_raw)
    denominator = _extract_event_type_phrase(denominator_raw)
    return {"numerator_event_type": numerator, "denominator_event_type": denominator}


def _parse_count_hints(kpi_name):
    """Extract event_type, priority, and event_status hints from count KPI names.

    Examples:
      'Issue Count'               -> {event_type: 'Issue'}
      'Near Miss Count'           -> {event_type: 'Near Miss'}
      'Open Issue Count'          -> {event_type: 'Issue', event_status: 'Open'}
      'High Priority Issue Count' -> {event_type: 'Issue', priority: 'High'}
    """
    text = re.sub(r"\s+count$", "", (kpi_name or "").strip(), flags=re.IGNORECASE).strip()
    event_types = [str(v) for v in get_column_values("event_type")]
    priorities = [str(v) for v in get_column_values("priority")]
    event_statuses = [str(v) for v in get_column_values("event_status")]
    hints = {}
    for et in sorted(event_types, key=len, reverse=True):
        if re.search(re.escape(et), text, flags=re.IGNORECASE):
            hints["event_type"] = et
            text = re.sub(re.escape(et), "", text, flags=re.IGNORECASE).strip()
            break
    for p in priorities:
        if re.search(rf"\b{re.escape(p)}\b", text, flags=re.IGNORECASE):
            hints["priority"] = p
            break
    for s in sorted(event_statuses, key=len, reverse=True):
        if re.search(rf"\b{re.escape(s)}\b", text, flags=re.IGNORECASE):
            hints["event_status"] = s
            break
    return hints


def parse_kpi_name(kpi_name):
    """Parse a free-text KPI name into deterministic metric_type, operands,
    default filter hints, and interpretation text.

    Returns a dict with metric_type=None when the KPI name is unrecognised.
    Callers must check for None and return an error to the user.
    """
    metric_type = infer_metric_type(kpi_name)
    parsed = {
        "metric_type": metric_type,
        "default_measure_column": infer_default_measure_column(kpi_name),
        "parsed_operands": {},
        "interpretation": "",
    }

    if metric_type is None:
        parsed["interpretation"] = (
            "Unsupported KPI format. Please use one of: "
            "Issue Count, Total Cost Impact, Average Processing Hours, "
            "Near Miss to Issue Ratio."
        )
        return parsed

    if metric_type == "ratio":
        operands = _parse_ratio_operands(kpi_name)
        parsed["parsed_operands"] = operands
        n = operands.get("numerator_event_type")
        d = operands.get("denominator_event_type")
        if n and d:
            parsed["interpretation"] = (
                f"I understand that you want to measure the ratio between {n} events "
                f"and {d} events."
            )
        else:
            parsed["interpretation"] = (
                "I detected a ratio KPI. Please confirm numerator and denominator "
                "event types to avoid incorrect assumptions."
            )

    elif metric_type == "count":
        hints = _parse_count_hints(kpi_name)
        parsed["parsed_operands"] = hints
        et = hints.get("event_type")
        qualifiers = []
        if hints.get("priority"):
            qualifiers.append(hints["priority"] + " priority")
        if hints.get("event_status"):
            qualifiers.append(hints["event_status"] + " status")
        qs = " and ".join(qualifiers)
        if et and qs:
            parsed["interpretation"] = (
                f"I understand that you want to count {et} events with {qs}."
            )
        elif et:
            parsed["interpretation"] = (
                f"I understand that you want to count {et} events within your "
                "selected filters and time period."
            )
        else:
            parsed["interpretation"] = (
                "I understand that you want a count KPI. I will count matching "
                "events within your selected filters and time period."
            )

    elif metric_type == "average":
        col = parsed["default_measure_column"]
        parsed["interpretation"] = (
            f"I understand that you want an average KPI. I will compute "
            f"AVG({col}) within your selected filters and time period."
        )

    elif metric_type == "sum":
        col = parsed["default_measure_column"]
        parsed["interpretation"] = (
            f"I understand that you want a total KPI. I will compute "
            f"SUM({col}) within your selected filters and time period."
        )

    return parsed


def generate_description(intent):
    """Generate a non-empty human-readable description from a built intent."""
    metric_type = intent.get("metric_type")
    kpi_name = intent.get("kpi_name", "KPI")

    if metric_type == "ratio":
        n = intent.get("aggregation", {}).get("numerator", {}).get("event_type", "numerator")
        d = intent.get("aggregation", {}).get("denominator", {}).get("event_type", "denominator")
        return (
            f"Measures the ratio of {n} events to {d} events "
            "within the selected filters and time period."
        )
    if metric_type == "sum":
        col = intent.get("aggregation", {}).get("column", "value")
        return (
            f"Measures the total {col} for matching events "
            "within the selected filters and time period."
        )
    if metric_type == "average":
        col = intent.get("aggregation", {}).get("column", "value")
        return (
            f"Measures the average {col} for matching events "
            "within the selected filters and time period."
        )
    et = intent.get("filters", {}).get("event_type")
    subject = f"{et} events" if et else "matching events"
    return (
        f"Measures the total count of {subject} for {kpi_name} "
        "within the selected filters and time period."
    )
