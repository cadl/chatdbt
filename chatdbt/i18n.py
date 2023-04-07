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
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES: "Here are some candidate data tables to choose from: {}",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_MESSAGES: "And some related chat logs: {}",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_TABLES: "Based on the above information, please select the most appropriate data table from the candidate tables({}) to answer my next question, and tell me the reason for choosing this data table. If there are no appropriate data table options, please inform me that none are suitable. My question is: '{}'",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_SQL: "Based on the above information, please select the most appropriate data table from the candidate tables({}) to write an SQL query in response to my next question, and tell me the reason for choosing this data table. If there are no appropriate data table options, please inform me of this. My question is: '{}'",
        I18nKey.KEY_NO_RESPONSE: "Sorry, I can't find any tables",
        I18nKey.KEY_MESSAGE_related_tables: "Related tables",
        I18nKey.KEY_MESSAGE_related_messages: "Related messages",
    },
    "zh-cn": {
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_CONTENT: "你是一位 SQL 专家",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES: "这里有一些备选数据表: {}",
        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_MESSAGES: "以及一些相关的聊天记录: {}",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_TABLES: "请你根据以上信息，从备选数据表({})中挑选最合适的数据表来回答我接下来的问题，并告诉我选择这个数据表的理由。如果没有合适的数据表选项，请告诉我没有合适的选项。我的问题是:'{}'。",
        I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_SQL: "请你根据以上信息，从备选数据表({})中挑选最合适的数据表写一段 SQL 来回答我接下来的问题，并告诉我选择这个数据表的理由。如果没有合适的数据表选项，请告诉我没有合适的选项。我的问题是:'{}'。",
        I18nKey.KEY_NO_RESPONSE: "抱歉，我检索不到任何数据表",
        I18nKey.KEY_MESSAGE_related_tables: "相关的数据表",
        I18nKey.KEY_MESSAGE_related_messages: "相关的聊天记录",
    },
}


def get_i18n_text(key: I18nKey) -> str:
    lang = os.environ.get("CHATDBT_I18N", "en-us")
    if lang not in _i18n:
        raise ValueError(f"Unsupported language: {lang}")
    return _i18n[lang][key]
