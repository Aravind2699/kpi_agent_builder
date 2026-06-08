"""Agent conversation state manager.

Why this exists:
- Encapsulates step-based state transitions for the agent flow.
- Ensures consistent state shape across endpoints.
- Makes the interview-critical state logic easy to inspect and test.
"""

DEFAULT_STATE = {
    "current_step": "kpi_name",
    "kpi_name": "",
    "metric_type": None,
    "interpretation": "",
    "description": "",
    "questions": [],
    "answers": {},
    "intent": None,
    "validation_result": None,
    "calculation_result": None,
}


def initialize_state(session):
    session["agent_state"] = DEFAULT_STATE.copy()
    session.modified = True
    return session["agent_state"]


def get_state(session):
    if "agent_state" not in session:
        return initialize_state(session)
    return session["agent_state"]


def update_state(session, patch):
    state = get_state(session)
    state.update(patch)
    session["agent_state"] = state
    session.modified = True
    return state


def transition_state(session, next_step):
    state = get_state(session)
    state["current_step"] = next_step
    session["agent_state"] = state
    session.modified = True
    return state


def reset_state(session):
    return initialize_state(session)
