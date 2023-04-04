import logging
from typing import List
from chatdbt.model import DocMetaContainer, VectorStorage, Doc


class AtlasVectorStorage(VectorStorage):
    """Vector storage using Atlas"""

    def __init__(self, api_key: str, project_name: str):
        self.api_key = api_key
        self.project_name = project_name
        try:
            from nomic import AtlasProject  # pylint: disable=import-outside-toplevel
        except ImportError as ex:
            raise RuntimeError(
                f"{ex}\nPlease install nomic to use AtlasVectorStorage\npip install chatdbt[nomic]"
            )  # pylint: disable=raise-missing-from

        logging.debug("initializing Atlas project: %s", project_name)
        self.project = AtlasProject(
            name=project_name,
            modality="embedding",
            is_public=True,
            unique_id_field="foobar",
        )
        logging.debug("Atlas project: %s", self.project)

    def insert_doc(self, doc: Doc, vector: List[float]):
        """Insert a document into the vector storage"""
        with self.project.wait_for_project_lock():
            self.project.add_embeddings(
                data=[doc.get_metadata().dict()], embeddings=[vector]
            )

    def similarity_search(self, vector: List[float], k: int) -> List[DocMetaContainer]:
        """Search for similar documents in the vector storage"""
        with self.project.wait_for_project_lock():
            neighbors, _ = self.project.projections[0].vector_search([vector], k=k)
            datas = self.project.get_data(ids=neighbors)

        res = [DocMetaContainer(**datas[idx]) for idx in enumerate(neighbors)]
        return res
