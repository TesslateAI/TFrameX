
import pytest
import logging
import os
import sys # For sys.stdout.isatty()
from pathlib import Path
from unittest.mock import MagicMock, patch

from tframex.util.logging import setup_logging, LLMInteraction, LLMInteractionFormatter
from tframex.models.primitives import Message, ToolCall, FunctionCall

# Helper to ensure logging handlers are closed and removed
def reset_logging_state():
    # Close and remove handlers from root logger
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers): # Iterate over a copy
        try:
            handler.acquire() # Ensure thread safety for closing
            handler.close()
        except Exception:
            pass # Ignore errors during close, e.g., if already closed
        finally:
            if hasattr(handler, 'release'): # Check if release exists, some handlers might not
                 handler.release()
        root_logger.removeHandler(handler)
    
    # Close and remove handlers from llm_interaction logger
    llm_logger = logging.getLogger("llm_interaction")
    for handler in list(llm_logger.handlers):
        try:
            handler.acquire()
            handler.close()
        except Exception:
            pass
        finally:
            if hasattr(handler, 'release'):
                handler.release()
        llm_logger.removeHandler(handler)
    llm_logger.handlers = [] # Ensure it's empty
    root_logger.handlers = [] # Ensure root is also empty

@pytest.fixture(autouse=True)
def cleanup_logs():
    reset_logging_state() # Ensure handlers are closed before trying to delete files
    
    log_dir = Path("logs")
    general_log = log_dir / "tframex.log"
    llm_log = log_dir / "llm_interactions.log"
    
    if general_log.exists():
        try:
            os.remove(general_log)
        except PermissionError:
            print(f"Warning: Could not remove {general_log} due to PermissionError in fixture setup.")
            pass # Try to continue if cleanup fails, test might still pass if logging setup handles it
    if llm_log.exists():
        try:
            os.remove(llm_log)
        except PermissionError:
            print(f"Warning: Could not remove {llm_log} due to PermissionError in fixture setup.")
            pass

    yield # Run tests

    reset_logging_state() # Ensure handlers are closed after test
    if general_log.exists():
        try:
            os.remove(general_log)
        except PermissionError:
             print(f"Warning: Could not remove {general_log} due to PermissionError in fixture teardown.")
    if llm_log.exists():
        try:
            os.remove(llm_log)
        except PermissionError:
            print(f"Warning: Could not remove {llm_log} due to PermissionError in fixture teardown.")

    if log_dir.exists() and not any(log_dir.iterdir()):
        try:
            os.rmdir(log_dir)
        except OSError: # Can fail if other files are present or dir is locked
             print(f"Warning: Could not remove log directory {log_dir}.")


def test_setup_logging_save_to_file_true():
    setup_logging(level=logging.DEBUG, save_to_file=True, use_colors=False) # Disable colors for file check simplicity
    assert os.path.exists("logs/tframex.log")
    assert os.path.exists("logs/llm_interactions.log")
    
    root_logger = logging.getLogger()
    assert any(isinstance(h, logging.FileHandler) and Path(h.baseFilename).name == "tframex.log" for h in root_logger.handlers)
    
    llm_logger = logging.getLogger("llm_interaction")
    assert any(isinstance(h, logging.FileHandler) and Path(h.baseFilename).name == "llm_interactions.log" for h in llm_logger.handlers)
    assert not llm_logger.propagate

def test_setup_logging_save_to_file_false():
    setup_logging(level=logging.DEBUG, save_to_file=False, use_colors=False)
    
    # The cleanup_logs fixture will try to remove these if they existed from previous tests
    # So, the primary assertion is that no *new* files are created by this call.
    # It's harder to assert non-existence if the fixture fails to clean perfectly.
    # A robust way is to check *before* and *after* if save_to_file=False
    
    assert not os.path.exists("logs/tframex.log"), "tframex.log should not exist when save_to_file=False"
    assert not os.path.exists("logs/llm_interactions.log"), "llm_interactions.log should not exist when save_to_file=False"
    
    root_logger = logging.getLogger()
    assert not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)
    
    llm_logger = logging.getLogger("llm_interaction")
    assert not any(isinstance(h, logging.FileHandler) for h in llm_logger.handlers)
    assert llm_logger.propagate

def test_llm_interaction_formatter():
    formatter = LLMInteractionFormatter()
    
    interaction = LLMInteraction(
        agent_name="TestAgent",
        messages=[
            Message(role="system", content="You are helpful."),
            Message(role="user", content="Hello AI")
        ],
        response=Message(
            role="assistant", 
            content="Hello User!", 
            tool_calls=[
                ToolCall(id="tc1", type="function", function=FunctionCall(name="get_info", arguments='{"id": 1, "details": "more"}'))
            ]
        ),
        tools_called=[
            ToolCall(id="tc1", type="function", function=FunctionCall(name="get_info", arguments='{"id": 1, "details": "more"}'))
        ]
    )
    
    record = logging.LogRecord("llm_interaction", logging.DEBUG, "test.py", 10, "LLM Call", (), None, "test_func")
    record.llm_interaction = interaction
    
    formatted_log = formatter.format(record)
    
    assert "Agent: TestAgent" in formatted_log
    assert "[System] You are helpful." in formatted_log
    assert "[User] Hello AI" in formatted_log
    assert "[Assistant] Hello User!" in formatted_log
    assert "Tool: get_info" in formatted_log
    assert '    "id": 1,' in formatted_log # Check pretty printed JSON args
    assert '    "details": "more"' in formatted_log
    assert "Timestamp:" in formatted_log

def test_llm_interaction_formatter_no_tools():
    formatter = LLMInteractionFormatter()
    interaction = LLMInteraction(
        agent_name="SimpleAgent",
        messages=[Message(role="user", content="Hi")],
        response=Message(role="assistant", content="Hi back"),
        tools_called=[]
    )
    record = logging.LogRecord("llm_interaction", logging.DEBUG, "test.py", 10, "LLM Call", (), None, "test_func")
    record.llm_interaction = interaction
    
    formatted_log = formatter.format(record)
    assert "Tools Called:\n  No tools were called." in formatted_log

