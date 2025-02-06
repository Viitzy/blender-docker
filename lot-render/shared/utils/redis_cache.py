import json
import os
import redis
from shared.utils.json_encoder import json_encoder

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    password=os.getenv("REDIS_PW"),
)


def check_cache(key: str):
    # verificar se há uma resposta no cache do Redis
    cached_response = redis_client.get(key)
    if cached_response:
        return json.loads(cached_response)

    return None


def set_cache(key: str, value: str, expiration: int = 604800):
    # armazenar o resultado no cache do Redis
    redis_client.setex(key, expiration, json.dumps(value, default=json_encoder))
