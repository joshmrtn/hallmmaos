from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ProcessHealth(BaseModel):
    """Schema for resource usage of a single running process."""
    pid: int
    """Process ID."""
    name: str
    """Process name."""
    cpu_percent: float
    """CPU usage of this process."""
    memory_percent: float
    """Memory usage percent of this process."""
    status: str
    """Process status (e.g. 'running', 'sleeping')."""
    username: str
    """Username associated with this process."""

class SystemHealth(BaseModel):
    """Standardized schema for system resource snapshot."""
    timestamp: float
    """Unix timestamp."""
    cpu_utilization_percent: float
    """Total CPU usage percentage."""
    memory_total_mb: int
    """Total physical RAM available in MB."""
    memory_available_mb: int
    """Available physical RAM in MB."""
    memory_usage_percent: float
    """Percentage of total memory currently in use."""
    disk_usage_percent: float
    """Percentage of disk space used on the root partition."""
    network_io: Dict[str, Any]
    """Details about network I/O."""
    process_count: int
    """Total number of running processes on the system."""
    top_processes: List[ProcessHealth]
    """List of top resource-consuming processes."""
    # Optional field for platform-specific details
    extra_data: Optional[Dict[str, Any]] = None
    """Optional dictionary for misc. system data."""