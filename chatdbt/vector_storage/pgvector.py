import json
import logging
import datetime
from sqlalchemy import Column, create_engine, Integer, VARCHAR, DateTime
from sqlalchemy.dialects.postgresql import insert
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Session, declarative_base
from chatdbt.model import VectorStorage, Doc, DocMetaContainer

from typing import List


Base = declarative_base()


class PGVectorStorage(VectorStorage):
    def _orm_for(self, table_name):
        class Item(Base):
            __tablename__ = table_name
            id = Column(Integer, primary_key=True, autoincrement=True)
            unique_id = Column(VARCHAR, unique=True)
            embedding = Column(Vector(1536))
            data_metadata = Column(JSON)
            created_at = Column(DateTime, default=datetime.datetime.utcnow)
            updated_at = Column(
                DateTime,
                default=datetime.datetime.utcnow,
                onupdate=datetime.datetime.utcnow,
            )

        return Item

    def __init__(self, connect_string: str, table_name: str):
        self.connect_string = connect_string
        self.table_name = table_name
        self._engine = create_engine(connect_string)
        self._conn = self._engine.connect()

        self._table = self._orm_for(table_name)
        self._create_tables()

    def _create_tables(self):
        Base.metadata.create_all(self._engine)

    def insert_doc(self, doc: Doc, vector: List[float]):
        logging.debug("inserting doc: %s, %s", doc, vector[:5])
        unique_id = doc.get_unique_id()
        with Session(self._conn) as session:
            values = dict(
                unique_id=unique_id,
                embedding=vector,
                data_metadata=doc.get_metadata().json(),
                updated_at=datetime.datetime.utcnow(),
            )

            stmt = (
                insert(self._table)
                .values(
                    **values,
                )
                .on_conflict_do_update(
                    index_elements=["unique_id"],
                    set_=values,
                )
            )
            session.execute(stmt)
            session.commit()

    def similarity_search(self, vector: List[float], k: int) -> List[DocMetaContainer]:
        with Session(self._conn) as session:
            res = (
                session.query(self._table)
                .order_by(self._table.embedding.cosine_distance(vector))
                .limit(k)
                .all()
            )
        return [
            DocMetaContainer.parse_obj(json.loads(item.data_metadata)) for item in res
        ]
