import json
from typing import Dict, List, Optional

from chatdbt.model import DBTDocResolver


class LocalfsDBTDocResolver(DBTDocResolver):
    def __init__(self, manifest_json_path: str, catalog_json_path: str):
        with open(manifest_json_path, "r", encoding="utf8") as manifest_f:
            self._dbt_docs_manifest = json.load(manifest_f)
        with open(catalog_json_path, "r", encoding="utf8") as catalog_f:
            self._dbt_docs_catalog = json.load(catalog_f)

    def get_manifest_by_unique_id(self, unique_id: str) -> Optional[Dict]:
        return self._dbt_docs_manifest["nodes"].get(unique_id)

    def get_catalog_by_unique_id(self, unique_id: str) -> Optional[Dict]:
        return self._dbt_docs_catalog["nodes"].get(unique_id)

    def list_model_unique_id(self) -> List[str]:
        res = []
        for model in self._dbt_docs_manifest["nodes"].values():
            if model["resource_type"] != "model":
                continue
            res.append(model["unique_id"])
        return res
