"""Conditional edge router functions for the LangGraph."""

from app.agent.graph.state import BidState


def check_completion(state: BidState) -> str:
    """Check if all chapters are done → final_review, or dispatch more."""
    remaining = [c for c in state["chapters"] if c.status == "pending"]
    in_progress = [c for c in state["chapters"] if c.status == "in_progress"]

    if not remaining and not in_progress:
        return "final_review"
    return "execute_batch"


def route_final(state: BidState) -> str:
    """Route after final review: pass → end, fail → re-execute failing chapters."""
    result = state.get("final_review_result")
    if result == "PASS":
        return "__end__"

    rounds = state.get("final_review_round", 0)
    if rounds >= state.get("max_final_rounds", 2):
        return "__end__"

    # Reset failed/review-needed chapters to pending
    return "reset_failed"


def reset_failed(state: BidState) -> dict:
    """Reset all non-completed chapters to pending for re-execution."""
    updated = []
    for c in state["chapters"]:
        if c.status != "completed":
            updated.append(c.model_copy(update={
                "status": "pending",
                "content": None,
                "review_feedback": None,
                "revision_count": 0,
            }))
        else:
            updated.append(c)

    return {"chapters": updated}
