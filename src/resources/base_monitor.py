from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseResourceMonitor(ABC):
    """The abstract contract for sensing system state."""

    @abstractmethod
    def get_available_ram_mb(self) -> int:
        """
        Retrieves the amount of physical RAM available on the system.

        Returns:
            The available physical memory in megabytes (MB).
        """
        pass

    @abstractmethod
    def get_available_cpu_cores(self) -> float:
        """
        Retrieves the amount of CPU capacity currently available.

        Typically calculated as (Total Cores * (1 - Current Load)).

        Returns:
            The available CPU capacity expressed as a floating-point number of cores.
        """
        pass

    @abstractmethod
    def get_system_load_details(self) -> Dict[str, Any]:
        """
        Retrieves a detailed dictionary of system-wide load information.

        This may be useful for more sophisticated scheduling strategies that need 
        more than just RAM and CPU metrics.

        Returns:
            A dictionary containing various system load metrics.
        """
        pass