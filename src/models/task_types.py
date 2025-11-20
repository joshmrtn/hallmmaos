from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from enum import Enum
from datetime import datetime, timedelta

class TaskStatus(Enum):
    """
    The current state of a Task in the scheduling pipeline.
    """

    model_config = ConfigDict(
        frozen = True  # Tasks are immutable.
    )


    NEW = "NEW"
    """Task created, waiting for first scheduler pass. (Initial state)."""
    PENDING = "PENDING"
    """Task validated. Waiting to be executed."""
    RUNNING = "RUNNING"
    """Currently executing."""
    COMPLETED = "COMPLETED"
    """Execution finished successfully."""
    FAILED = "FAILED"
    """Execution stopped due to an error."""
    CANCELLED = "CANCELLED"
    """Stopped or expired."""

class Task(BaseModel):
    """
    A class representing an immutable, discrete unit of work for an agent.
    """

    task_id: str = Field(
        ..., description="A unique, immutable identifier for the task instance."
    )
    """A unique, immutable identifier for the task instance."""
    task_description: str = Field(
        default="", 
        description="The description of the task to complete. E.g., 'summarize this email...'"
    )
    """The description of the task to complete. E.g., 'summarize this email...'"""
    task_acceptance_criteria: str = Field(
        default="",
        description="The specific requirements for this task to be considered 'done'."
    )
    """The specific requirements for this task to be considered 'done'."""
    requires_human_acceptance: bool = Field(
        default=False,
        description="If True, a human must approve this task to mark it as complete."
    )
    """If True, a human must approve this task to mark it as complete."""
    deadline: datetime = Field(
        default = datetime.now() + timedelta(days=7),
        description="The deadline of the task. Defaults to 7 days from creation date."
    )
    """The deadline of the task. Defaults to 7 days from creation date."""
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
        default_factory=list,
        description="A list of task_id strings that are prerequisite to this task."
    )
    """A list of task_id strings that are prerequisite to this task."""
    blocking: List[str] = Field(
        default_factory=list,
        description="A list of task_id strings that this task is a prerequisite of."
    )
    """A list of task_id strings that this task is a prerequisite of."""
    correlation_ids: List[str] = Field(
        default_factory=list,
        description="A list of common identifiers linking related tasks (e.g.: 'project-123', 'userID:123')."
    )
    """A list of common identifiers linking related tasks (e.g.: 'project-123', 'userID:123')."""
    
    required_ram_mb: int = Field(
        4096,
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
    status: TaskStatus = Field(
        TaskStatus.NEW,
        description="The current state of the task. (e.g., PENDING, RUNNING, COMPLETED).",
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
    execution_metrics: Optional[dict] = Field(
        None,
        description=(
            "Actual execution metrics used to improve future execution estimations."
        )

    )
    """Actual execution metrics used to improve future execution estimations."""

