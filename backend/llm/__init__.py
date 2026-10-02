"""Pick the LLM provider from .env (LLM_PROVIDER=ollama|anthropic)."""
import os

from dotenv import load_dotenv

from backend.llm.base import LLM, LLMResponse

load_dotenv()


def get_llm() -> LLM:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "ollama":
        from backend.llm.ollama_llm import OllamaLLM

        return OllamaLLM(
            model=_require("OLLAMA_MODEL"),
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "16384")),
        )
    if provider == "anthropic":
        from backend.llm.anthropic_llm import AnthropicLLM

        return AnthropicLLM(model=_require("ANTHROPIC_MODEL"), api_key=_require("ANTHROPIC_API_KEY"))
    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'ollama' or 'anthropic')")


def _require(var: str) -> str:
    value = os.getenv(var)
    if not value:
        raise ValueError(f"{var} is not set. Add it to your .env file.")
    return value


__all__ = ["LLM", "LLMResponse", "get_llm"]
