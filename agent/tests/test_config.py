import os
from pathlib import Path
import config

def test_config_paths_resolved():
    """Assert config paths resolve as absolute paths and fall inside the sandboxed Vault."""
    assert config.VAULT_PATH.is_absolute()
    assert config.SYSTEM_DIR.is_absolute()
    assert config.DATABASE_DIR.is_absolute()
    
    assert config.SYSTEM_DIR.parent == config.VAULT_PATH
    assert config.DATABASE_DIR.parent == config.SYSTEM_DIR


def test_ensure_directories_creates_folders():
    """Assert ensure_directories() creates all required folders on disk."""
    # Temporarily remove directories to check creation
    if config.DATABASE_DIR.exists():
        config.DATABASE_DIR.rmdir()
    if config.SKILLS_DIR.exists():
        config.SKILLS_DIR.rmdir()
    if config.SYSTEM_DIR.exists():
        config.SYSTEM_DIR.rmdir()
        
    assert not config.DATABASE_DIR.exists()
    assert not config.SKILLS_DIR.exists()
    assert not config.SYSTEM_DIR.exists()
    
    config.ensure_directories()
    
    assert config.VAULT_PATH.exists()
    assert config.SYSTEM_DIR.exists()
    assert config.SKILLS_DIR.exists()
    assert config.DATABASE_DIR.exists()
