"""Wire the nodes into a LangGraph state machine.

    get_schema -> write_sql -> validate -> execute -> summarize
                                ^    | error     | error   ^
                                |    v           v         |
                                +--- repair_sql <+         |
                                         |                 |
                                         +-----------------+
                         (repair repeats an earlier attempt)
    After MAX_REPAIRS failed repairs, validate or execute also route to summarize.
"""
from functools import partial

from langgraph.graph import END, START, StateGraph

from backend.agent import nodes
from backend.agent.state import AgentState
from backend.llm import LLM
from backend.warehouse import Warehouse

MAX_REPAIRS = 3  # after the first SQL, allow up to 3 repair attempts before giving up


def route_after_check(state: AgentState, on_success: str) -> str:
    """Shared router for validate and execute: continue, repair, or give up."""
    if not state.get("error"):
        return on_success
    if state["attempts"] < MAX_REPAIRS:
        return "repair_sql"
    return "summarize"  # summarize reports the failure honestly


# Named wrappers (not partial) so each routing decision has a readable name in
# LangSmith traces instead of "RunnableCallable".
def route_after_validate(state: AgentState) -> str:
    return route_after_check(state, on_success="execute")


def route_after_execute(state: AgentState) -> str:
    return route_after_check(state, on_success="summarize")


def route_after_repair(state: AgentState) -> str:
    """A repair that repeats an earlier attempt goes straight to summarize."""
    return "summarize" if state.get("repeated") else "validate"


def build_graph(llm: LLM, warehouse: Warehouse):
    # partial() injects the LLM and warehouse, so nodes stay plain functions
    # that are easy to unit test with fakes.
    graph = StateGraph(AgentState)
    graph.add_node("get_schema", partial(nodes.get_schema, warehouse=warehouse))
    graph.add_node("write_sql", partial(nodes.write_sql, llm=llm, warehouse=warehouse))
    graph.add_node("validate", partial(nodes.validate, warehouse=warehouse))
    graph.add_node("execute", partial(nodes.execute, warehouse=warehouse))
    graph.add_node("repair_sql", partial(nodes.repair_sql, llm=llm, warehouse=warehouse))
    graph.add_node("summarize", partial(nodes.summarize, llm=llm))

    graph.add_edge(START, "get_schema")
    graph.add_edge("get_schema", "write_sql")
    graph.add_edge("write_sql", "validate")
    graph.add_conditional_edges("validate", route_after_validate)
    graph.add_conditional_edges("execute", route_after_execute)
    graph.add_conditional_edges("repair_sql", route_after_repair)
    graph.add_edge("summarize", END)
    return graph.compile()
