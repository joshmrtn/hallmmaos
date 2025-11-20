import pytest
from unittest.mock import MagicMock, patch, ANY
from src.llm.ollama_text_llm import OllamaTextLLM
from src.config.config_manager import ConfigManager
from src.llm.llm_types import Content, SystemInstruction, ContentPart

# --- Fixtures ---

@pytest.fixture
def mock_config():
    """Mocks the ConfigManager to provide a predictable base_url."""
    config = MagicMock(spec=ConfigManager)
    config.get.return_value = {"base_url": "http://test-ollama:11434"}
    return config

@pytest.fixture
def ollama_llm(mock_config):
    """Creates an instance of OllamaTextLLM with the mocked config."""
    return OllamaTextLLM(mock_config)

# --- Tests ---

@patch("src.llm.ollama_text_llm.ChatOllama")
def test_generate_content_initializes_correct_model(mock_chat_cls, ollama_llm):
    """
    Verifies that ChatOllama is initialized with the specific model_key,
    temperature, and context settings passed to generate_content.
    """
    # Setup Mock
    mock_instance = mock_chat_cls.return_value
    # Mock the with_retry chain
    mock_retry_wrapper = mock_instance.with_retry.return_value
    mock_retry_wrapper.invoke.return_value.content = "Test response"
    mock_retry_wrapper.invoke.return_value.tool_calls = []
    mock_retry_wrapper.invoke.return_value.response_metadata = {}

    # Arguments
    history = []
    user_query = "Hello"
    model_key = "phi3:mini"
    
    # Act
    ollama_llm.generate_content(
        history=history, 
        user_query=user_query, 
        model_key=model_key,
        temperature=0.5,
        max_tokens=4096
    )

    # Assert
    # Verify ChatOllama was initialized with specific runtime params
    mock_chat_cls.assert_called_with(
        base_url="http://test-ollama:11434", # From config
        model="phi3:mini",                 # From arg
        temperature=0.5,                   # From arg
        num_ctx=4096                       # From arg
    )

@patch("src.llm.ollama_text_llm.ChatOllama")
def test_generate_content_formats_messages_correctly(mock_chat_cls, ollama_llm):
    """
    Verifies that internal Content/ContentPart objects are correctly converted 
    to LangChain's SystemMessage, HumanMessage, and AIMessage.
    """
    # Setup Mock
    mock_instance = mock_chat_cls.return_value
    mock_retry_wrapper = mock_instance.with_retry.return_value
    mock_retry_wrapper.invoke.return_value.content = "Response"
    mock_retry_wrapper.invoke.return_value.tool_calls = []
    mock_retry_wrapper.invoke.return_value.response_metadata = {}

    # Data Setup
    sys_instruction = SystemInstruction(parts=[ContentPart(text="Be helpful")])
    
    history = [
        Content(
            role="user", 
            sender_id="u1", 
            parts=[ContentPart(text="Hi")]
        ),
        Content(
            role="assistant", 
            sender_id="a1", 
            parts=[
                ContentPart(text="Thinking...", type="thought"), # Should be included in context
                ContentPart(text="Hello there", type="text")
            ]
        )
    ]
    query = "How are you?"

    # Act
    ollama_llm.generate_content(
        history, 
        query, 
        "llama3", 
        system_instruction=sys_instruction
    )

    # Assert
    # We check the args passed to invoke() on the *retry wrapper*
    call_args = mock_retry_wrapper.invoke.call_args
    passed_messages = call_args[0][0]

    # 1. System Prompt
    assert passed_messages[0].type == "system"
    assert passed_messages[0].content == "Be helpful"
    
    # 2. User History
    assert passed_messages[1].type == "human"
    assert passed_messages[1].content == "Hi"
    
    # 3. Assistant History (Should combine thought + text)
    assert passed_messages[2].type == "ai"
    assert "Thinking..." in passed_messages[2].content
    assert "Hello there" in passed_messages[2].content
    
    # 4. Current Query
    assert passed_messages[3].type == "human"
    assert passed_messages[3].content == "How are you?"

@patch("src.llm.ollama_text_llm.ChatOllama")
def test_generate_content_uses_retries(mock_chat_cls, ollama_llm):
    """
    Verifies that the LangChain .with_retry() method is applied to the LLM
    before invocation, using the passed retry parameters.
    """
    mock_instance = mock_chat_cls.return_value
    mock_retry_wrapper = mock_instance.with_retry.return_value
    
    # Setup a successful response
    mock_retry_wrapper.invoke.return_value.content = "Success"
    mock_retry_wrapper.invoke.return_value.tool_calls = []
    mock_retry_wrapper.invoke.return_value.response_metadata = {}

    # Act
    ollama_llm.generate_content(
        [], 
        "hi", 
        "test-model", 
        retries=5
    )

    # Assert
    # Check that .with_retry was called on the raw LLM instance
    mock_instance.with_retry.assert_called_once()
    
    # Check args: LangChain stop_after_attempt is usually retries + 1
    _, kwargs = mock_instance.with_retry.call_args
    assert kwargs['stop_after_attempt'] == 6 

    # Assert that invoke was called on the WRAPPER, not the raw instance
    mock_retry_wrapper.invoke.assert_called_once()
    mock_instance.invoke.assert_not_called()

@patch("src.llm.ollama_text_llm.ChatOllama")
def test_generate_content_binds_tools(mock_chat_cls, ollama_llm):
    """Verifies that if tools are provided, .bind_tools() is called."""
    mock_instance = mock_chat_cls.return_value
    # When bind_tools is called, it returns a new bound runnable
    mock_bound_llm = mock_instance.bind_tools.return_value
    # Then with_retry is called on that bound llm
    mock_retry_wrapper = mock_bound_llm.with_retry.return_value
    
    mock_retry_wrapper.invoke.return_value.content = "Using tool"
    mock_retry_wrapper.invoke.return_value.tool_calls = []
    mock_retry_wrapper.invoke.return_value.response_metadata = {}

    tools = [{"name": "test_tool", "description": "does stuff"}]

    # Act
    ollama_llm.generate_content([], "use tool", "model", tools=tools)

    # Assert
    mock_instance.bind_tools.assert_called_once_with(tools)
    # Ensure the retry wrapper was created from the bound LLM
    mock_bound_llm.with_retry.assert_called_once()