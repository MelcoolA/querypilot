"""Wire the nodes into a LangGraph state machine.

    get_schema -> write_sql -> validate -> execute -> summarize
                                  ^          |  |
                                  |   error  |  | error
                                  +-- repair_sql <+
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
    graph.add_conditional_edges("validate", partial(route_after_check, on_success="execute"))
    graph.add_conditional_edges("execute", partial(route_after_check, on_success="summarize"))
    graph.add_edge("repair_sql", "validate")
    graph.add_edge("summarize", END)
    return graph.compile()
