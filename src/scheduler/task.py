from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Task(BaseModel):
    """
    A class representing an immutable, discrete unit of work for an agent.
    """

    task_id: str = Field(
        ..., description="A unique, immutable identifier for the task instance."
    )
    """A unique, immutable identifier for the task instance."""
    agent_id: str = Field(
        ..., description="The id of the agent assigned to this task."
    )
    """The id of the agent assigned to this task."""

    source_domain: str = Field(
        ..., description="The domain name where this task originates from."
    )
    """The domain name where this task originates from."""
    source_topic: str = Field(
        ..., description="The topic (thread) where this task originates from."
    )
    """The topic (thread) where this task originates from."""
    input_message: str = Field(
        ..., description="The raw message content where this task originates from."
    )
    """The raw message content where this task originates from."""

    priority: int = Field(
        ..., ge=1, le=10, description="The task's priority level (1=Highest, 10=Lowest)"
    )
    """The task's priority level (1=Highest, 10=Lowest)"""
    blocked_by: List[str] = Field(
        ...,
        description="A list of task_id strings that are prerequisite to this task."
    )
    """A list of task_id strings that are prerequisite to this task."""
    blocking: List[str] = Field(
        ...,
        description="A list of task_id strings that this task is a prerequisite of."
    )
    """A list of task_id strings that this task is a prerequisite of."""
    required_ram_mb: int = Field(
        1024,
        ge=1,
        description="Estimated RAM in MB required for task execution."
    )
    """Estimated RAM in MB required for task execution."""
    required_cpu_cores: float = Field(
        0.5,
        ge=0.01,
        description="Estimated CPU cores/fraction required for task execution."
    )
    """Estimated CPU cores/fraction required for task execution."""
    status: str = Field(
        "PENDING",
        description="The current state of the task. (e.g., PENDING, RUNNING, COMPLETE).",
    )
    """The current state of the task. (e.g., PENDING, RUNNING, COMPLETE)."""
    duration_estimate_sec: Optional[float] = Field(
        None, description="The estimated time in seconds this task will take."
    )
    """The estimated time in seconds this task will take."""
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="The immutable timestamp of when the task was created."
    )
    """The immutable timestamp of when the task was created."""
    checkpoint_data: Optional[dict] = Field(
        None,
        description=(
            "Minimal state data required to pause and resume the task (e.g. last token, "
            "internal planner state)."
        )
    )
    """Minimal state data required to pause and resume the task."""

    class Config:
        frozen = True  # Tasks are immutable.
