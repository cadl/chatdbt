from typing import Dict
from chatdbt.model import TikTokenProvider


def get_tiktoken_provider(
    provider_type: str, config: Dict[str, str]
) -> TikTokenProvider:
    if provider_type == "tiktoken_http_server":
        from .tiktoken_http_server import TikTokenHttpServerProvider

        return TikTokenHttpServerProvider(**config)
    else:
        raise NotImplementedError
