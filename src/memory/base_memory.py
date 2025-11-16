from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseMemory(ABC):
    """Abstract interface for storing and retrieving conversational history and long-term knowledge."""

    @abstractmethod
    def get_history(self, agent_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve recent conversation for the current context window.
        
        Args:
            agent_id (str): The unique id of the agent whose history to retrieve.
            limit (int): the maximum number of recent messages to return.
        Returns:
            A list of message dictionaries, where each dict typically contains 
            'role' ('user', 'assistant', etc.), 'sender_id', 'timestamp' and 'content' 
            (the message text).
        """
        pass
    
    @abstractmethod
    def add_message(self, agent_id: str, message: Dict[str, Any]):
        """
        Stores a new message to the history.

        Args:
            agent_id (str): The unique ID of the agent associated with the message.
            message (dict): The message dictionary, structured to include the rule, 
            sender id, timestamp, and content.
        """
        pass
    
    @abstractmethod
    def query_knowledge_base(self, agent_id: str, query: str, top_k: int = 3) -> List[str]:
        """
        Performs RAG lookup against long-term data.
        
        Args:
            agent_id (str): The unique ID of the agent to query the knowledge base for.
            query (str): The query or prompt fragment to search on.
            top_k (int): The maximum number of relevant documents/chunks to retrieve.

        Returns:
            A list of strings, where each string is a retrieved chunk of text relevant 
            to the query. Returns an empty list if no knowledge base exists.
        """
        pass

    @abstractmethod
    def clear_history(self, agent_id: str):
        """
        Permanently deletes all conversational history associated with a given agent ID.
        
        Args:
            agent_id: The unique ID of the agent whose history should be cleared.
        """
        pass