"""KPI status engine.

Why this exists:
- Encapsulates badge-level interpretation from raw computed KPI values.
- Keeps UI status logic centralized and reusable.
- Supports future domain-specific thresholds by KPI template.
"""


def compute_status(metric_type, value):
    if value is None:
        return {
            "status": "Critical",
            "reason": "No computable value was produced for the selected intent.",
        }

    if metric_type == "ratio":
        if value < 1.0:
            return {"status": "Good", "reason": "Ratio is below threshold 1.0."}
        if value < 1.5:
            return {"status": "Warning", "reason": "Ratio is between 1.0 and 1.5."}
        return {"status": "Critical", "reason": "Ratio exceeded threshold of 1.5."}

    if metric_type == "average":
        if value <= 6:
            return {"status": "Good", "reason": "Average is within target threshold (<= 6)."}
        if value <= 12:
            return {"status": "Warning", "reason": "Average is elevated (between 6 and 12)."}
        return {"status": "Critical", "reason": "Average exceeds threshold 12."}

    if metric_type == "sum":
        if value <= 10000:
            return {"status": "Good", "reason": "Sum is within target threshold (<= 10000)."}
        if value <= 50000:
            return {"status": "Warning", "reason": "Sum is elevated (between 10000 and 50000)."}
        return {"status": "Critical", "reason": "Sum exceeds threshold 50000."}

    # Count thresholds are generic placeholders when domain thresholds are unknown.
    if value <= 100:
        return {"status": "Good", "reason": "Count is within target threshold (<= 100)."}
    if value <= 300:
        return {"status": "Warning", "reason": "Count is elevated (between 100 and 300)."}
    return {"status": "Critical", "reason": "Count exceeds threshold 300."}
