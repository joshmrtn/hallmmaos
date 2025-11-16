from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class BaseChatAdapter(ABC):
    """Abstract interface for all chat systems."""

    @abstractmethod
    def get_new_messages(self, agent_id: str) -> list:
        """
        Polls or listens for new messages addressed to the agent in subscribed domains.
        Returns a list of structured message events.

        Args:
            agent_id (str): The unique id of the agent whose messages to check.

        Returns:
            A list of structured message events (Dicts).
        """
    pass

    @abstractmethod
    def send_message(
        self, 
        recipient_id: str, 
        content: str, 
        context_data: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
        """
        Sends a new unthreaded message to the specified recipient (user, channel, agent).

        Args:
            recipient_id (str): The unique ID of the target user or channel/domain.
            content (str): The text content of the message.
            context_data (Dict[str, Any], optional): Optional platform-specific data 
                (e.g., domain/topic names) needed for the initial delivery.

        Returns:
            A dictionary containing the successful response, typically including the 
            new message's platform specific ID.        
        """
        pass

    @abstractmethod
    def reply_to_message(
        self,
        thread_id: str,
        content: str,
        message_to_reply_id: str
    ) -> Dict[str, Any]:
        """
        Sends a message specifically to reply to another message.

        Args:
            thread_id (str): The identifier for the thread/conversation.
            content (str): The text content of the reply.
            message_to_reply_id (str): The ID of the message this reply is responding to.

        Returns:
            A dictionary containing the successful response.
        """
        pass

    @abstractmethod
    def get_conversation_context(
        self,
        thread_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Retrieves a list of prior messages in a specified conversation thread.

        Args:
            thread_id (str): The identifier for the conversation thread.
            limit (int): The maximum number of prior messages to retrieve.
        """
        pass