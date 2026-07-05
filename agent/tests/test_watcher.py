import pytest
import os
import time
from pathlib import Path
from watchdog.events import FileCreatedEvent, FileModifiedEvent, FileDeletedEvent, FileMovedEvent

import config
from db import VectorDBManager
from watcher import is_valid_markdown_file, get_relative_path, run_incremental_sync, VaultEventHandler


def test_is_valid_markdown_file():
    """Assert helper matches markdown files correctly and ignores hidden system folders/files."""
    assert is_valid_markdown_file(Path("vault/Inbox/hello.md")) is True
    assert is_valid_markdown_file(Path("vault/Inbox/hello.txt")) is False
    assert is_valid_markdown_file(Path("vault/.system/symbio_db/metadata.md")) is False
    assert is_valid_markdown_file(Path("vault/Inbox/.temp_file.md")) is False


def test_incremental_sync_adds_and_removes(monkeypatch):
    """Assert incremental sync updates new notes and deletes stale notes in database index."""
    db_manager = VectorDBManager()
    db_manager.initialize_tables()
    
    # Mock embedding function
    monkeypatch.setattr(db_manager, "get_embedding", lambda text: [0.0] * db_manager.embedding_dimension)

    # 1. Create a markdown file on disk
    note_path = config.VAULT_PATH / "notes_folder" / "hello.md"
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text("Hello, this is a local second brain note.", encoding="utf-8")
    
    # Run sync
    run_incremental_sync(db_manager, config.VAULT_PATH)
    
    # Verify the note is indexed in LanceDB
    results = db_manager.query_notes("brain")
    assert len(results) == 1
    assert results[0]["id"] == "notes_folder/hello.md"
    assert results[0]["content"] == "Hello, this is a local second brain note."

    # 2. Delete the file from disk, but it is still in the DB
    note_path.unlink()
    
    # Run sync again
    run_incremental_sync(db_manager, config.VAULT_PATH)
    
    # Verify it is deleted from the DB index
    results = db_manager.query_notes("brain")
    assert len(results) == 0


def test_event_handler_upsert_and_delete(monkeypatch):
    """Assert that FileSystemEvents trigger database additions, updates, and deletions."""
    db_manager = VectorDBManager()
    db_manager.initialize_tables()
    
    monkeypatch.setattr(db_manager, "get_embedding", lambda text: [1.0] * db_manager.embedding_dimension)

    event_handler = VaultEventHandler(db_manager, config.VAULT_PATH)

    # 1. Simulate FileCreatedEvent
    note_path = config.VAULT_PATH / "created_file.md"
    note_path.write_text("New file created content.", encoding="utf-8")
    
    event = FileCreatedEvent(str(note_path))
    event_handler.on_created(event)
    
    # Verify indexed
    results = db_manager.query_notes("query")
    assert len(results) == 1
    assert results[0]["id"] == "created_file.md"
    assert results[0]["content"] == "New file created content."

    # 2. Simulate FileModifiedEvent
    note_path.write_text("Modified file content.", encoding="utf-8")
    
    event = FileModifiedEvent(str(note_path))
    event_handler.on_modified(event)
    
    # Verify updated content is queryable
    results = db_manager.query_notes("query")
    assert len(results) == 1
    assert results[0]["content"] == "Modified file content."

    # 3. Simulate FileMovedEvent (Rename)
    new_path = config.VAULT_PATH / "moved_file.md"
    new_path.write_text("Modified file content.", encoding="utf-8")
    
    # Moved event deletes the old path and creates the new path
    event = FileMovedEvent(str(note_path), str(new_path))
    event_handler.on_moved(event)
    
    # Verify old file index is deleted, and new file index is active
    results = db_manager.query_notes("query")
    assert len(results) == 1
    assert results[0]["id"] == "moved_file.md"

    # 4. Simulate FileDeletedEvent
    event = FileDeletedEvent(str(new_path))
    event_handler.on_deleted(event)
    
    # Verify deleted
    results = db_manager.query_notes("query")
    assert len(results) == 0
