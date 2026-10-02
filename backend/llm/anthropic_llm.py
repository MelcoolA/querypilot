"""Claude via the Anthropic API. Used for final evals and the deployed demo."""
import anthropic

from backend.llm.base import LLM, LLMResponse


class AnthropicLLM(LLM):
    def __init__(self, model: str, api_key: str):
        self.model = model
        self.name = f"anthropic:{model}"
        self.client = anthropic.Anthropic(api_key=api_key)

    def complete(self, system: str, prompt: str) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
