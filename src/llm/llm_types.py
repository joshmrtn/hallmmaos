from typing import List, Dict, Optional
from pydantic import BaseModel

class ContentPart(BaseModel):
    """A single segment of a message content."""
    text: str
    """The raw text of a part of a message."""
    type: str = "text" # or 'thought' or 'code_result' or 'image_url',...
    """The type of the message part, such as 'thought' or 'code_result' or 'image_url'."""
    metadata: Optional[Dict[str, str]] = None
    """Structural information that isn't the raw content but is necessary for rendering or processing."""

class Content(BaseModel):
    """
    Encapsulates a part of the conversation history or the immediate user query.
    """
    role: str
    """The 'role' of the message sender (e.g. 'user', 'assistant', 'system)."""
    sender_id: str
    """The unique identifer of the sender (user id, agent_id, system)"""
    parts: List[ContentPart]
    """The encapsulated data payload of a single message."""

class SystemInstruction(BaseModel):
    """
    Encapsulates the system-level prompt defining the LLM's persona, rules, and constraints.
    """
    parts: List[ContentPart]
    """The encapsulated instruction payload for the system-level prompt."""
