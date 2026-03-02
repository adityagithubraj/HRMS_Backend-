from typing import AsyncGenerator

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import get_settings


settings = get_settings()

_client: AsyncIOMotorClient | None = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    client = get_client()
    return client[settings.DATABASE_NAME]


async def get_db_dependency() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    db = get_db()
    try:
        yield db
    finally:
        # Motor manages connection pooling automatically; no explicit close per request.
        pass

