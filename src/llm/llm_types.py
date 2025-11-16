from typing import List, Dict
from pydantic import BaseModel

class SystemInstruction(BaseModel):
    """
    Encapsulates the system-level prompt defining the LLM's persona, rules, and constraints.
    """
    parts: List[Dict[str, str]]
    """The encapsulated instruction payload for the system-level prompt."""

class Content(BaseModel):
    """
    Encapsulates a part of the conversation history or the immediate user query.
    """
    role: str
    """The 'role' of the message sender (e.g. 'user', 'assistant', 'system)."""
    sender_id: str
    """The unique identifer of the sender (user id, agent_id, system)"""
    parts: List[Dict[str, str]]
    """The encapsulated data payload of a single message."""