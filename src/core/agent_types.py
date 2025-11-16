from typing import Dict, Any, List
from pydantic import BaseModel

class AgentConfig(BaseModel):
    """The standardized schema for all agent configurations."""
    agent_id: str
    """The unique ID of the agent."""
    name: str
    """A human-readable name for the agent."""
    model_key: str
    """The LLM model for this agent (e.g.: "phi3:mini")"""
    system_prompt: Dict[str, Any]
    """The system instructions from llm_types.SystemInstruction.parts."""
    enabled_tools: List[str]
    """A list of tools this agent may call."""
    access_domains: List[str]
    """A list of domains (channels, streams) this agent has access to."""