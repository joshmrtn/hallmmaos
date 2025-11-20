from typing import List, Dict, Any, Optional
import logging

# LangChain Imports
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from src.llm.base_text_llm import BaseTextLLM
from src.llm.llm_types import Content, SystemInstruction
from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class OllamaTextLLM(BaseTextLLM):
    """
    Concrete implementation of BaseTextLLM using Ollama via LangChain.

    This class is stateless regarding the model. It instantiates the specific 
    Ollama model requested by the model_key argument for each generation call.
    """

    def __init__(self, config_manager: ConfigManager):
        """Instantiates a new OllamaTextLLM object."""
        self._config = config_manager
        llm_config = self._config.get("llm", {})

        self.base_url = llm_config.get("base_url", "http://localhost::11434")


    def _convert_history_to_messages(self, history: List[Content]) -> List[BaseMessage]:
        """Converts internal Content objects to LangChain Message objects."""
        messages = []
        for content in history:
            # Flatten parts into a single string for now.
            # Future TODO: Handle different kinds of message parts. For now, handles only text.
            text_parts = [p.text for p in content.parts if p.type in ['text', 'thought', 'code_result']]
            full_text = "\n".join(text_parts)

            if not full_text.strip():
                continue
            
            if content.role == 'user':
                messages.append(HumanMessage(content=full_text))
            elif content.role == 'assistant':
                messages.append(AIMessage(content=full_text))
            elif content.role == 'system':
                messages.append(SystemMessage(content=full_text))
                
        return messages

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
        backoff_factor: float = 2.0
    ) -> Dict[str, Any]:
        """
        Generates content using a specific Ollama model with specific settings.
        """
        
        # 1. Prepare Messages
        messages: List[BaseMessage] = []
        
        # Add System Instruction if present
        if system_instruction:
            sys_parts = [p.text for p in system_instruction.parts]
            messages.append(SystemMessage(content="\n".join(sys_parts)))
            
        # Add History
        messages.extend(self._convert_history_to_messages(history))
        
        # Add current User Query
        messages.append(HumanMessage(content=user_query))
        
        # 2. Instantiate the specific model requested by the Agent
        # We create a fresh instance per call to ensure thread safety and 
        # correct model selection.
        llm = ChatOllama(
            base_url=self.base_url,
            model=model_key,
            temperature=temperature,
            num_ctx=max_tokens if max_tokens else 8192,
        )

        # 3. Bind Tools if present
        if tools:
            llm = llm.bind_tools(tools)

        # 4. Configure retries
        llm_with_retry = llm.with_retry(
            stop_after_attempt=retries + 1,
            wait_exponential_jitter=False,
            # TODO: configure to actually use exponential backoff factor
        )


        # 5. Execute
        try:
            response = llm_with_retry.invoke(messages)
            
            # 5. Parse Response into Standard Dict
            result = {
                "content": response.content,
                "model_used": model_key,
                "tool_calls": [],
                "raw_response": response.response_metadata # Capture metadata like token usage
            }
            
            # Check for tool calls in the LangChain response object
            if response.tool_calls:
                result["tool_calls"] = response.tool_calls
                
            return result

        except Exception as e:
            logger.error(f"LLM Generation failed for model {model_key}: {e}")
            raise e

    def parse_tool_call(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parses the output to extract tool calls. 
        
        Since we used LangChain's bind_tools, the tool calls are likely 
        already parsed in the 'tool_calls' key of our result dict.
        """
        return response.get("tool_calls", [])