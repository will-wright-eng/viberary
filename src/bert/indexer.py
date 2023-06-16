from src.io import file_reader as f
from src.bert.viberary_logging import ViberaryLogging

from io import TextIOWrapper


from pathlib import Path
from typing import IO, Dict, List, TypedDict


import csv
import importlib.resources

import sys

import numpy as np
from pandas import DataFrame
from redis import Redis
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.query import Query
from tqdm import tqdm
import pandas as pd

"""
Indexes embeddings from a file into a Redis instance
"""


class Indexer:
    def __init__(
        self,
        redis_conn,
        filepath,
        nvecs=0,
        dim=0,
        max_edges=0,
        ef=0,
        vector_field="",
        index_name="",
        distance_metric="COSINE",
        token_field_name="token",
        float_type="FLOAT64",
    ) -> None:
        self.conn = redis_conn
        self.filepath = filepath
        self.dim = dim
        self.nvecs = nvecs
        self.max_edges = max_edges
        self.ef = ef
        self.vector_field = vector_field
        self.token_field_name = token_field_name
        self.float_type = float_type
        self.index_name = index_name
        self.distance_metric = distance_metric
        self.logger = ViberaryLogging().setup_logging()

    def file_to_embedding_dict(self) -> Dict[str, List[float]]:
        """Reads Parquet file and process in Pandas, returning zipped dict of index and embeddings

        Returns:
            Dict[str, List[float]]: _description_
        """
        parquet = self.filepath

        self.logger.info(f"Creating dataframe from {parquet}...")
        pqt = pd.read_parquet(parquet)

        embedding_dict = dict(zip(pqt["index"], pqt["embeddings"]))

        return embedding_dict

    def delete_index(self):
        """Delete Redis index, will need to do to recreate"""
        self.logger.info(f"Deleting Redis index...")
        r = self.conn
        r.flushall()

    def create_index_schema(self) -> None:
        """Create Redis index with schema parameters from config"""

        r = self.conn

        schema = (
            VectorField(
                self.vector_field,
                "HNSW",
                {
                    "TYPE": self.float_type,
                    "DIM": self.dim,
                    "DISTANCE_METRIC": self.distance_metric,
                },
            ),
            TextField(self.token_field_name),
        )

        r.ft(self.index_name).create_index(schema)
        r.ft(self.index_name).config_set("default_dialect", 2)
        self.logger.info(f"Creating Redis schema: {schema}")

    def load_docs(self):
        r = self.conn

        vector_dict: Dict[str, List[float]] = self.file_to_embedding_dict()
        self.logger.info(f"Inserting vector into Redis index {self.index_name}")

        # an input dictionary from a dictionary
        for i, (k, v) in enumerate(vector_dict.items()):
            data = np.array(v, dtype=np.float64)
            np_vector = data.astype(np.float64)

            try:
                # write to Redis
                r.hset(k, mapping={self.vector_field: np_vector.tobytes()})
                self.logger.info(
                    f"Set {i} vector into Redis index as {self.vector_field}"
                )
            except Exception as e:
                self.logger.error("An exception occurred: {}".format(e))

    def get_index_metadata(self):
        r = self.conn
        metadata = r.ft(self.index_name).info()
        self.logger.info(
            f"name: {metadata['index_name']}, docs: {metadata['max_doc_id']}, time:{metadata['total_indexing_time']} seconds"
        )
