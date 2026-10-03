"""The one LLM interface every agent node talks to."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from langsmith import traceable


@dataclass
class LLMResponse:
    text: str
    # Token counts are tracked so evals can report cost per question.
    input_tokens: int = 0
    output_tokens: int = 0


class LLM(ABC):
    name: str  # e.g. "ollama:qwen2.5-coder:7b" or "anthropic:claude-sonnet-5-5"

    def complete(self, system: str, prompt: str) -> LLMResponse:
        """Send a system prompt plus one user message, return the model's reply.

        Each call is recorded in LangSmith as an LLM run (prompt, reply, tokens)
        when LANGSMITH_TRACING=true; otherwise this is a plain call. Tracing lives
        here so every provider gets it without repeating code.
        """
        provider, _, model = self.name.partition(":")  # "ollama:qwen2.5-coder:7b"
        traced = traceable(
            run_type="llm",
            name=self.name,
            # ls_provider / ls_model_name let LangSmith label the model and price tokens.
            metadata={"ls_provider": provider, "ls_model_name": model},
            process_outputs=_trace_outputs,
        )(self._complete)
        return traced(system, prompt)

    @abstractmethod
    def _complete(self, system: str, prompt: str) -> LLMResponse:
        """Provider-specific call. Implemented by OllamaLLM and AnthropicLLM."""


def _trace_outputs(response: LLMResponse) -> dict:
    """Shape the reply the way LangSmith expects, so token counts show up."""
    return {
        "output": response.text,
        "usage_metadata": {
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
            "total_tokens": response.input_tokens + response.output_tokens,
        },
    }
