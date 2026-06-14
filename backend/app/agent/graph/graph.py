"""LangGraph StateGraph construction for the bid generation agent flow."""

from langgraph.graph import END, StateGraph

from app.agent.graph.nodes import (
    create_tasks,
    execute_batch,
    final_review,
    parse_tender,
)
from app.agent.graph.router import check_completion, reset_failed, route_final
from app.agent.graph.state import BidState


def build_bid_graph() -> StateGraph:
    """Build and compile the bid generation state graph.

    Graph structure:
      START → parse_tender → create_tasks → execute_batch
                                                ↓
                                         check_completion
                                          ↙            ↘
                                     more chapters    all done
                                          ↓               ↓
                                    execute_batch   final_review
                                                         ↓
                                                     route_final
                                                      ↙        ↘
                                                   PASS        FAIL
                                                    ↓           ↓
                                                   END    reset_failed
                                                             ↓
                                                       execute_batch
    """
    builder = StateGraph(BidState)

    # Nodes
    builder.add_node("parse_tender", parse_tender)
    builder.add_node("create_tasks", create_tasks)
    builder.add_node("execute_batch", execute_batch)
    builder.add_node("final_review", final_review)
    builder.add_node("reset_failed", reset_failed)

    # Edges: main flow
    builder.add_edge("parse_tender", "create_tasks")
    builder.add_edge("create_tasks", "execute_batch")

    # Loop: execute → check → more? → execute | done? → final_review
    builder.add_conditional_edges(
        "execute_batch",
        check_completion,
        {
            "execute_batch": "execute_batch",
            "final_review": "final_review",
        },
    )

    # Final review → pass: end | fail: reset & re-execute
    builder.add_conditional_edges(
        "final_review",
        route_final,
        {
            "__end__": END,
            "reset_failed": "reset_failed",
        },
    )
    builder.add_edge("reset_failed", "execute_batch")

    builder.set_entry_point("parse_tender")

    return builder.compile()


# Singleton compiled graph
bid_graph = build_bid_graph()
