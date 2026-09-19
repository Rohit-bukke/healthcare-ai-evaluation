"""
Repository for Conversation Turns.
"""

from typing import List
from app.models.conversation import ConversationTurn
from evaluation.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[ConversationTurn]):
    """Repository managing ConversationTurn execution history."""

    def __init__(self):
        super().__init__(collection_name="conversations", model_cls=ConversationTurn, id_field="turn_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("turn_id", unique=True)
            collection.create_index("role")
            collection.create_index("timestamp")
        except Exception:
            pass
