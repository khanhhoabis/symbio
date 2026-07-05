import os
import sys
import time
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent directory to path so we can import our core modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from db import VectorDBManager

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("VaultWatcher")


def get_relative_path(absolute_path: Path, base_path: Path) -> str:
    """Calculates the relative path from base_path, formatted with forward slashes."""
    try:
        rel_path = absolute_path.relative_to(base_path)
        return str(rel_path).replace("\\", "/")
    except ValueError:
        return str(absolute_path)


def is_valid_markdown_file(path: Path) -> bool:
    """Checks if the path is a markdown file and is not a hidden file or system file."""
    if path.suffix.lower() != ".md":
        return False
    # Ignore files inside hidden directories (like .system/) or files starting with .
    for part in path.parts:
        if part.startswith("."):
            return False
    return True


class VaultEventHandler(FileSystemEventHandler):
    def __init__(self, db_manager: VectorDBManager, vault_path: Path):
        self.db_manager = db_manager
        self.vault_path = vault_path

    def handle_upsert(self, file_path_str: str):
        file_path = Path(file_path_str)
        if not is_valid_markdown_file(file_path):
            return

        rel_path = get_relative_path(file_path, self.vault_path)
        note_id = rel_path  # We use the relative path as the unique ID
        
        # Give editor time to write the file completely on disk to avoid empty read race conditions
        time.sleep(0.1)
        
        try:
            if not file_path.exists():
                return
            content = file_path.read_text(encoding="utf-8")
            # Extract tags or labels if present (fallback to empty)
            tags = ""
            
            logger.info(f"Indexing updated note: {rel_path}")
            self.db_manager.index_note(
                note_id=note_id,
                relative_path=rel_path,
                content=content,
                tags=tags
            )
        except Exception as e:
            logger.error(f"Failed to index note {rel_path}: {e}")

    def handle_delete(self, file_path_str: str):
        file_path = Path(file_path_str)
        # Check suffix manually since the file doesn't exist on disk anymore
        if file_path.suffix.lower() != ".md":
            return
        
        # Don't trigger if it belongs to system folder
        rel_path = get_relative_path(file_path, self.vault_path)
        if rel_path.startswith(".system") or any(part.startswith(".") for part in file_path.parts):
            return

        note_id = rel_path
        logger.info(f"Deleting indexed note: {rel_path}")
        try:
            table = self.db_manager.db.open_table("notes")
            table.delete(f"id = '{note_id}'")
        except Exception as e:
            logger.error(f"Failed to delete note {rel_path} from database: {e}")

    def on_created(self, event):
        if event.is_directory:
            return
        self.handle_upsert(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        self.handle_upsert(event.src_path)

    def on_deleted(self, event):
        if event.is_directory:
            return
        self.handle_delete(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        logger.info(f"File moved from {event.src_path} to {event.dest_path}")
        self.handle_delete(event.src_path)
        self.handle_upsert(event.dest_path)


def run_incremental_sync(db_manager: VectorDBManager, vault_path: Path):
    """Scans disk and syncs with LanceDB database on startup."""
    logger.info("Starting startup incremental sync...")
    
    # 1. Fetch current database index
    indexed_dict = {}
    try:
        table = db_manager.db.open_table("notes")
        if table.count_rows() > 0:
            rows = table.to_arrow().to_pylist()
            # Map note_id -> last_modified timestamp
            indexed_dict = {row["id"]: row["last_modified"] for row in rows}
    except Exception as e:
        logger.warning(f"Could not read notes database index (might be uninitialized): {e}")

    # 2. Scan all local markdown files on disk
    files_on_disk = {}
    for root, dirs, files in os.walk(vault_path):
        # Exclude hidden directories like .system
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        
        for file in files:
            file_path = Path(root) / file
            if is_valid_markdown_file(file_path):
                rel_path = get_relative_path(file_path, vault_path)
                try:
                    mtime = os.path.getmtime(file_path)
                    files_on_disk[rel_path] = (file_path, mtime)
                except Exception as e:
                    logger.error(f"Could not read metadata for {rel_path}: {e}")

    # 3. Synchronize new & modified files
    synced_count = 0
    for rel_path, (file_path, mtime) in files_on_disk.items():
        # If file is not in database OR modified timestamp on disk is newer
        if rel_path not in indexed_dict or mtime > indexed_dict.get(rel_path, 0):
            try:
                content = file_path.read_text(encoding="utf-8")
                db_manager.index_note(
                    note_id=rel_path,
                    relative_path=rel_path,
                    content=content,
                    tags=""
                )
                synced_count += 1
                logger.info(f"Auto-synced: {rel_path}")
            except Exception as e:
                logger.error(f"Failed to auto-sync {rel_path}: {e}")

    # 4. Clean up deleted files from database
    deleted_count = 0
    for note_id in indexed_dict.keys():
        if note_id not in files_on_disk:
            try:
                table = db_manager.db.open_table("notes")
                table.delete(f"id = '{note_id}'")
                deleted_count += 1
                logger.info(f"Auto-deleted stale index: {note_id}")
            except Exception as e:
                logger.error(f"Failed to delete stale note {note_id} from index: {e}")

    logger.info(f"Incremental sync complete. Added/Updated: {synced_count}, Removed: {deleted_count}")


def start_watcher(db_manager: VectorDBManager, vault_path: Path):
    """Main watcher execution loop."""
    config.ensure_directories()
    
    # Initialize DB tables
    db_manager.initialize_tables()
    
    # Run startup synchronization
    run_incremental_sync(db_manager, vault_path)

    event_handler = VaultEventHandler(db_manager, vault_path)
    observer = Observer()
    observer.schedule(event_handler, path=str(vault_path), recursive=True)
    
    logger.info(f"FileSystem Watcher is actively monitoring: {vault_path}")
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Watcher stopping...")
        observer.stop()
    observer.join()
    logger.info("Watcher stopped successfully.")


if __name__ == "__main__":
    db_manager = VectorDBManager()
    start_watcher(db_manager, config.VAULT_PATH)
