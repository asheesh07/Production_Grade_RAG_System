class Cache_client:
    def __init__(self,client:redis.Redis):
        self.client=client
    def get(self,key):
        try:
            value=self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (RedisError, json.JSONDecodeError) as e:
            return None
    def set(self,key,value,ttl):
        try:
            payload=json.dumps(value)
            self.client.set(key,payload,ex=ttl)
        except (RedisError,TextError) as e:
            return None
        
    def delete(self,key):
            try:
                self.client.delete(key)
            except RedisError as e:
                return None
            
    def ping(self):
        try:
            return self.client.ping()
        except RedisError as e:
            return False
def init_cache(settings):
    try:
        redis_client=redis.Redis(
            host=settings.reddis_host,
            port=settings.redis_port,
            password=settings.redis_password,
            decode_responses=True,
            socket_timeout=5
            
        )
        redis_client.ping()
        return Cache_client(redis_client)
    except RedisError as e:
        raise RuntimeError("Cache unavailable") from e
    
async def close_cache(cache:Cache_client):
    try:
         cache._client.close()
    except Exception as e:
        pass
def _hash_key(prefix: str, raw: str) -> str:
    """
    Generate stable cache keys for AI workloads.
    """
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def get_cached_embedding(
    cache: CacheClient,
    text: str,
) -> Optional[list]:
    """
    Retrieve cached embedding for input text.
    """
    key = _hash_key("embedding", text)
    return cache.get(key)


def set_cached_embedding(
    cache: CacheClient,
    text: str,
    embedding: list,
    ttl: int,
):
    """
    Cache embedding vector.
    """
    key = _hash_key("embedding", text)
    cache.set(key, embedding, ttl)


def get_cached_response(
    cache: CacheClient,
    prompt: str,
) -> Optional[str]:
    """
    Retrieve cached LLM response.
    """
    key = _hash_key("response", prompt)
    return cache.get(key)


def set_cached_response(
    cache: CacheClient,
    prompt: str,
    response: str,
    ttl: int,
):
    """
    Cache LLM response.
    """
    key = _hash_key("response", prompt)
    cache.set(key, response, ttl)
