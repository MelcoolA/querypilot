"""Ask the agent a question from the terminal.

    python -m backend.cli "top 5 customers by revenue"
"""
import sys
import time

from backend.agent.graph import build_graph
from backend.formatting import format_table
from backend.llm import get_llm
from backend.warehouse import get_warehouse


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m backend.cli "your question"')
        sys.exit(1)
    question = " ".join(sys.argv[1:])

    llm = get_llm()
    agent = build_graph(llm, get_warehouse())
    print(f"Question: {question}\nModel:    {llm.name}\n")

    state = {"question": question}
    start = time.time()
    # stream_mode="updates" yields after every node, so we can show live progress.
    config = {"run_name": "cli question", "tags": ["cli"], "metadata": {"model": llm.name}}
    for update in agent.stream(state, config=config, stream_mode="updates"):
        for node, changes in update.items():
            state.update(changes)
            print(f"[{time.time() - start:5.1f}s] {node:<10} {_describe(node, changes)}")

    print("\nSQL:\n" + state.get("sql", ""))
    if state.get("rows") is not None and not state.get("error"):
        print("\nResult:\n" + format_table(state["columns"], state["rows"]))
    print("\nAnswer:\n" + state.get("answer", ""))
    print(
        f"\n({time.time() - start:.1f}s, {state.get('attempts', 0)} repairs, "
        f"{state.get('input_tokens', 0)} in / {state.get('output_tokens', 0)} out tokens)"
    )


def _describe(node: str, changes: dict) -> str:
    if changes.get("error"):
        return f"error: {changes['error'].splitlines()[0][:100]}"
    if node == "get_schema":
        return f"{len(changes['tables'])} tables"
    if node == "execute":
        return f"{len(changes['rows'])} rows"
    if node == "repair_sql":
        return f"attempt {changes['attempts']}"
    return "ok"


if __name__ == "__main__":
    main()
