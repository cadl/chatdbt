# ruff: noqa: E501
import os
from enum import Enum


class I18nKey(Enum):
    KEY_PROMPT_SYSTEM_ROLE_CONTENT = "prompt_system_content"
    KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES = "prompt_system_related_tables"
    KEY_PROMPT_SYSTEM_ROLE_RELATED_MESSAGES = "prompt_system_related_messages"
    KEY_PROMPT_USER_ROLE_SUGGEST_TABLES = "prompt_user_suggest_tables"
    KEY_PROMPT_USER_ROLE_SUGGEST_SQL = "prompt_user_suggest_sql"
    KEY_NO_RESPONSE = "no_response"

    KEY_MESSAGE_related_tables = "message_related_tables"
    KEY_MESSAGE_related_messages = "message_related_messages"


_i18n = {
    "en-us": {
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_CONTENT: "You are a sql master",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES: "Here are some tables with description: {}",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_MESSAGES: "Here are some related chat messages: {}",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_TABLES: "My question is '{}'. Can you tell me which table in ({}) I should use? why?",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_SQL: "My question is '{}'. Can you tell me which table in ({}) I should use(Please select from the table provided above or from the table listed in depends_on)? why? Can you write a sql to complete my question based on this table?",
        I18nKey.KEY_NO_RESPONSE: "Sorry, I can't find any tables",
        I18nKey.KEY_MESSAGE_related_tables: "Related tables",
        I18nKey.KEY_MESSAGE_related_messages: "Related messages",
    },
    "zh-cn": {
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_CONTENT: "你是一位 SQL 专家",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES: "这里有一些 table 的描述: {}",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_MESSAGES: "这里有一些相关的聊天记录: {}",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_TABLES: "我的问题是 '{}'. 你能告诉我我应该使用哪个 table 吗(请从上面提供的 table 或 depends_on 中的 table 中选取)? 为什么?",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_SQL: "我的问题是 '{}'. 你能告诉我我应该使用哪个 table 吗? 为什么? 你能基于这个 table ，写一段 sql 来完成我的问题吗？",
        I18nKey.KEY_NO_RESPONSE: "抱歉，我检索不到任何 table",
        I18nKey.KEY_MESSAGE_related_tables: "相关的 table",
        I18nKey.KEY_MESSAGE_related_messages: "相关的聊天记录",
    },
}


def get_i18n_text(key: I18nKey) -> str:
    lang = os.environ.get("CHATDBT_I18N", "en-us")
    if lang not in _i18n:
        raise ValueError(f"Unsupported language: {lang}")
    return _i18n[lang][key]
