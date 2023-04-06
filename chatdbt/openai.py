"""OpenAI embedding"""

import logging
import openai
from openai.embeddings_utils import get_embedding
from typing import Dict, List
from chatdbt.model import EmbeddingProvider
from tenacity import retry, stop_after_attempt, wait_random_exponential


COMPLETION_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"


@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def chat_completion(messages: List[Dict[str, str]], temperature=0.2):
    return openai.ChatCompletion.create(
        messages=messages, model=COMPLETION_MODEL, temperature=temperature
    )


def price_for_completion(n_tokens: int) -> float:
    return float(n_tokens) / 1000.0 * 0.002


def price_for_embedding(n_tokens: int) -> float:
    return float(n_tokens) / 1000.0 * 0.0004


class Openai(EmbeddingProvider):
    """OpenAI embedding"""

    def __init__(self, temperature: float = 0.2):
        self.embedding_model = EMBEDDING_MODEL
        self.temperature = float(temperature)

    def embed(self, content: str) -> List[float]:
        """Embed a piece of text into a vector"""
        return get_embedding(content, engine=self.embedding_model)

    def completion(self):
        openai.ChatCompletion.create()

    def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        res = chat_completion(messages, temperature=self.temperature)
        usage = res["usage"]["total_tokens"]
        logging.info(
            "chat-completion total tokens: %s, cost %s$",
            usage,
            price_for_completion(usage),
        )

        return res["choices"][0]["message"]["content"]
