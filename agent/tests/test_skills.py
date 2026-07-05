import pytest
from pathlib import Path
import config
from skills import SkillManager, Skill
from db import VectorDBManager

def test_parse_valid_skill():
    """Assert a markdown skill with valid YAML frontmatter parses correctly."""
    manager = SkillManager()
    
    # Create test skill file
    skill_content = """---
name: "Clean Desk"
description: "Organizes the local environment files."
trigger: "when desk is messy"
---

# Instructions
1. Archive unused files.
2. Clean caches.
"""
    skill_path = config.SKILLS_DIR / "clean_desk.md"
    skill_path.write_text(skill_content, encoding="utf-8")
    
    skill = manager.parse_skill_file(skill_path)
    assert skill.name == "Clean Desk"
    assert skill.description == "Organizes the local environment files."
    assert skill.trigger == "when desk is messy"
    assert "Archive unused files." in skill.instructions


def test_parse_skill_missing_frontmatter():
    """Assert a markdown file with missing/malformed frontmatter falls back gracefully."""
    manager = SkillManager()
    
    skill_content = """# Plain Instructions
Just copy files from inbox to archive without headers.
"""
    skill_path = config.SKILLS_DIR / "plain_copy.md"
    skill_path.write_text(skill_content, encoding="utf-8")
    
    skill = manager.parse_skill_file(skill_path)
    assert skill.name == "Plain Copy"  # Derived from filename stem
    assert skill.description == "No description provided."
    assert skill.trigger == "manual"
    assert "Just copy files" in skill.instructions


def test_sync_skills_to_db(monkeypatch):
    """Assert that sync_skills_to_db indexes skills inside the Vector DB."""
    # Write a test skill
    skill_content = """---
name: "Format Markdown"
description: "Formats files."
trigger: "on clean request"
---
Instruction list...
"""
    skill_path = config.SKILLS_DIR / "format_md.md"
    skill_path.write_text(skill_content, encoding="utf-8")
    
    db_manager = VectorDBManager()
    db_manager.initialize_tables()
    
    # Mock embedding function for db
    monkeypatch.setattr(db_manager, "get_embedding", lambda text: [0.0] * db_manager.embedding_dimension)
    
    skill_manager = SkillManager()
    skill_manager.sync_skills_to_db(db_manager)
    
    # Verify skill was indexed
    results = db_manager.find_matching_skill("format")
    assert len(results) > 0
    assert results[0]["id"] == "format_md"
    assert results[0]["name"] == "Format Markdown"
