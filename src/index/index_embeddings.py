from pathlib import Path

from index.indexer import Indexer
from index.title_mapper import TitleMapper
from inout import file_reader as f
from inout.redis_conn import RedisConnection

# Load Learned Embeddings Data
embedding_data: Path = (
    f.get_project_root() / "src" / "training_data" / "20230701_learned_embeddings.snappy"
)

# Instantiate indexer
indexer = Indexer(
    RedisConnection().conn(),
    embedding_data,
    "vector",
    "author",
    "title",
    "viberary",
    nvecs=800000,
    dim=768,
    max_edges=40,  # maximum allowed outgoing edges for each node in the graph in each layer.
    ef=200,  # maximum allowed potential outgoing edges candidates for each node in the graph
    distance_metric="COSINE",
    float_type="FLOAT64",
    index_type="HNSW",
)

# Create search index
# Delete existing index
indexer.drop_index()

# Recreate schema based on Indexer
indexer.create_search_index_schema()

# Load Embeddings
indexer.write_embeddings_to_search_index(columns=["title", "index", "author", "embeddings"])

# Check Search Index Metadata
indexer.get_search_index_metadata()