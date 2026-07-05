import os
import time
import numpy as np
from pathlib import Path
import config

# Try importing lancedb and google SDK, fail gracefully if not installed yet
try:
    import lancedb
    LANCE_AVAILABLE = True
except ImportError:
    LANCE_AVAILABLE = False

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import urllib.request
    import json
    OLLAMA_HTTP_AVAILABLE = True
except ImportError:
    OLLAMA_HTTP_AVAILABLE = False


try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False


class VectorDBManager:
    def __init__(self):
        self.db_path = config.DATABASE_DIR
        self.provider = config.LLM_PROVIDER
        self.api_key = config.GEMINI_API_KEY
        self.ollama_host = config.OLLAMA_HOST
        self._db = None
        self.client = None
        
        # Configure Gemini client if key is present
        if self.provider == "gemini" and self.api_key and GEMINI_AVAILABLE:
            self.client = genai.Client(api_key=self.api_key)

    @property
    def embedding_dimension(self) -> int:
        """Returns the vector dimension size based on active LLM provider."""
        if self.provider == "gemini":
            return 3072
        # Default dimension for Ollama nomic-embed-text or fallback
        return 768

    @property
    def db(self):
        if not LANCE_AVAILABLE:
            raise ImportError("lancedb is not installed. Please run: pip install lancedb")
        if self._db is None:
            config.ensure_directories()
            self._db = lancedb.connect(str(self.db_path))
        return self._db

    def get_embedding(self, text: str) -> list:
        """Generates embedding vector for a given text based on current LLM provider."""
        if not text or not text.strip():
            # Return dummy zero vector based on current provider dimension
            return [0.0] * self.embedding_dimension

        if self.provider == "gemini":
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not configured in environment.")
            if not GEMINI_AVAILABLE or not self.client:
                raise ImportError("google-genai client is not initialized or installed.")
            
            try:
                # Standard model for embeddings in Gemini using google-genai SDK
                result = self.client.models.embed_content(
                    model="gemini-embedding-2",
                    contents=text,
                )
                return result.embeddings[0].values
            except Exception as e:
                print(f"Error generating Gemini embedding: {e}")
                # Fallback dummy vector
                return [0.0] * self.embedding_dimension

        elif self.provider == "ollama":
            # Call Ollama local embed API using raw python http to minimize dependencies
            try:
                url = f"{self.ollama_host.rstrip('/')}/api/embeddings"
                # Using 'nomic-embed-text' or matching LLM model for embeddings
                model_name = "nomic-embed-text" if "hermes" in config.LLM_MODEL else config.LLM_MODEL
                data = json.dumps({"model": model_name, "prompt": text}).encode("utf-8")
                
                req = urllib.request.Request(
                    url, data=data, 
                    headers={'Content-Type': 'application/json'}, 
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    return res_body["embedding"]
            except Exception as e:
                print(f"Error generating Ollama embedding (make sure Ollama is running and has 'nomic-embed-text' downloaded): {e}")
                # Fallback dummy vector (nomic is 768 dimensional)
                return [0.0] * 768
                
        else:
            # Default fallback mock vector
            return [0.0] * self.embedding_dimension

    def initialize_tables(self):
        """Initializes tables for notes and skills if they do not exist using PyArrow schemas."""
        if not LANCE_AVAILABLE:
            print("Warning: LanceDB is not installed, skipping table initialization.")
            return
        if not PYARROW_AVAILABLE:
            print("Warning: PyArrow is not installed, skipping table initialization.")
            return

        db = self.db
        dim = self.embedding_dimension
        
        # 1. Notes Table Schema
        if "notes" not in db.list_tables().tables:
            notes_schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("path", pa.string()),
                pa.field("content", pa.string()),
                pa.field("tags", pa.string()),
                pa.field("last_modified", pa.float64()),
                pa.field("vector", pa.list_(pa.float32(), dim))
            ])
            db.create_table("notes", schema=notes_schema)
            print("Created empty table: notes (with PyArrow schema)")
        
        # 2. Skills Table Schema
        if "skills" not in db.list_tables().tables:
            skills_schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("name", pa.string()),
                pa.field("description", pa.string()),
                pa.field("trigger", pa.string()),
                pa.field("file_path", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), dim))
            ])
            db.create_table("skills", schema=skills_schema)
            print("Created empty table: skills (with PyArrow schema)")

    def index_note(self, note_id: str, relative_path: str, content: str, tags: str):
        """Adds or updates a note in the database index."""
        if not LANCE_AVAILABLE:
            return
            
        vector = self.get_embedding(content)
        db = self.db
        table = db.open_table("notes")
        
        # Check if record exists and delete it first (LanceDB supports upsert by delete-then-insert in basic setups)
        try:
            table.delete(f"id = '{note_id}'")
        except Exception:
            pass

        data = [{
            "id": note_id,
            "path": relative_path,
            "content": content,
            "tags": tags,
            "last_modified": time.time(),
            "vector": vector
        }]
        table.add(data)

    def query_notes(self, query_text: str, limit: int = 3) -> list:
        """Searches notes based on semantic similarity of query_text."""
        if not LANCE_AVAILABLE:
            return []
            
        table = self.db.open_table("notes")
        if table.count_rows() == 0:
            return []
            
        vector = self.get_embedding(query_text)
        # Perform vector similarity search
        results = table.search(vector).limit(limit).to_list()
        
        # Remove init dummy if returned
        return [r for r in results if r["id"] != "init_dummy"]

    def index_skill(self, skill_id: str, name: str, description: str, trigger: str, file_path: str):
        """Adds or updates an agent skill in the skills database."""
        if not LANCE_AVAILABLE:
            return
            
        # Embed the trigger and description which are what we match semantic intent on
        embed_context = f"Skill: {name}. Description: {description}. Trigger: {trigger}"
        vector = self.get_embedding(embed_context)
        db = self.db
        table = db.open_table("skills")
        
        try:
            table.delete(f"id = '{skill_id}'")
        except Exception:
            pass

        data = [{
            "id": skill_id,
            "name": name,
            "description": description,
            "trigger": trigger,
            "file_path": file_path,
            "vector": vector
        }]
        table.add(data)

    def find_matching_skill(self, user_intent: str) -> list:
        """Finds the most relevant skills for a given user request using semantic similarity."""
        if not LANCE_AVAILABLE:
            return []
            
        table = self.db.open_table("skills")
        if table.count_rows() == 0:
            return []
            
        vector = self.get_embedding(user_intent)
        results = table.search(vector).limit(2).to_list()
        
        return [r for r in results if r["id"] != "init_dummy"]


if __name__ == "__main__":
    # Quick connectivity test
    print("Testing VectorDB Connection...")
    try:
        manager = VectorDBManager()
        if LANCE_AVAILABLE:
            manager.initialize_tables()
            print("LanceDB initialized successfully!")
            print("Generating test embedding...")
            vec = manager.get_embedding("Symbio second brain project")
            print(f"Embedding generated! Dimension size: {len(vec)}")
        else:
            print("LanceDB package not installed locally, running mock simulation mode.")
    except Exception as e:
        print(f"Database setup error: {e}")
