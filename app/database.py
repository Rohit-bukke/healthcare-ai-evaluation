"""
MongoDB Connection & Client Layer using PyMongo.
Supports local MongoDB instances and MongoDB Atlas with proper timeouts.
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database as PyMongoDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PyMongo MongoClient connection lifecycle and database access."""

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or settings.mongodb_uri
        self.db_name = db_name or settings.database_name
        self._client: Optional[MongoClient] = None
        self._cached_ping: Optional[dict] = None
        self._cached_ping_time: float = 0.0

    def get_client(self) -> MongoClient:
        """Returns or initializes the PyMongo client with connection pooling and timeouts."""
        if self._client is None:
            self._client = MongoClient(
                self.uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=3000,
                maxPoolSize=50,
                minPoolSize=5,
            )
        return self._client

    def get_database(self) -> PyMongoDatabase:
        """Returns the target MongoDB database instance."""
        client = self.get_client()
        return client[self.db_name]

    def ping(self) -> dict:
        """
        Safely checks connectivity to MongoDB server.
        Returns a dict indicating status, latency or error message without raising exceptions.
        """
        import time
        now = time.time()
        if self._cached_ping and (now - self._cached_ping_time) < 5.0:
            return self._cached_ping

        try:
            client = self.get_client()
            result = client.admin.command('ping')
            res = {
                "status": "connected",
                "database": self.db_name,
                "ping": result.get("ok", 1.0) == 1.0
            }
        except (ConnectionFailure, ServerSelectionTimeoutError) as err:
            logger.warning(f"MongoDB connection check failed: {err}")
            res = {
                "status": "disconnected",
                "database": self.db_name,
                "error": str(err)
            }
        except Exception as err:
            logger.error(f"Unexpected MongoDB error: {err}")
            res = {
                "status": "error",
                "database": self.db_name,
                "error": str(err)
            }

        self._cached_ping = res
        self._cached_ping_time = now
        return res

    def close(self):
        """Closes the MongoDB client connection if open."""
        if self._client is not None:
            self._client.close()
            self._client = None


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> PyMongoDatabase:
    """Helper function to retrieve active database instance."""
    return db_manager.get_database()
