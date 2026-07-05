import pytest
import time
from db import VectorDBManager

def test_db_manager_initialization(monkeypatch):
    """Assert DB tables are initialized empty and queries on empty tables return empty list."""
    manager = VectorDBManager()
    manager.initialize_tables()
    
    # Assert tables created
    assert "notes" in manager.db.list_tables().tables
    assert "skills" in manager.db.list_tables().tables
    
    # Mock embedding function to return a mock vector
    monkeypatch.setattr(manager, "get_embedding", lambda text: [0.0] * manager.embedding_dimension)
    
    # Assert query on empty tables returns empty list without raising LanceDB vector errors
    assert manager.query_notes("hello") == []
    assert manager.find_matching_skill("do task") == []


def test_db_indexing_and_querying(monkeypatch):
    """Assert notes and skills can be indexed and retrieved semantically."""
    manager = VectorDBManager()
    manager.initialize_tables()
    
    dim = manager.embedding_dimension
    
    # Mock embedding to return a specific vector
    # We will make query embedding match the note embedding exactly
    monkeypatch.setattr(manager, "get_embedding", lambda text: [1.0 if "test" in text else 0.0] * dim)
    
    # Index a note
    manager.index_note(
        note_id="note_1",
        relative_path="Inbox/test_note.md",
        content="This is a test content.",
        tags="test,note"
    )
    
    # Query notes
    results = manager.query_notes("test")
    assert len(results) == 1
    assert results[0]["id"] == "note_1"
    assert results[0]["content"] == "This is a test content."
    assert results[0]["path"] == "Inbox/test_note.md"
    assert results[0]["tags"] == "test,note"
    
    # Index a skill
    manager.index_skill(
        skill_id="test_skill",
        name="Test Action",
        description="Used to test",
        trigger="when test matches",
        file_path=".system/skills/test_skill.md"
    )
    
    # Query skill
    skills = manager.find_matching_skill("test")
    assert len(skills) == 1
    assert skills[0]["id"] == "test_skill"
    assert skills[0]["name"] == "Test Action"
    assert skills[0]["file_path"] == ".system/skills/test_skill.md"
