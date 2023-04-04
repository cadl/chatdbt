# chatdbt

## What is this?
chatdbt is an openai-based [dbt](https://www.getdbt.com/) documentation robot. You can use natural language to describe your data query requirements to the robot, and chatdbt will help you select the dbt model you need, or generate sql responses based on these dbt models to meet your needs. Of course, you need to set up your [dbt documentation](https://docs.getdbt.com/reference/commands/cmd-docs) for chatdbt in advance.

## Quick Install

`pip install chatdbt`

package extras:
- `nomic`: use nomic/atlas as vector storage backend
- `pgvector`: use pgvector as vector storage backend

## Internals

Chatdbt uses openai's `text-embedding-ada-002` model interface to embed your dbt documentation and save the vectors to the vector storage you provide. When you make an inquiry to chatdbt, it retrieves the [models](https://docs.getdbt.com/docs/build/models) and [metrics](https://docs.getdbt.com/docs/build/metrics) (todo😊) that are semantically similar to your question. Based on the returned content and your question, it uses openai `gpt-3.5-turbo` model to provide appropriate answers. Similar to [langchain](https://github.com/hwchase17/langchain) or [llama_index](https://github.com/jerryjliu/llama_index).


**How does chatdbt integrate with my dbt doc, and where is my embedding data stored?**

There are several interfaces within chatdbt:
- `VectorStorage` is responsible for storing embedding vectors. Currently supporting:
  - `atlas`

    Set up your `api_key` and `project_name` to use Nomic Atlas for storing and retrieving the vector data.

  - `pgvector`

    Set up your `connect_string` and `table_name` to use pgvector for storing and retrieving the vector data.
- `DBTDocResolver` is responsible for providing dbt manifest and catalog data. Currently supporting:
  - `localfs`

    Set up `manifest_json_path` and `manifest_json_path`, and chatdbt will read the dbt manifest and catalog from the local file system.
- `TikTokenProvider` is responsible for estimating the number of tokens consumed by OpenAI. Currently supporting:
  - `tiktoken_http_server`

    Set up a [tiktoken-http-server](https://github.com/howdymic/tiktoken-server) `api_base`(example: `http://localhost:8080`) to use tiktoken-http-server for estimating the number of tokens consumed by OpenAI.

You can also implement the above interfaces yourself and integrate them into your own system.

## Quick Start

You can initialize a chatdbt instance manually:

```python
your_pgvector_connect_string = "postgresql+psycopg://postgres:foobar@localhost:5432/chatdbt"
your_pgvector_table_name = "chatdbt"
your_manifest_json_path = "data/manifest.json"
your_catalog_json_path = "data/catalog.json"
your_openai_key = "sk-foobar"
```

```python
import os

os.environ["OPENAI_API_KEY"] = your_openai_key

from chatdbt import ChatBot
from chatdbt.vector_storage.pgvector import PGVectorStorage
from chatdbt.dbt_doc_resolver.localfs import LocalfsDBTDocResolver


vector_storage = PGVectorStorage(connect_string=your_pgvector_connect_string, table_name=your_pgvector_table_name)
dbt_doc_resolver = LocalfsDBTDocResolver(manifest_json_path=your_manifest_json_path, catalog_json_path=your_catalog_json_path)

bot = ChatBot(doc_resolver=dbt_doc_resolver, vector_storage=vector_storage, tiktoken_provider=None)

bot.suggest_table("query the number of users who have purchased a product")

bot.suggest_sql("query the number of users who have purchased a product")
```

or initialize a chatdbt instance with environment variables:

```python

import os

os.environ["CHATDBT_I18N"] = "zh-cn"
os.environ["CHATDBT_VECTOR_STORAGE_TYPE"] = "pgvector"
os.environ[
    "CHATDBT_VECTOR_STORAGE_CONFIG_CONNECT_STRING"
] = your_pgvector_connect_string
os.environ["CHATDBT_VECTOR_STORAGE_CONFIG_TABLE_NAME"] = your_pgvector_table_name

os.environ["CHATDBT_DBT_DOC_RESOLVER_TYPE"] = "localfs"
os.environ["CHATDBT_DBT_DOC_RESOLVER_CONFIG_MANIFEST_JSON_PATH"] = your_manifest_json_path
os.environ["CHATDBT_DBT_DOC_RESOLVER_CONFIG_CATALOG_JSON_PATH"] = your_catalog_json_path

os.environ["OPENAI_API_KEY"] = your_openai_key

import chatdbt

chatdbt.suggest_table("query the number of users who have purchased a product")

chatdbt.suggest_sql("query the number of users who have purchased a product")
```
