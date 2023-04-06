"""Base classes for the chatdbt model"""
import datetime
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel as PydanticBaseModel
from chatdbt.i18n import get_i18n_text, I18nKey

from enum import Enum


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True


class DocType(Enum):
    MODEL = "model"
    # todo add metrics
    # METRICS = "metrics"
    SQL = "sql"
    CHAT = "chat"


class DocMetaContainer(BaseModel):
    """Metadata for a document"""

    doc_type: DocType
    meta: Dict[str, Any]


class Doc(ABC):
    """Base class for all documents"""

    @abstractmethod
    def get_content(self):
        """Get the content of the document"""

    @abstractmethod
    def get_metadata(self) -> DocMetaContainer:
        """Get the metadata of the document"""

    @abstractmethod
    def get_unique_id(self) -> str:
        pass


class VectorStorage(ABC):
    """Base class for all vector storages"""

    @abstractmethod
    def insert_doc(self, doc: Doc, vector: List[float]):
        """Insert a document into the vector storage"""

    @abstractmethod
    def similarity_search(self, vector: List[float], k: int) -> List[DocMetaContainer]:
        """Search for similar documents in the vector storage"""


class EmbeddingProvider(ABC):
    """Base class for all embeddings"""

    @abstractmethod
    def embed(self, content: str) -> List[float]:
        """Embed a piece of text into a vector"""


class TikTokenProvider(ABC):
    """Base class for all tiktoken providers"""

    @abstractmethod
    def count_token(self, prompt: str, model: str) -> Optional[int]:
        """Count tokens for a prompt"""


def _markdown_dbt_doc_li(name: str, content: str, indent: int = 4):
    _items = content.split("\n")
    items = []
    for item in _items:
        items.append(item)
    body = "\n\n".join([" " * indent + item for item in ["```", *items, "```"]])
    return f"""- {name}

{body}

"""


def _markdown_chat_doc_li(query: str, response: str, indent: int = 4):
    items = [
        " " * indent + item
        for item in ["```", f"query: {query}", f"response: {response}", "```"]
    ]
    body = "\n\n".join(items)
    return f"- {body}"


class DBTDocResolver(ABC):
    """Base class for all DBT document resolvers"""

    @abstractmethod
    def get_manifest_by_unique_id(self, unique_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def get_catalog_by_unique_id(self, unique_id: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def list_model_unique_id(self) -> List[str]:
        pass


class DBTDocMeta(BaseModel):
    """DBT document metadata"""

    name: str


class ChatMessageMeta(BaseModel):
    """Chat message metadata"""

    ref_dbt_docs_meta_containers: List[DocMetaContainer]
    query: str
    created_at: datetime.datetime
    response: Optional[str]


class CatalogColumn(BaseModel):
    """A column in a DBT catalog"""

    name: str
    data_type: Optional[str]
    description: Optional[str]


class DBTModelDocument(BaseModel, Doc):
    """A DBT model document"""

    meta: DocMetaContainer
    name: str
    description: Optional[str]
    columns: List[CatalogColumn]
    depends_on: List[str]

    def get_content(self):
        columns = [
            str(i.dict()).replace(" ", "").replace("'", "") for i in self.columns
        ]
        return f"""name: {self.name}
description: {self.description or ''}
columns: {columns}
depends_on: {self.depends_on}
"""

    def get_metadata(self):
        return self.meta

    def get_unique_id(self) -> str:
        return self.name


# todo: add metrics document


class DBTModelSqlDocument(BaseModel, Doc):
    """A DBT SQL document"""

    doc: DBTModelDocument
    compiled_sql: str
    meta: DocMetaContainer

    def get_content(self):
        return f"""name: {self.doc.name}
build_by: {self.compiled_sql}
depends_on: {self.doc.depends_on}
"""

    def get_metadata(self):
        return self.meta

    def get_unique_id(self) -> str:
        return f"{self.doc.name}_sql"


class ChatConversationDocument(BaseModel, Doc):
    """A chat conversation document"""

    query: str
    response: Optional[str]
    meta: DocMetaContainer
    ref_dbt_docs: List[Doc]

    def get_content(self):
        return f"""previous chat:
query: {self.query}
response: {self.response}"""

    def get_metadata(self):
        return self.meta

    def get_unique_id(self) -> str:
        return str(hash(self.query))


class ChatMessage(BaseModel):
    """A chat message"""

    query: str
    response: str
    uuid: str
    created_at: datetime.datetime
    ref_dbt_docs: List[Doc]
    ref_chat_docs: List[ChatConversationDocument]

    def _repr_markdown_(self):
        ref_dbt_docs = "\n".join(
            [
                _markdown_dbt_doc_li(i.get_unique_id(), i.get_content())
                for i in self.ref_dbt_docs
            ]
        )
        ref_chat_docs = "\n".join(
            [
                _markdown_chat_doc_li(
                    i.query,
                    i.response,
                )
                for i in self.ref_chat_docs
            ]
        )

        return f"""{self.response}

{get_i18n_text(I18nKey.KEY_MESSAGE_related_tables)}:

{ref_dbt_docs}

{get_i18n_text(I18nKey.KEY_MESSAGE_related_messages)}:

{ref_chat_docs}

"""
