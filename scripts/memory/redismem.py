"""Redis memory provider."""
from typing import Any, List, Optional
import redis
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.query import Query
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
import numpy as np

from memory.base import MemoryProviderSingleton, get_ada_embedding


SCHEMA = [
    TextField("namespace"),
    TextField("data"),
    VectorField(
        "embedding",
        "HNSW",
        {
            "TYPE": "FLOAT32",
            "DIM": 1536,
            "DISTANCE_METRIC": "COSINE"
        }
    ),
]


class RedisMemory(MemoryProviderSingleton):
    def __init__(self, cfg):
        """
        Initializes the Redis memory provider.

        Args:
            cfg: The config object.

        Returns: None
        """
        redis_host = cfg.redis_host
        redis_port = cfg.redis_port
        redis_password = cfg.redis_password
        self.dimension = 1536
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            db=0  # Cannot be changed
        )
        self.cfg = cfg
        if cfg.wipe_redis_on_start:
            self.redis.flushall()
        try:
            self.redis.ft(f"{cfg.memory_index}").create_index(
                fields=SCHEMA,
                definition=IndexDefinition(
                    prefix=["namespace:"],
                    index_type=IndexType.HASH
                )
            )
        except Exception as e:
            print("Error creating Redis search index: ", e)

    def add(self, data: str, namespace="default") -> str:
        """
        Adds a data point to the memory.

        Args:
            data: The data to add.

        Returns: Message indicating that the data has been added.
        """
        if 'Command Error:' in data:
            return ""
        vector = get_ada_embedding(data)
        vector = np.array(vector).astype(np.float32).tobytes()
        data_dict = {
            "namespace": namespace,
            b"data": data,
            "embedding": vector
        }

        base_key = f"namespace:{namespace}"
        vec_num = self.redis.get(f"{base_key}-vec_num")
        vec_num = int(vec_num.decode('utf-8')) + 1 if vec_num else 0
        doc_id = f"{base_key}:{vec_num}"

        pipe = self.redis.pipeline()
        pipe.hset(doc_id, mapping=data_dict)
        _text = f"Inserting data into memory at index: {vec_num}:\n"\
            f"data: {data}"
        pipe.set(f'{base_key}-vec_num', vec_num)
        pipe.execute()
        return _text

    def get(self, data: str, namespace="default") -> Optional[List[Any]]:
        """
        Gets the data from the memory that is most relevant to the given data.

        Args:
            data: The data to compare to.

        Returns: The most relevant data.
        """
        return self.get_relevant(data, 1, namespace=namespace)

    def clear(self) -> str:
        """
        Clears the redis server.

        Returns: A message indicating that the memory has been cleared.
        """
        self.redis.flushall()
        return "Obliviated"

    def get_relevant(
        self,
        data: str,
        num_relevant: int = 5,
        namespace="default"
    ) -> Optional[List[Any]]:
        """
        Returns all the data in the memory that is relevant to the given data.
        Args:
            data: The data to compare to.
            num_relevant: The number of relevant data to return.

        Returns: A list of the most relevant data.
        """
        query_embedding = get_ada_embedding(data)
        base_query = f"(@namespace:{namespace})=>[KNN {num_relevant} @embedding $vector AS vector_score]"
        query = Query(base_query).return_fields(
            "data",
            "vector_score"
        ).sort_by("vector_score").dialect(2)
        query_vector = np.array(query_embedding).astype(np.float32).tobytes()

        try:
            results = self.redis.ft(f"{self.cfg.memory_index}").search(
                query, query_params={"vector": query_vector}
            )
        except Exception as e:
            print("Error calling Redis search: ", e)
            return None
        return [result.data for result in results.docs]

    def get_stats(self):
        """
        Returns: The stats of the memory index.
        """
        return self.redis.ft(f"{self.cfg.memory_index}").info()
