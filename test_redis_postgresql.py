import asyncio
import os

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

async def main():
    r = redis.from_url(REDIS_URL, decode_responses=True)
    pong = await r.ping()
    print("redis ping:", pong)

    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
    async with engine.begin() as conn:
        val = await conn.execute(text("select 1"))
        print("db select 1:", val.scalar_one())

    await r.aclose()
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
