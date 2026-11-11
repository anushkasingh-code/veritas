"""
Async MongoDB Atlas Connection Manager using Motor.
Provides database initialization, graceful shutdown, health checks, and collection accessors.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton connection manager for MongoDB Atlas using Motor async client.
    """
    client: Optional[AsyncIOMotorClient] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Initializes the Motor AsyncIOMotorClient connection and sets up collection indexes.
        """
        if cls.client is None:
            logger.info("Initializing MongoDB client connection...")
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
            )
            # Verify connectivity and create indexes
            try:
                await cls.client.admin.command("ping")
                logger.info("MongoDB client connected successfully.")
                await cls._ensure_indexes()
            except Exception as e:
                logger.warning(f"MongoDB initial connection warning: {e}")

    @classmethod
    async def close(cls) -> None:
        """
        Closes the Motor AsyncIOMotorClient connection gracefully.
        """
        if cls.client is not None:
            logger.info("Closing MongoDB client connection...")
            cls.client.close()
            cls.client = None
            logger.info("MongoDB connection closed.")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """
        Returns the configured AsyncIOMotorDatabase instance.
        """
        if cls.client is None:
            # Fallback inline connection if invoked before explicit lifespan hook
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
        return cls.client[settings.MONGODB_DB_NAME]

    @classmethod
    def get_collection(cls, collection_name: Optional[str] = None) -> AsyncIOMotorCollection:
        """
        Returns a specific AsyncIOMotorCollection instance.
        Defaults to settings.MONGODB_COLLECTION_NAME.
        """
        name = collection_name or settings.MONGODB_COLLECTION_NAME
        return cls.get_db()[name]

    @classmethod
    async def _ensure_indexes(cls) -> None:
        """
        Ensures necessary database indexes are created on the research_analyses collection.
        """
        collection = cls.get_collection()
        try:
            # Index job_id for fast lookup
            await collection.create_index("job_id", unique=True)
            # Index created_at for chronological queries
            await collection.create_index("created_at")
            logger.info("MongoDB indexes verified on 'research_analyses' collection.")
        except Exception as e:
            logger.warning(f"Could not create MongoDB indexes: {e}")

    @classmethod
    async def check_health(cls) -> bool:
        """
        Pings the MongoDB server to verify health status.
        Returns True if healthy, False otherwise.
        """
        try:
            db = cls.get_db()
            await db.command("ping")
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False


# Functional helper exports matching standard FastAPI dependency patterns
async def init_db() -> None:
    """Initialize database connection."""
    await DatabaseManager.connect()


async def close_db() -> None:
    """Close database connection."""
    await DatabaseManager.close()


def get_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance."""
    return DatabaseManager.get_db()


def get_research_collection() -> AsyncIOMotorCollection:
    """Get MongoDB research_analyses collection instance."""
    return DatabaseManager.get_collection()


async def check_db_health() -> bool:
    """Check MongoDB database connectivity health."""
    return await DatabaseManager.check_health()
