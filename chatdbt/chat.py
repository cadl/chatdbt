import logging
from typing import Optional, Set, List, Dict, cast, Any
import uuid
import datetime
from chatdbt.model import (
    ChatConversationDocument,
    ChatMessageMeta,
    Doc,
    DocMetaContainer,
    DocType,
    DBTDocResolver,
    VectorStorage,
    ChatMessage,
    TikTokenProvider,
    DBTModelDocument,
    DBTModelSqlDocument,
    DBTDocMeta,
    CatalogColumn,
)
from collections import defaultdict
from chatdbt.openai import (
    Openai,
    price_for_embedding,
    EMBEDDING_MODEL,
)
from chatdbt.i18n import get_i18n_text, I18nKey


def _truncate_schema_name_for_model(name: str) -> str:
    """Truncate the schema name from a model name"""
    return ".".join(name.split(".")[1:])


class DocManager:
    def __init__(self, dbt_doc_resolver: DBTDocResolver) -> None:
        self._dbt_doc_resolver = dbt_doc_resolver
        self._dbt_model_doc_store: Dict[str, DBTModelDocument] = {}
        self._dbt_model_sql_doc_store: Dict[str, DBTModelSqlDocument] = {}

        self._initialize_model_doc_store()

    def _get_catalog_columns_for_unique_id(self, unique_id: str) -> List[CatalogColumn]:
        model = self._dbt_doc_resolver.get_manifest_by_unique_id(unique_id) or {
            "columns": {}
        }
        _columns: Dict[str, Dict[str, str]] = defaultdict(dict)
        for column in model["columns"].values():
            _columns[column["name"]]["description"] = column["description"]
            _columns[column["name"]]["type"] = column["data_type"]
            _columns[column["name"]]["name"] = column["name"]

        for column in (
            (self._dbt_doc_resolver.get_catalog_by_unique_id(unique_id) or {})
            .get("columns", {})
            .values()
        ):
            _columns[column["name"]]["type"] = column["type"]
            _columns[column["name"]]["name"] = column["name"]

        catalog_columns = [
            CatalogColumn(
                data_type=i["type"],
                description=i.get("description"),
                name=i["name"],
            )
            for i in _columns.values()
        ]
        return catalog_columns

    def _initialize_model_doc_store(self):
        for unique_id in self._dbt_doc_resolver.list_model_unique_id():
            model = self._dbt_doc_resolver.get_manifest_by_unique_id(unique_id)
            if model["resource_type"] == "model":
                model_name = _truncate_schema_name_for_model(model["unique_id"])
                unique_id = model["unique_id"]
                catalog_columns = self._get_catalog_columns_for_unique_id(unique_id)

                model_doc = DBTModelDocument(
                    name=model_name,
                    description=model["description"],
                    columns=catalog_columns,
                    depends_on=[
                        _truncate_schema_name_for_model(i)
                        for i in model["depends_on"]["nodes"]
                    ],
                    meta=DocMetaContainer(
                        doc_type=DocType.MODEL, meta=DBTDocMeta(name=model_name)
                    ),
                )
                self._dbt_model_doc_store[model_name] = model_doc

                if "compiled_code" in model:
                    model_sql_doc = DBTModelSqlDocument(
                        doc=model_doc,
                        compiled_sql=model["compiled_code"],
                        meta=DocMetaContainer(
                            doc_type=DocType.MODEL, meta=DBTDocMeta(name=model_name)
                        ),
                    )
                    self._dbt_model_sql_doc_store[model_name] = model_sql_doc

    def get_all_docs(self) -> List[Doc]:
        """Get all DBT docs"""
        logging.debug("Getting all DBT docs")
        return [
            *self._dbt_model_doc_store.values(),
        ]

    def _resolve_dbt_doc_meta(self, container: DocMetaContainer) -> Doc:
        """Resolve a DBT doc meta"""
        model_meta = container.meta
        if container.doc_type == DocType.MODEL:
            return self._dbt_model_doc_store[model_meta["name"]]
        elif container.doc_type == DocType.SQL:
            return self._dbt_model_sql_doc_store[model_meta["name"]]
        else:
            raise NotImplementedError

    def resolve_doc_meta(self, container: DocMetaContainer) -> Doc:
        if container.doc_type in [
            DocType.MODEL,
            DocType.SQL,
        ]:
            return self._resolve_dbt_doc_meta(container)
        elif container.doc_type == DocType.CHAT:
            meta = ChatMessageMeta.parse_obj(container.meta)
            return ChatConversationDocument(
                query=meta.query,
                response=meta.response,
                meta=container,
                ref_dbt_docs=[
                    self._resolve_dbt_doc_meta(i)
                    for i in meta.ref_dbt_docs_meta_containers
                ],
            )
        else:
            raise NotImplementedError


