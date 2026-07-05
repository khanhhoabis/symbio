import os
import sys
import json
import argparse
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Resolve absolute path to ensure modular imports
AGENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AGENT_DIR))

import config
from db import VectorDBManager
from hermes import HermesAgent


class SymbioHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress request spam logging in standard output
        pass

    def send_json_response(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def end_headers(self):
        # Inject CORS headers for web interface connectivity
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        if path == "/api/files":
            self.handle_list_files()
        elif path == "/api/file":
            file_path_query = query.get("path", [""])[0]
            self.handle_read_file(file_path_query)
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            self.send_json_response(400, {"error": "Invalid JSON"})
            return

        if path == "/api/file":
            self.handle_write_file(body)
        elif path == "/api/chat":
            self.handle_chat(body)
        else:
            self.send_error(404, "Not Found")

    def handle_list_files(self):
        vault_path = config.VAULT_PATH
        md_files = []
        for root, dirs, files in os.walk(vault_path):
            # Ignore hidden folders (.system/)
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            
            for file in files:
                if file.endswith(".md"):
                    full_path = Path(root) / file
                    rel_path = str(full_path.relative_to(vault_path)).replace("\\", "/")
                    md_files.append({
                        "path": rel_path,
                        "name": file
                    })
        self.send_json_response(200, {"files": md_files})

    def handle_read_file(self, rel_path: str):
        if not rel_path:
            self.send_json_response(400, {"error": "Missing path parameter"})
            return

        # Security check: Ensure file is inside vault
        target_path = (config.VAULT_PATH / rel_path).resolve()
        if not str(target_path).startswith(str(config.VAULT_PATH.resolve())):
            self.send_json_response(403, {"error": "Access denied outside vault"})
            return

        if not target_path.exists():
            self.send_json_response(404, {"error": "File not found"})
            return

        try:
            content = target_path.read_text(encoding="utf-8")
            self.send_json_response(200, {"content": content, "path": rel_path})
        except Exception as e:
            self.send_json_response(500, {"error": str(e)})

    def handle_write_file(self, body: dict):
        rel_path = body.get("path")
        content = body.get("content", "")

        if not rel_path:
            self.send_json_response(400, {"error": "Missing path parameter"})
            return

        # Security check: Ensure file remains inside vault boundary
        target_path = (config.VAULT_PATH / rel_path).resolve()
        if not str(target_path).startswith(str(config.VAULT_PATH.resolve())):
            self.send_json_response(403, {"error": "Access denied outside vault"})
            return

        try:
            # Create subdirectories if they do not exist
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")

            # Update index incrementally in database
            db_manager = getattr(self.server, "db_manager", None)
            if db_manager:
                try:
                    db_manager.index_note(
                        note_id=rel_path,
                        relative_path=rel_path,
                        content=content,
                        tags=""
                    )
                except Exception as db_err:
                    print(f"[Server] Vector index update error: {db_err}")

            self.send_json_response(200, {"status": "success"})
        except Exception as e:
            self.send_json_response(500, {"error": str(e)})

    def handle_chat(self, body: dict):
        message = body.get("message")
        if not message:
            self.send_json_response(400, {"error": "Missing message parameter"})
            return

        agent = getattr(self.server, "agent", None)
        db_manager = getattr(self.server, "db_manager", None)

        if not agent:
            self.send_json_response(500, {"error": "AI Agent Hermes not initialized"})
            return

        try:
            # Execute Hermes prompt loop
            raw_response = agent.run(message)

            # Query database to retrieve matching context notes to display in the UI as references
            context_notes = []
            if db_manager:
                try:
                    notes = db_manager.query_notes(message, limit=3)
                    for note in notes:
                        # Strip vector attribute to avoid JSON serialization failures
                        if "vector" in note:
                            del note["vector"]
                        context_notes.append(note)
                except Exception:
                    pass

            # Extract thought block vs clean response block
            thought = ""
            clean_response = raw_response
            if "<thought>" in raw_response and "</thought>" in raw_response:
                start_idx = raw_response.find("<thought>") + len("<thought>")
                end_idx = raw_response.find("</thought>")
                thought = raw_response[start_idx:end_idx].strip()
                clean_response = raw_response[end_idx + len("</thought>"):].strip()

            self.send_json_response(200, {
                "thought": thought,
                "response": clean_response,
                "context_notes": context_notes
            })
        except Exception as e:
            self.send_json_response(500, {"error": str(e)})


def main():
    parser = argparse.ArgumentParser(description="Symbio Local HTTP Server")
    parser.add_argument("--port", type=int, default=5678, help="Port to run the HTTP server on")
    args = parser.parse_args()

    # Ensure config folders are active
    config.ensure_directories()

    # Initialize managers
    db_manager = VectorDBManager()
    db_manager.initialize_tables()
    agent = HermesAgent(db_manager)

    # Start HTTP server
    server_address = ("127.0.0.1", args.port)  # Strictly bind to localhost for security
    httpd = HTTPServer(server_address, SymbioHTTPHandler)
    
    # Store references on the server object for handler access
    httpd.db_manager = db_manager
    httpd.agent = agent

    print(f"Symbio Core Server active at http://127.0.0.1:{args.port}/")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    main()
