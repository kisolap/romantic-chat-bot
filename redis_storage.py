from redis.asyncio import Redis
from aiogram.fsm.storage.redis import RedisStorage

redis = Redis(host='localhost', port=6379, db=0)
storage = RedisStorage(redis=redis)