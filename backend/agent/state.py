"""The state object that flows through every node of the agent graph."""
from typing import TypedDict


class AgentState(TypedDict, total=False):
    question: str
    tables: list[str]        # tables included in the schema context
    schema_context: str      # text description of those tables given to the LLM
    sql: str                 # latest SQL (raw from the LLM, then cleaned by validate)
    attempts: int            # how many repairs have been tried so far
    error: str               # latest validation or execution error, "" if none
    history: list[dict]      # failed attempts so far: [{"sql": ..., "error": ...}], oldest first
    repeated: bool           # True if a repair returned SQL it had already tried
    columns: list[str]
    rows: list[tuple]
    answer: str              # final plain-English answer
    input_tokens: int        # running totals across all LLM calls, for cost tracking
    output_tokens: int
