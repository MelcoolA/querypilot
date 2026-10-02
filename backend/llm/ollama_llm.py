"""Local LLM via Ollama. Free, used for day-to-day development."""
import ollama

from backend.llm.base import LLM, LLMResponse


class OllamaLLM(LLM):
    def __init__(self, model: str, host: str):
        self.model = model
        self.name = f"ollama:{model}"
        self.client = ollama.Client(host=host)

    def complete(self, system: str, prompt: str) -> LLMResponse:
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            # Temperature 0 makes SQL generation repeatable, which matters for evals.
            options={"temperature": 0},
        )
        return LLMResponse(
            text=response.message.content,
            input_tokens=response.prompt_eval_count or 0,
            output_tokens=response.eval_count or 0,
        )
