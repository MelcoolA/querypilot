"""Prime the LLM with the real schema prompt before the first question.

A local model loads into memory on first use, and Ollama caches the processed
prompt prefix (the ~5k-token schema shared by every question). Without a
warm-up, the first question pays both costs (about 60s instead of about 10s).
"""
from backend.agent import nodes, prompts, semantic
from backend.llm import LLM
from backend.warehouse import Warehouse


def warm_up(llm: LLM, warehouse: Warehouse) -> None:
    schema = nodes.get_schema({}, warehouse)["schema_context"]
    llm.complete(
        prompts.WRITE_SQL_SYSTEM.format(dialect=warehouse.dialect),
        prompts.WRITE_SQL_USER.format(
            schema=schema,
            examples=semantic.render_examples(semantic.load_semantic(warehouse.dataset)),
            question="How many rows are in the orders table?",
        ),
    )


def needs_warm_up(llm: LLM) -> bool:
    # Only local models have a load time and prompt cache to warm. For Claude
    # it would just be a paid call that speeds nothing up.
    return llm.name.startswith("ollama:")