class ChatBot:
    """Chatbot for dbt documentation"""

    def __init__(
        self,
        doc_resolver: DBTDocResolver,
        vector_storage: VectorStorage,
        tiktoken_provider: Optional[TikTokenProvider],
        openai_config: Optional[Dict[str, Any]] = None,
        i18n: str = "en",
    ) -> None:
        self.doc_manager = DocManager(doc_resolver)
        self.vector_storage = vector_storage
        self.tiktoken_provider = tiktoken_provider
        self.openai = Openai(**(openai_config or {}))
        self._i18n = i18n
        self._messages: List[ChatMessage] = []

    def index_dbt_docs(self):
        """Index all dbt docs"""

        if self.tiktoken_provider:
            n_tokens = 0
            for doc in self.doc_manager.get_all_docs():
                n_tokens += self.tiktoken_provider.count_token(
                    doc.get_content(), EMBEDDING_MODEL
                )
            logging.info(
                "index dbt docs total tokens: %s, cost %s$",
                n_tokens,
                price_for_embedding(n_tokens),
            )
        for doc in self.doc_manager.get_all_docs():
            logging.debug("indexing doc: %s", doc)
            vector = self.openai.embed(doc.get_content())
            self.vector_storage.insert_doc(doc, vector)

    def _unique_docs(self, docs: List[Doc]) -> List[Doc]:
        """Remove duplicate docs"""
        res = []
        visited: Set[str] = set()
        for doc in docs:
            if doc.get_unique_id() not in visited:
                res.append(doc)
                visited.add(doc.get_unique_id())
        return res

    def suggest_table(self, query: str, k: int = 5) -> ChatMessage:
        """Suggest table for query"""
        vector = self.openai.embed(query)
        logging.debug("embedding query: %s, %s", query, vector[:5])
        similar_docs_meta = self.vector_storage.similarity_search(vector, k)
        docs = [self.doc_manager.resolve_doc_meta(meta) for meta in similar_docs_meta]
        logging.debug("similar docs: %s, %s", query, docs)
        dbt_docs = [
            doc
            for doc in docs
            if doc.get_metadata().doc_type in [DocType.MODEL, DocType.SQL]
        ]
        chat_docs = [
            cast(ChatConversationDocument, doc)
            for doc in docs
            if doc.get_metadata().doc_type == DocType.CHAT
        ]
        dbt_model_names = [doc.get_metadata().meta["name"] for doc in dbt_docs]

        if not dbt_docs:
            message = ChatMessage(
                uuid=uuid.uuid4().hex,
                created_at=datetime.datetime.now(),
                query=query,
                response=get_i18n_text(I18nKey.KEY_NO_RESPONSE),
                ref_dbt_docs=dbt_docs,
                ref_chat_docs=chat_docs,
            )
            self._messages.append(message)
            return message

        messages = []
        messages.append(
            {
                "role": "system",
                "content": get_i18n_text(I18nKey.KEY_PROMPT_SYSTEM_ROLE_CONTENT),
            }
        )
        if dbt_docs:
            _content = "\n".join([doc.get_content() for doc in docs])
            messages.append(
                {
                    "role": "system",
                    "content": get_i18n_text(
                        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES
                    ).format(_content),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": get_i18n_text(
                    I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_TABLES
                ).format(query, ",".join(dbt_model_names)),
            }
        )
        response = self.openai.chat_completion(messages=messages)
        message = ChatMessage(
            uuid=uuid.uuid4().hex,
            created_at=datetime.datetime.now(),
            query=query,
            response=response,
            ref_dbt_docs=dbt_docs,
            ref_chat_docs=chat_docs,
        )
        self._messages.append(message)
        return message

    def suggest_sql(self, query: str, k: int = 10) -> ChatMessage:
        """Suggest sql for query"""
        vector = self.openai.embed(query)
        logging.debug("embedding query: %s, %s", query, vector[:5])
        similar_docs_meta = self.vector_storage.similarity_search(vector, k)
        docs = [self.doc_manager.resolve_doc_meta(meta) for meta in similar_docs_meta]
        logging.debug("similar docs: %s, %s", query, docs)
        dbt_docs = [
            doc
            for doc in docs
            if doc.get_metadata().doc_type in [DocType.MODEL, DocType.SQL]
        ]
        chat_docs = [
            cast(ChatConversationDocument, doc)
            for doc in docs
            if doc.get_metadata().doc_type == DocType.CHAT
        ]
        dbt_model_names = [doc.get_metadata().meta["name"] for doc in dbt_docs]

        if not dbt_docs:
            message = ChatMessage(
                uuid=uuid.uuid4().hex,
                created_at=datetime.datetime.now(),
                query=query,
                response=get_i18n_text(I18nKey.KEY_NO_RESPONSE),
                ref_dbt_docs=dbt_docs,
                ref_chat_docs=chat_docs,
            )
            self._messages.append(message)
            return message

        messages = []
        messages.append(
            {
                "role": "system",
                "content": get_i18n_text(I18nKey.KEY_PROMPT_SYSTEM_ROLE_CONTENT),
            }
        )
        if dbt_docs:
            _content = "\n".join([doc.get_content() for doc in docs])
            messages.append(
                {
                    "role": "system",
                    "content": get_i18n_text(
                        I18nKey.KEY_PROMPT_SYSTEM_ROLE_RELATED_TABLES
                    ).format(_content),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": get_i18n_text(
                    I18nKey.KEY_PROMPT_USER_ROLE_SUGGEST_SQL
                ).format(query, ",".join(dbt_model_names)),
            }
        )
        logging.debug("messages: %s", messages)
        response = self.openai.chat_completion(messages=messages)
        message = ChatMessage(
            uuid=uuid.uuid4().hex,
            created_at=datetime.datetime.now(),
            query=query,
            response=response,
            ref_dbt_docs=dbt_docs,
            ref_chat_docs=chat_docs,
        )
        self._messages.append(message)
        return message

    def memory_message(self, message: ChatMessage):
        """Memory message"""
        return self.memory_message_by_uuid(message.uuid)

    def _find_message(self, chat_uuid: str) -> Optional[ChatMessage]:
        """Find message by uuid"""
        for message in self._messages:
            if message.uuid == chat_uuid:
                return message
        return None

    def memory_message_by_uuid(self, chat_uuid: str):
        """Memory message by uuid"""
        message = self._find_message(chat_uuid)
        if not message:
            raise ValueError("message not found")
        chat_doc = ChatConversationDocument(
            query=message.query,
            response=message.response,
            meta=DocMetaContainer(
                doc_type=DocType.CHAT,
                meta=ChatMessageMeta(
                    query=message.query,
                    response=message.response,
                    created_at=datetime.datetime.now(),
                    ref_dbt_docs_meta_containers=[
                        i.get_metadata() for i in message.ref_dbt_docs
                    ],
                ).dict(),
            ),
            ref_dbt_docs=message.ref_dbt_docs,
        )

        vector = self.openai.embed(chat_doc.get_content())
        logging.debug("memory message: %s, %s", chat_doc, vector[:5])
        self.vector_storage.insert_doc(chat_doc, vector)
