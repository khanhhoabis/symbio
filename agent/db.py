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
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import urllib.request
    import json
    OLLAMA_HTTP_AVAILABLE = True
except ImportError:
    OLLAMA_HTTP_AVAILABLE = False


class VectorDBManager:
    def __init__(self):
        self.db_path = config.DATABASE_DIR
        self.provider = config.LLM_PROVIDER
        self.api_key = config.GEMINI_API_KEY
        self.ollama_host = config.OLLAMA_HOST
        self._db = None
        
        # Configure Gemini if key is present
        if self.provider == "gemini" and self.api_key and GEMINI_AVAILABLE:
            genai.configure(api_key=self.api_key)

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
            # Return dummy zero vector of size 768 (standard for Gemini text-embedding-004)
            return [0.0] * 768

        if self.provider == "gemini":
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY is not configured in environment.")
            if not GEMINI_AVAILABLE:
                raise ImportError("google-generativeai is not installed. Please run: pip install google-generativeai")
            
            try:
                # Standard model for embeddings in Gemini
                result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text,
                    task_type="retrieval_document"
                )
                return result["embedding"]
            except Exception as e:
                print(f"Error generating Gemini embedding: {e}")
                # Fallback dummy vector
                return [0.0] * 768

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
            return [0.0] * 768

    def initialize_tables(self):
        """Initializes tables for notes and skills if they do not exist."""
        if not LANCE_AVAILABLE:
            print("Warning: LanceDB is not installed, skipping table initialization.")
            return

        db = self.db
        
        # 1. Notes Table
        if "notes" not in db.table_names():
            # Create table with a schema template
            dummy_vector = [0.0] * 768
            schema_data = [{
                "id": "init_dummy",
                "path": "Inbox/hello.md",
                "content": "Initial startup note",
                "tags": "welcome,system",
                "last_modified": time.time(),
                "vector": dummy_vector
            }]
            db.create_table("notes", schema_data)
            print("Created table: notes")
        
        # 2. Skills Table
        if "skills" not in db.table_names():
            dummy_vector = [0.0] * 768
            schema_data = [{
                "id": "init_dummy",
                "name": "Dummy Skill",
                "description": "Initial skill placeholder",
                "trigger": "never",
                "file_path": ".system/skills/README.md",
                "vector": dummy_vector
            }]
            db.create_table("skills", schema_data)
            print("Created table: skills")

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
            
        vector = self.get_embedding(query_text)
        table = self.db.open_table("notes")
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
            
        vector = self.get_embedding(user_intent)
        table = self.db.open_table("skills")
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
