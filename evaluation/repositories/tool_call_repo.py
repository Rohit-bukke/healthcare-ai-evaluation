"""
Repository for Tool Calls.
"""

from app.models.tool_call import ToolCall
from evaluation.repositories.base import BaseRepository


class ToolCallRepository(BaseRepository[ToolCall]):
    """Repository managing tool call records."""

    def __init__(self):
        super().__init__(collection_name="tool_calls", model_cls=ToolCall, id_field="tool_id")

    def create_indexes(self, collection):
        try:
            collection.create_index("tool_id", unique=True)
            collection.create_index("tool_name")
            collection.create_index("status")
        except Exception:
            pass
