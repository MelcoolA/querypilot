"""Local LLM via Ollama. Free, used for day-to-day development."""
import ollama

from backend.llm.base import LLM, LLMResponse


class OllamaLLM(LLM):
    def __init__(self, model: str, host: str, num_ctx: int, keep_alive: str):
        self.model = model
        self.num_ctx = num_ctx
        self.keep_alive = keep_alive
        self.name = f"ollama:{model}"
        self.client = ollama.Client(host=host)

    def _complete(self, system: str, prompt: str) -> LLMResponse:
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            # Temperature 0 makes SQL generation repeatable, which matters for evals.
            # Ollama's default context is only 4096 tokens, and it silently drops
            # part of any longer prompt (losing e.g. the semantic layer). Set it explicitly.
            options={"temperature": 0, "num_ctx": self.num_ctx},
            # Ollama unloads an idle model after 5 minutes by default, so the next
            # question pays ~60s to reload it. Keep it loaded longer between questions.
            keep_alive=self.keep_alive,
        )
        return LLMResponse(
            text=response.message.content,
            input_tokens=response.prompt_eval_count or 0,
            output_tokens=response.eval_count or 0,
        )
