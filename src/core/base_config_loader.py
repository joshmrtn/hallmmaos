from abc import ABC, abstractmethod
from typing import List
from .agent_types import AgentConfig

class BaseConfigLoader(ABC):
    """
    Abstract interface for loading, parsing, and validating configurations.
    """

    @abstractmethod
    def load_all_configs(self) -> List[AgentConfig]:
        """
        Loads and validates configurations for all known agents from all defined 
        storage layers (e.g.: /etc/ and /var/lib/).

        Returns:
            A list of validated AgentConfig objects.
        """
        pass

    @abstractmethod
    def save_dynamic_config(self, config: AgentConfig) -> None:
        """
        Saves a configuration for a dynamically created agent to the application 
        writable storage layer (e.g.: /var/lib/hallmmaos/dynamic_agents/).

        Args:
            config (AgentConfig): The AgentConfig object to be saved.
        """
        pass