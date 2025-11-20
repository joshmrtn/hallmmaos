from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .llm_types import Content, SystemInstruction

class BaseTextLLM(ABC):
    """
    Abstract interface for text generating LLM technologies.

    This class defines the service contract for all text-based LLM implementations, 
    ensuring the Orchestrator and Agents remain decoupled from specific model 
    implementations.
    """

    @abstractmethod
    def generate_content(
        self, 
        history: List[Content],
        user_query: str,
        model_key: str,
        system_instruction: Optional[SystemInstruction] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        retries: int = 3,
        backoff_factor: float = 2.0,
        **kwargs
        ) -> Dict[str, Any]:
        """
        Send a request to the LLM to generate text based on context.
        
        This is the primary method for generation.
        
        Args:
            history (Content[]): The list of Content objects representing the prior conversation 
                                 to establish context.
            user_query (str): The immediate user message or prompt to respond to.
            model_key (str): The specific model to call (e.g., 'llama3:8b').
            system_instruction (SystemInstruction): Optional. Define's model's persona, rules, and 
                                                    constraints for the current request.
            tools (Dict[]): A list of available tools the model can use.
            temperature (float): The 'temperature' setting to use. Default 0.7.
            max_tokens (Optional int): Maximum number of tokens for context window. 
            retries (int): The maximum number of times to retry an API call on transient errors.
            backoff_factor (float): The exponential factor for wait time between retries.
            kwargs (Any): additional keyword arguments for specific platforms.

        Returns:
            A dictionary containing the full response from the LLM, including the generated 
            text and metadata (model used, tool calls, citations, etc).
        """
        pass
    
    @abstractmethod
    def parse_tool_call(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses the raw LLM output to detect if it wants to use a tool.

        Args:
            response (dict): The raw dictionary response returned by the generate_content method.
        
        Returns: 
            A list of dictionaries, where each dictionary represents a tool call 
            in a standardized format. Returns an empty list if no tool calls are present.
        """
        pass
