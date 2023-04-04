from typing import Dict
from chatdbt.model import DBTDocResolver


def get_dbt_doc_resolver(
    dbt_doc_resolver_type: str, dbt_doc_resolver_config: Dict[str, str]
) -> DBTDocResolver:
    if dbt_doc_resolver_type == "localfs":
        from .localfs import LocalfsDBTDocResolver

        return LocalfsDBTDocResolver(**dbt_doc_resolver_config)
    else:
        raise ValueError("Unknown dbt doc resolver type")
