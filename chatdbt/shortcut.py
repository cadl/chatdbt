import logging
import functools
import os

from typing import Optional

from chatdbt.chat import ChatBot
from chatdbt.model import VectorStorage, ChatMessage, DBTDocResolver, TikTokenProvider
from chatdbt.vector_storage import get_vector_storage
from chatdbt.dbt_doc_resolver import get_dbt_doc_resolver
from chatdbt.tiktoken_provider import get_tiktoken_provider


ENV_VAR_VECTOR_STORAGE_TYPE = "CHATDBT_VECTOR_STORAGE_TYPE"
ENV_VAR_VECTOR_STORAGE_CONFIG_PREFIX = "CHATDBT_VECTOR_STORAGE_CONFIG_"
ENV_VAR_DBT_DOC_RESOLVER_TYPE = "CHATDBT_DBT_DOC_RESOLVER_TYPE"
ENV_VAR_DBT_DOC_RESOLVER_CONFIG_PREFIX = "CHATDBT_DBT_DOC_RESOLVER_CONFIG_"

ENV_VAR_I18N = "CHATDBT_I18N"

ENV_VAR_TIKTOKEN_PROVIDER_TYPE = "CHATDBT_TIKTOKEN_PROVIDER_TYPE"
ENV_VAR_TIKTOKEN_PROVIDER_CONFIG_PREFIX = "CHATDBT_TIKTOKEN_PROVIDER_CONFIG_"


_settings = {"init": False, "chat_instance": None}


def setup_shortcut(
    vector_storage: VectorStorage,
    dbt_doc_resolver: DBTDocResolver,
    tiktoken_provider: Optional[TikTokenProvider] = None,
    i18n: str = "en-us",
):
    logging.basicConfig(level=logging.INFO)

    """Setup chat instance"""
    _settings["chat_instance"] = ChatBot(
        dbt_doc_resolver,
        vector_storage,
        tiktoken_provider,
        i18n,
    )
    _settings["init"] = True


def setup_shortcut_via_env():
    """Setup chat instance via environment variables"""
    vector_storage_type = os.environ.get(ENV_VAR_VECTOR_STORAGE_TYPE)
    vector_storage_config = {
        k.replace(ENV_VAR_VECTOR_STORAGE_CONFIG_PREFIX, "").lower(): v
        for k, v in os.environ.items()
        if k.startswith(ENV_VAR_VECTOR_STORAGE_CONFIG_PREFIX)
    }
    dbt_doc_resolver_type = os.environ.get(ENV_VAR_DBT_DOC_RESOLVER_TYPE)
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

    setup_shortcut(
        get_vector_storage(vector_storage_type, vector_storage_config),
        get_dbt_doc_resolver(dbt_doc_resolver_type, dbt_doc_resolver_config),
        tiktoken_provider,
        i18n,
    )


def ensure_chat_init(func):
    """Decorator to ensure chat instance is initialized before calling the function."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not _settings["init"]:
            setup_shortcut_via_env()
        return func(*args, **kwargs)

    return wrapper


@ensure_chat_init
def suggest_table(query: str, k: int = 5):
    """Suggest table based on query."""
    chat: ChatBot = _settings["chat_instance"]
    return chat.suggest_table(query, k)


@ensure_chat_init
def index_dbt_docs():
    """Index dbt docs."""
    chat: ChatBot = _settings["chat_instance"]
    return chat.index_dbt_docs()


@ensure_chat_init
def suggest_sql(query: str, k: int = 5):
    """Suggest sql based on query."""
    chat: ChatBot = _settings["chat_instance"]
    return chat.suggest_sql(query, k)


@ensure_chat_init
def memory_message(message: ChatMessage):
    """Memory chat message."""
    chat: ChatBot = _settings["chat_instance"]
    return chat.memory_message(message)
