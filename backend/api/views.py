from copy import deepcopy

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from services.calculator import calculate_kpi as execute_kpi_calculation
from services.csv_loader import get_schema, load_dataframe
from services.intent_builder import build_intent as build_kpi_intent
from services.kpi_parser import parse_kpi_name
from services.question_generator import generate_questions as generate_kpi_questions
from services.state_manager import DEFAULT_STATE
from services.validator import validate_intent as validate_kpi_intent

# ---------------------------------------------------------------------------
# All endpoints are stateless: the frontend owns state in localStorage and
# sends it back in every request body. This avoids cross-origin session-cookie
# issues (SameSite restrictions) in local development.
# ---------------------------------------------------------------------------


def _make_state(patch):
    """Build a clean state dict by merging patch over defaults."""
    state = deepcopy(DEFAULT_STATE)
    state.update(patch)
    return state


def _get_interpretation(kpi_name):
    if not kpi_name:
        return ""
    return parse_kpi_name(kpi_name).get("interpretation", "")


@api_view(["POST"])
def generate_questions(request):
    kpi_name = (request.data.get("kpi_name") or "").strip()
    if not kpi_name:
        return Response({"error": "kpi_name is required"}, status=status.HTTP_400_BAD_REQUEST)

    generated = generate_kpi_questions(kpi_name)
    if generated.get("metric_type") is None:
        return Response(
            {
                "valid": False,
                "error": "Unsupported KPI format. Recognised patterns: "
                "'Issue Count', 'Total Cost Impact', "
                "'Average Processing Hours', 'Near Miss to Issue Ratio'. "
                "Please revise the KPI name.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    state = _make_state(
        {
            "current_step": "questionnaire",
            "kpi_name": kpi_name,
            "metric_type": generated["metric_type"],
            "description": generated["description"],
            "interpretation": generated["interpretation"],
            "questions": generated["questions"],
            "answers": generated.get("default_answers", {}),
            "intent": None,
            "validation_result": None,
            "calculation_result": None,
        }
    )

    return Response(
        {
            "state": state,
            "questions": generated["questions"],
            "default_measure_column": generated["default_measure_column"],
            "interpretation": generated["interpretation"],
        }
    )


@api_view(["POST"])
def build_intent(request):
    # Accept kpi_name/metric_type from body (sent by frontend from localStorage state)
    kpi_name = (request.data.get("kpi_name") or "").strip()
    metric_type = (request.data.get("metric_type") or "").strip()
    answers = request.data.get("answers") or {}

    if not kpi_name or not metric_type:
        return Response(
            {"error": "kpi_name and metric_type are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    intent = build_kpi_intent(kpi_name, metric_type, answers)
    state = _make_state(
        {
            "current_step": "intent_validation",
            "kpi_name": kpi_name,
            "metric_type": metric_type,
            "interpretation": _get_interpretation(kpi_name),
            "description": intent.get("description", ""),
            "answers": answers,
            "intent": intent,
            "validation_result": None,
            "calculation_result": None,
        }
    )

    return Response({"state": state, "intent": intent})


@api_view(["POST"])
def validate_intent(request):
    intent = request.data.get("intent")

    if not intent:
        return Response({"error": "intent is required"}, status=status.HTTP_400_BAD_REQUEST)

    df = load_dataframe()
    validation = validate_kpi_intent(intent, df)
    next_step = "calculation" if validation["valid"] else "intent_validation"
    state = _make_state(
        {
            "current_step": next_step,
            "kpi_name": intent.get("kpi_name", ""),
            "metric_type": intent.get("metric_type", ""),
            "interpretation": _get_interpretation(intent.get("kpi_name", "")),
            "description": intent.get("description", ""),
            "intent": intent,
            "validation_result": validation,
        }
    )

    return Response({"state": state, "validation_result": validation})


@api_view(["POST"])
def calculate_kpi(request):
    intent = request.data.get("intent")

    if not intent:
        return Response({"error": "intent is required"}, status=status.HTTP_400_BAD_REQUEST)

    df = load_dataframe()
    validation = validate_kpi_intent(intent, df)
    if not validation["valid"]:
        state = _make_state(
            {
                "current_step": "intent_validation",
                "kpi_name": intent.get("kpi_name", ""),
                "metric_type": intent.get("metric_type", ""),
                "interpretation": _get_interpretation(intent.get("kpi_name", "")),
                "description": intent.get("description", ""),
                "intent": intent,
                "validation_result": validation,
            }
        )
        return Response(
            {"state": state, "validation_result": validation, "error": "Intent validation failed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = execute_kpi_calculation(df, intent)
    except ZeroDivisionError as exc:
        err_state = _make_state(
            {
                "current_step": "intent_validation",
                "kpi_name": intent.get("kpi_name", ""),
                "metric_type": intent.get("metric_type", ""),
                "interpretation": _get_interpretation(intent.get("kpi_name", "")),
                "description": intent.get("description", ""),
                "intent": intent,
                "validation_result": {"valid": False, "errors": [str(exc)]},
            }
        )
        return Response(
            {"state": err_state, "error": str(exc)},
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
    except (ValueError, KeyError) as exc:
        err_state = _make_state(
            {
                "current_step": "intent_validation",
                "kpi_name": intent.get("kpi_name", ""),
                "metric_type": intent.get("metric_type", ""),
                "intent": intent,
                "validation_result": {"valid": False, "errors": [str(exc)]},
            }
        )
        return Response(
            {"state": err_state, "error": str(exc)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return Response(
            {"error": f"Unexpected calculation error: {str(exc)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    state = _make_state(
        {
            "current_step": "review",
            "kpi_name": intent.get("kpi_name", ""),
            "metric_type": intent.get("metric_type", ""),
            "interpretation": _get_interpretation(intent.get("kpi_name", "")),
            "description": intent.get("description", ""),
            "intent": intent,
            "validation_result": validation,
            "calculation_result": result,
        }
    )

    return Response({"state": state, "calculation_result": result})


@api_view(["POST"])
def reset_session(request):
    state = deepcopy(DEFAULT_STATE)
    return Response({"message": "Session reset", "state": state})


@api_view(["GET"])
def schema(request):
    return Response(
        {
            "api": {
                "generate_questions": "POST /api/generate-questions/",
                "build_intent": "POST /api/build-intent/",
                "validate_intent": "POST /api/validate-intent/",
                "calculate_kpi": "POST /api/calculate-kpi/",
                "reset_session": "POST /api/reset-session/",
                "schema": "GET /api/schema/",
            },
            "data_schema": get_schema(),
        }
    )
