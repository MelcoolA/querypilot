"""The one LLM interface every agent node talks to."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    # Token counts are tracked now so Phase 2 evals can report cost per question.
    input_tokens: int = 0
    output_tokens: int = 0


class LLM(ABC):
    name: str

    @abstractmethod
    def complete(self, system: str, prompt: str) -> LLMResponse:
        """Send a system prompt plus one user message, return the model's reply."""
