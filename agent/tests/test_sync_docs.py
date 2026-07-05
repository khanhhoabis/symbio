import sys
import pytest
import sync_docs

def test_sync_docs_loop_prevention(monkeypatch):
    """Assert sync_docs exits immediately when last commit message starts with docs(auto):."""
    exited = False
    
    # Mock sys.exit to track execution termination
    def mock_exit(code):
        nonlocal exited
        exited = True
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", mock_exit)
    
    # Mock git command to simulate last commit was an automated doc commit
    monkeypatch.setattr(
        sync_docs, 
        "run_git_command", 
        lambda args: "docs(auto): sync architecture and workspace rules" if "--pretty=%s" in args[2] else ""
    )
    
    with pytest.raises(SystemExit):
        sync_docs.main()
        
    assert exited  # Assert that the script attempted to call sys.exit


def test_sync_docs_no_api_key(monkeypatch):
    """Assert sync_docs exits gracefully if Gemini API key is missing (fallback behavior)."""
    exited = False
    
    def mock_exit(code):
        nonlocal exited
        exited = True
        raise SystemExit(code)

    monkeypatch.setattr(sys, "exit", mock_exit)
    monkeypatch.setattr(os := __import__("os"), "getenv", lambda key, default=None: None if key == "GEMINI_API_KEY" else default)
    
    monkeypatch.setattr(
        sync_docs, 
        "run_git_command", 
        lambda args: "feat(core): modify something" if "--pretty=%s" in args[2] else ""
    )
    
    with pytest.raises(SystemExit):
        sync_docs.main()
        
    assert exited
