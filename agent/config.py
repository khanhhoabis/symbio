import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directories
AGENT_DIR = Path(__file__).resolve().parent
DEFAULT_VAULT_PATH = AGENT_DIR.parent / "vault"

# Vault Configuration
VAULT_PATH_STR = os.getenv("VAULT_PATH", str(DEFAULT_VAULT_PATH))
VAULT_PATH = Path(VAULT_PATH_STR).resolve()

# System Paths (stored inside the vault to ensure local-first portability)
SYSTEM_DIR = VAULT_PATH / ".system"
SKILLS_DIR = SYSTEM_DIR / "skills"
DATABASE_DIR = SYSTEM_DIR / "symbio_db"

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")

# Provider details
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def ensure_directories():
    """Ensure all required system and vault directories exist."""
    VAULT_PATH.mkdir(parents=True, exist_ok=True)
    SYSTEM_DIR.mkdir(parents=True, exist_ok=True)
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

def get_status():
    """Returns a debug status representation of the loaded configuration."""
    return {
        "vault_path": str(VAULT_PATH),
        "system_dir": str(SYSTEM_DIR),
        "skills_dir": str(SKILLS_DIR),
        "database_dir": str(DATABASE_DIR),
        "llm_provider": LLM_PROVIDER,
        "llm_model": LLM_MODEL,
        "gemini_configured": bool(GEMINI_API_KEY),
        "ollama_host": OLLAMA_HOST,
    }

if __name__ == "__main__":
    ensure_directories()
    print("Symbio Configuration status:")
    for key, value in get_status().items():
        print(f"  {key}: {value}")
