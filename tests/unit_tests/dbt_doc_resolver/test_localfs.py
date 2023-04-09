import os
import pytest

from chatdbt.dbt_doc_resolver.localfs import LocalfsDBTDocResolver

TESTDATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "testdata"
)


MANIFEST_JSON_PATH = os.path.join(
    TESTDATA_DIR,
    "jaffle_shop",
    "manifest.json",
)

CATALOG_JSON_PATH = os.path.join(TESTDATA_DIR, "jaffle_shop", "catalog.json")


@pytest.fixture(scope="session")
def sample_resolver() -> LocalfsDBTDocResolver:
    resolver = LocalfsDBTDocResolver(MANIFEST_JSON_PATH, CATALOG_JSON_PATH)
    return resolver


def test_get_manifest_by_unique_id(sample_resolver: LocalfsDBTDocResolver):
    doc = sample_resolver.get_manifest_by_unique_id("model.jaffle_shop.customers")
    assert doc["resource_type"] == "model"
    assert doc["name"] == "customers"
    assert doc["schema"] == "dbt_alice"


def test_get_catalog_by_unique_id(sample_resolver: LocalfsDBTDocResolver):
    doc = sample_resolver.get_catalog_by_unique_id("model.jaffle_shop.customers")
    assert doc is not None
    assert doc["metadata"]["schema"] == "dbt_alice"
    assert doc["metadata"]["name"] == "customers"
    assert doc["columns"]["customer_id"]["type"] == "integer"


def test_list_model_unique_id(sample_resolver: LocalfsDBTDocResolver):
    unique_ids = sample_resolver.list_model_unique_id()
    assert len(unique_ids) == 5
