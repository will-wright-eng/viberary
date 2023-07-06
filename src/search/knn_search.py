import logging.config
from typing import List, Tuple

import numpy as np
from redis.commands.search.query import Query
from sentence_transformers import SentenceTransformer

from inout import file_reader as f
from search.sanitize_input import InputSanitizer


class KNNSearch:
    def __init__(
        self,
        redis_conn,
    ) -> None:
        self.conn = redis_conn
        self.index = "viberary"
        self.vector_field = "vector"
        self.title_field = "title"
        self.author_field = "author"
        logging.config.fileConfig(f.get_project_root() / "logging.conf")
        self.sanitizer = InputSanitizer()
        self.embedder = SentenceTransformer("sentence-transformers/msmarco-distilbert-base-v3")

    def vectorize_query(self, query_string) -> np.ndarray:
        query_embedding = self.embedder.encode(query_string, convert_to_tensor=False)
        return query_embedding

    def top_knn(
        self,
        query,
        top_k=10,
    ) -> List:
        """Return top 10 vector results from model

        Args:
            top_k (int, optional): Defaults to 10.
            query str: query string

        Returns:
            List: Returns list of tuple that includes the index, author, cosine similarity, and book title
        """
        r = self.conn
        sanitized_query = self.sanitizer.parse_and_sanitize_input(query)

        query_vector = self.vectorize_query(sanitized_query).astype(np.float64).tobytes()

        q = (
            Query(f"*=>[KNN {top_k} @{self.vector_field} $vec_param AS vector_score]")
            .sort_by("vector_score", asc=False)
            .paging(0, top_k)
            .return_fields("vector_score", self.vector_field, self.title_field, self.author_field)
            .dialect(2)
        )

        params_dict = {"vec_param": query_vector}

        results = r.ft(self.index).search(q, query_params=params_dict)
        results_docs = results.docs

        index_vector = []

        for i in results_docs:
            print(i)
            id = i["id"]  # book id
            score = i["vector_score"]
            title = i["title"]
            author = i["author"]
            index_vector.append((id, score, title, author))

        logging.info(f"query:{sanitized_query}, {i}, results:{index_vector}")

        scored_results = self.rescore(index_vector)

        return scored_results

    def rescore(self, result_list: List[Tuple[int, float, str, str]]) -> List:
        """Takes a ranked list of tuples
        Each tuple contains (index, cosine similarity, book title, book author)
        and returns ordinal scores for each
        cosine similarity for UI, and start at index 1
        """
        return [(val[2], val[3], index) for index, val in enumerate(result_list, 1)]