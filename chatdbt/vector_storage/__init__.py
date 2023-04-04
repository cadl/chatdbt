from typing import Dict, Any
from chatdbt.model import VectorStorage


def get_vector_storage(
    vector_storage_type: str, vector_storage_config: Dict[str, Any]
) -> VectorStorage:
    """Get a vector storage instance"""
    if vector_storage_type == "atlas":
        from chatdbt.vector_storage.atlas import AtlasVectorStorage

        return AtlasVectorStorage(**vector_storage_config)
    elif vector_storage_type == "pgvector":
        from chatdbt.vector_storage.pgvector import PGVectorStorage

        return PGVectorStorage(**vector_storage_config)
    else:
        raise ValueError("Unknown vector storage type")
