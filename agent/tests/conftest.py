import pytest
import sys
from pathlib import Path

# Add parent directory (agent) to sys.path so test runner can find config, db, hermes modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

@pytest.fixture(autouse=True)
def mock_vault_sandbox(tmp_path):
    """Automatically redirects all vault paths to a clean temporary directory for every test."""
    original_vault_path = config.VAULT_PATH
    original_system_dir = config.SYSTEM_DIR
    original_skills_dir = config.SKILLS_DIR
    original_database_dir = config.DATABASE_DIR
    
    # Re-root to sandbox directory
    config.VAULT_PATH = tmp_path / "vault"
    config.SYSTEM_DIR = config.VAULT_PATH / ".system"
    config.SKILLS_DIR = config.SYSTEM_DIR / "skills"
    config.DATABASE_DIR = config.SYSTEM_DIR / "symbio_db"
    
    # Ensure directories exist for the test run
    config.ensure_directories()
    
    yield tmp_path
    
    # Restore original configuration after test finishes
    config.VAULT_PATH = original_vault_path
    config.SYSTEM_DIR = original_system_dir
    config.SKILLS_DIR = original_skills_dir
    config.DATABASE_DIR = original_database_dir
