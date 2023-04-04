import logging
from typing import Optional

import requests

from chatdbt.model import TikTokenProvider


class TikTokenHttpServerProvider(TikTokenProvider):
    """Count token using a"""

    def __init__(self, api_base: str, timeout_secs: int = 5) -> None:
        self._api_base = api_base.rstrip("/")
        self._timeout_secs = timeout_secs

    def count_token(self, prompt: str, model: str) -> Optional[int]:
        """Count tokens for a prompt"""

        req = requests.get(
            url=f"{self._api_base}/tokenize",
            json={"prompt": prompt, "model": model},
            timeout=self._timeout_secs,
        )
        if not req.ok:
            logging.warning(
                "Failed to count token, got %s %s", req.status_code, req.text
            )
            return None
        tokens = req.json()["tokens"]
        return len(tokens)
