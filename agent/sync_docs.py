import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Try importing the new Google GenAI SDK, fail gracefully if not installed
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def run_git_command(args: list) -> str:
    """Runs a git command and returns its stdout as a string."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e.stderr}")
        return ""


def main():
    # 1. Safety Loop Prevention Check
    last_commit_message = run_git_command(["log", "-1", "--pretty=%s"])
    
    if not last_commit_message:
        print("Could not retrieve last commit message. Exiting.")
        sys.exit(0)

    print(f"[SyncDocs] Last commit message: '{last_commit_message}'")
    
    # If this is an automated docs commit, exit immediately to prevent infinite recursion loop
    if last_commit_message.startswith("docs(auto):"):
        print("[SyncDocs] Automated commit detected. Exiting to prevent loop.")
        sys.exit(0)

    # Load environment variables from absolute path
    agent_dir = Path(__file__).resolve().parent
    dotenv_path = agent_dir / ".env"
    load_dotenv(dotenv_path=dotenv_path)

    api_key = os.getenv("GEMINI_API_KEY")
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    if provider != "gemini" or not api_key or not GEMINI_AVAILABLE:
        print("[SyncDocs] Gemini API is not configured or google-genai is not installed. Skipping auto-sync.")
        sys.exit(0)

    # 2. Retrieve Commit Diff
    # Get the diff of the last commit
    commit_diff = run_git_command(["show", "HEAD"])
    if not commit_diff:
        print("[SyncDocs] Could not retrieve commit diff. Exiting.")
        sys.exit(0)

    # 3. Read existing files
    project_root = agent_dir.parent
    arch_file = project_root / "docs" / "ARCHITECTURE.md"
    agents_file = project_root / ".agents" / "AGENTS.md"

    arch_content = arch_file.read_text(encoding="utf-8") if arch_file.exists() else ""
    agents_content = agents_file.read_text(encoding="utf-8") if agents_file.exists() else ""

    # 4. Formulate AI Prompt
    prompt = f"""You are the Symbio Project Document Sync Agent.
Your job is to analyze the latest git commit diff and update 'docs/ARCHITECTURE.md' and '.agents/AGENTS.md' if any architectural changes, configurations, dependencies, folder structures, or database schemas were introduced.

If NO documentation updates are needed, output `<no_change/>`.

If updates are needed, output the entire updated file content wrapped in the corresponding XML tags:
- For docs/ARCHITECTURE.md, wrap in `<updated_architecture>...</updated_architecture>`.
- For .agents/AGENTS.md, wrap in `<updated_agents>...</updated_agents>`.

Keep all Vietnamese explanations, structural details, and markdown styles. Be accurate and do not hallucinate.

---
CURRENT docs/ARCHITECTURE.md:
```markdown
{arch_content}
```

---
CURRENT .agents/AGENTS.md:
```markdown
{agents_content}
```

---
LATEST COMMIT DIFF:
```diff
{commit_diff}
```
"""

    print("[SyncDocs] Analyzing git diff with Gemini...")
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        response_text = response.text
    except Exception as e:
        print(f"[SyncDocs] Failed to connect to Gemini API: {e}")
        sys.exit(0)

    if "<no_change/>" in response_text or not response_text.strip():
        print("[SyncDocs] No architectural changes detected in documentation. Exiting.")
        sys.exit(0)

    # 5. Parse response and update files
    updated = False
    
    arch_match = os.getenv("ARCH_MATCH") # Dummy read for safety
    
    # Extract updated ARCHITECTURE.md
    if "<updated_architecture>" in response_text:
        start_idx = response_text.find("<updated_architecture>") + len("<updated_architecture>")
        end_idx = response_text.find("</updated_architecture>")
        if end_idx > start_idx:
            new_arch = response_text[start_idx:end_idx].strip()
            # Clean up markdown block wraps if AI added them inside tags
            if new_arch.startswith("```markdown"):
                new_arch = new_arch[len("```markdown"):].strip()
            if new_arch.endswith("```"):
                new_arch = new_arch[:-3].strip()
                
            arch_file.parent.mkdir(parents=True, exist_ok=True)
            arch_file.write_text(new_arch, encoding="utf-8")
            print("[SyncDocs] Updated docs/ARCHITECTURE.md")
            updated = True

    # Extract updated AGENTS.md
    if "<updated_agents>" in response_text:
        start_idx = response_text.find("<updated_agents>") + len("<updated_agents>")
        end_idx = response_text.find("</updated_agents>")
        if end_idx > start_idx:
            new_agents = response_text[start_idx:end_idx].strip()
            if new_agents.startswith("```markdown"):
                new_agents = new_agents[len("```markdown"):].strip()
            if new_agents.endswith("```"):
                new_agents = new_agents[:-3].strip()
                
            agents_file.parent.mkdir(parents=True, exist_ok=True)
            agents_file.write_text(new_agents, encoding="utf-8")
            print("[SyncDocs] Updated .agents/AGENTS.md")
            updated = True

    # 6. Auto-commit updates if any files were changed
    if updated:
        print("[SyncDocs] Committing updated documentation...")
        run_git_command(["add", "docs/ARCHITECTURE.md", ".agents/AGENTS.md"])
        run_git_command(["commit", "-m", "docs(auto): sync architecture and workspace rules"])
        print("[SyncDocs] Documentation sync complete.")
    else:
        print("[SyncDocs] AI returned response but no tagged modifications were extracted.")


if __name__ == "__main__":
    main()
