import functools
import logging
import os
from typing import Optional, cast, Any, Dict

from chatdbt.chat import ChatBot
from chatdbt.dbt_doc_resolver import get_dbt_doc_resolver
from chatdbt.model import ChatMessage, DBTDocResolver, TikTokenProvider, VectorStorage
from chatdbt.tiktoken_provider import get_tiktoken_provider
from chatdbt.vector_storage import get_vector_storage


ENV_VAR_VECTOR_STORAGE_TYPE = "CHATDBT_VECTOR_STORAGE_TYPE"
ENV_VAR_VECTOR_STORAGE_CONFIG_PREFIX = "CHATDBT_VECTOR_STORAGE_CONFIG_"
ENV_VAR_DBT_DOC_RESOLVER_TYPE = "CHATDBT_DBT_DOC_RESOLVER_TYPE"
ENV_VAR_DBT_DOC_RESOLVER_CONFIG_PREFIX = "CHATDBT_DBT_DOC_RESOLVER_CONFIG_"

ENV_VAR_I18N = "CHATDBT_I18N"

ENV_VAR_TIKTOKEN_PROVIDER_TYPE = "CHATDBT_TIKTOKEN_PROVIDER_TYPE"
ENV_VAR_TIKTOKEN_PROVIDER_CONFIG_PREFIX = "CHATDBT_TIKTOKEN_PROVIDER_CONFIG_"

ENV_VAR_OPENAI_CONFIG_PREFIX = "CHATDBT_OPENAI_CONFIG_"


class _Global:
    chat_instance: Optional[ChatBot] = None
    chat_instance_init: bool = False


def setup_shortcut(
    vector_storage: VectorStorage,
    dbt_doc_resolver: DBTDocResolver,
    tiktoken_provider: Optional[TikTokenProvider] = None,
    openai_config: Optional[Dict[str, Any]] = None,
    i18n: str = "en-us",
):
    logging.basicConfig(level=logging.INFO)

    _Global.chat_instance = ChatBot(
        dbt_doc_resolver,
        vector_storage,
        tiktoken_provider,
        openai_config,
        i18n,
    )
    _Global.chat_instance_init = True


def setup_shortcut_via_env() -> None:
    """Setup chat instance via environment variables"""
    vector_storage_type = os.environ.get(ENV_VAR_VECTOR_STORAGE_TYPE)
    if not vector_storage_type:
        raise ValueError(
            f"Environment variable {ENV_VAR_VECTOR_STORAGE_TYPE} is not set"
        )
    vector_storage_config = {
        k.replace(ENV_VAR_VECTOR_STORAGE_CONFIG_PREFIX, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(ENV_VAR_VECTOR_STORAGE_CONFIG_PREFIX)
    }
    dbt_doc_resolver_type = os.environ.get(ENV_VAR_DBT_DOC_RESOLVER_TYPE)
    if not dbt_doc_resolver_type:
        raise ValueError(
            f"Environment variable {ENV_VAR_DBT_DOC_RESOLVER_TYPE} is not set"
        )
    dbt_doc_resolver_config = {
        k.replace(ENV_VAR_DBT_DOC_RESOLVER_CONFIG_PREFIX, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(ENV_VAR_DBT_DOC_RESOLVER_CONFIG_PREFIX)
    }

    i18n = os.environ.get(ENV_VAR_I18N, "en")

    tiktoken_provider: Optional[TikTokenProvider] = None
    tiktoken_provider_type = os.environ.get(ENV_VAR_TIKTOKEN_PROVIDER_TYPE)
    tiktoken_provider_config = {
        k.replace(ENV_VAR_TIKTOKEN_PROVIDER_CONFIG_PREFIX, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(ENV_VAR_TIKTOKEN_PROVIDER_CONFIG_PREFIX)
    }

    if tiktoken_provider_type is not None:
        tiktoken_provider = get_tiktoken_provider(
            tiktoken_provider_type, tiktoken_provider_config
        )

    openai_config = {
        k.replace(ENV_VAR_OPENAI_CONFIG_PREFIX, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(ENV_VAR_OPENAI_CONFIG_PREFIX)
    }

    setup_shortcut(
        get_vector_storage(vector_storage_type, vector_storage_config),
        get_dbt_doc_resolver(dbt_doc_resolver_type, dbt_doc_resolver_config),
        tiktoken_provider,
        openai_config,
        i18n,
    )


def ensure_chat_init(func):
    """Decorator to ensure chat instance is initialized before calling the function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not _Global.chat_instance_init:
            setup_shortcut_via_env()
        return func(*args, **kwargs)

    return wrapper


@ensure_chat_init
def suggest_table(query: str, k: int = 5):
    """Suggest table based on query."""
    chat: ChatBot = cast(ChatBot, _Global.chat_instance)
    return chat.suggest_table(query, k)


@ensure_chat_init
def index_dbt_docs() -> None:
    """Index dbt docs."""
    chat: ChatBot = cast(ChatBot, _Global.chat_instance)
    return chat.index_dbt_docs()


@ensure_chat_init
def suggest_sql(query: str, k: int = 5):
    """Suggest sql based on query."""
    chat: ChatBot = cast(ChatBot, _Global.chat_instance)
    return chat.suggest_sql(query, k)


@ensure_chat_init
def memory_message(message: ChatMessage):
    """Memory chat message."""
    chat: ChatBot = cast(ChatBot, _Global.chat_instance)
    return chat.memory_message(message)
