from typing import Union, Any
import json
import redis
from ..config import REDIS_URL


class Redis:
    def __init__(self, url: str) -> None:
        """
        Setup Redis instance
        """
        self.instance = redis.from_url(url)

    def set(self, key: Union[bytes, str], data, ex: float = None):
        """
        Serialize and store python object in
        redis store.
        """
        serialized_data = json.dumps(data)
        self.instance.set(key, serialized_data, ex=ex)

    def get(self, key: Union[bytes, str]) -> Any:
        serialized_data = self.instance.get(key)
        data = json.loads(serialized_data)
        return data


redis_backend = Redis(REDIS_URL)
