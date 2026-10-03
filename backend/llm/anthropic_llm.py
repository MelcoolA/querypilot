"""Claude via the Anthropic API. Used for final evals and the deployed demo."""
import sys

import anthropic

from backend.llm.base import LLM, LLMResponse

# Room for Claude's thinking plus the answer. Current models (Sonnet 5.5,
# Opus 5.5) always think before answering, so a small cap could cut the
# answer off. Thinking tokens are billed as output tokens.
MAX_TOKENS = 16000


class AnthropicLLM(LLM):
    def __init__(self, model: str, api_key: str, effort: str):
        self.model = model
        self.effort = effort
        self.name = f"anthropic:{model}"
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system: str, prompt: str) -> LLMResponse:
        # No temperature: current Claude models reject sampling parameters.
        # Effort controls how much the model thinks, and so cost and latency.
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"effort": self.effort},
            # If a safety classifier declines the request, the API retries it on
            # Anthropic's recommended fallback model instead of returning a refusal.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise RuntimeError(f"Claude declined the request (category: {category})")
        if response.model != self.model:
            # A fallback answered. Rare for SQL work, but evals should know.
            print(f"[anthropic] answered by fallback model {response.model}", file=sys.stderr)

        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
