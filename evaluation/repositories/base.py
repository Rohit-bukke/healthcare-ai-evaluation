"""
Base Repository for MongoDB with safe fallback for testing/offline environments.
"""

import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic, Type
from pydantic import BaseModel
from pymongo.database import Database as PyMongoDatabase
from pymongo.errors import PyMongoError
from app.database import get_db, db_manager

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Generic repository providing CRUD operations on a PyMongo collection."""

    def __init__(self, collection_name: str, model_cls: Type[T], id_field: str = "_id"):
        self.collection_name = collection_name
        self.model_cls = model_cls
        self.id_field = id_field
        self._in_memory_store: Dict[str, Dict[str, Any]] = {}
        self._ensure_indexes_called = False

    def _get_collection(self):
        """Returns PyMongo collection if connected, else None."""
        try:
            ping_res = db_manager.ping()
            if ping_res.get("status") == "connected":
                db = get_db()
                collection = db[self.collection_name]
                if not self._ensure_indexes_called:
                    self.create_indexes(collection)
                    self._ensure_indexes_called = True
                return collection
        except Exception as err:
            logger.debug(f"MongoDB not available for collection {self.collection_name}: {err}")
        return None

    def create_indexes(self, collection):
        """Override in subclasses to specify MongoDB collection indexes."""
        pass

    def insert(self, entity: T) -> T:
        """Insert a domain model entity into MongoDB or in-memory store."""
        data = entity.model_dump(mode="json")
        key = str(data.get(self.id_field, data.get("id", "")))

        coll = self._get_collection()
        if coll is not None:
            try:
                # If _id isn't explicitly defined in model_dump, use key
                mongo_doc = data.copy()
                if self.id_field != "_id" and self.id_field in mongo_doc:
                    mongo_doc["_id"] = mongo_doc[self.id_field]
                coll.replace_one({"_id": mongo_doc["_id"]}, mongo_doc, upsert=True)
            except PyMongoError as err:
                logger.error(f"Error inserting into MongoDB {self.collection_name}: {err}")

        # Always update in-memory cache for fast read fallback
        self._in_memory_store[key] = data
        return entity

    def get_by_id(self, entity_id: str) -> Optional[T]:
        """Fetch entity by ID."""
        coll = self._get_collection()
        if coll is not None:
            try:
                doc = coll.find_one({"_id": entity_id}) or coll.find_one({self.id_field: entity_id})
                if doc:
                    doc.pop("_id", None)
                    return self.model_cls.model_validate(doc)
            except PyMongoError as err:
                logger.error(f"Error reading from MongoDB {self.collection_name}: {err}")

        # Fallback to in-memory store
        data = self._in_memory_store.get(entity_id)
        if data:
            return self.model_cls.model_validate(data)
        return None

    def list_all(self, filter_query: Optional[Dict[str, Any]] = None, limit: int = 100) -> List[T]:
        """List entities matching optional filter query."""
        filter_query = filter_query or {}
        coll = self._get_collection()
        if coll is not None:
            try:
                cursor = coll.find(filter_query).limit(limit)
                results = []
                for doc in cursor:
                    doc.pop("_id", None)
                    results.append(self.model_cls.model_validate(doc))
                return results
            except PyMongoError as err:
                logger.error(f"Error listing from MongoDB {self.collection_name}: {err}")

        # Fallback in-memory query
        results = []
        for data in self._in_memory_store.values():
            match = True
            for k, v in filter_query.items():
                if data.get(k) != v:
                    match = False
                    break
            if match:
                results.append(self.model_cls.model_validate(data))
                if len(results) >= limit:
                    break
        return results

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID."""
        deleted = False
        coll = self._get_collection()
        if coll is not None:
            try:
                res = coll.delete_one({"_id": entity_id})
                if res.deleted_count > 0:
                    deleted = True
            except PyMongoError as err:
                logger.error(f"Error deleting from MongoDB {self.collection_name}: {err}")

        if entity_id in self._in_memory_store:
            del self._in_memory_store[entity_id]
            deleted = True
        return deleted
