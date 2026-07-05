import re
from pathlib import Path
import config

class Skill:
    def __init__(self, name: str, description: str, trigger: str, instructions: str, file_path: Path):
        self.name = name
        self.description = description
        self.trigger = trigger
        self.instructions = instructions
        self.file_path = file_path

    def __str__(self):
        return f"Skill(Name: '{self.name}', Trigger: '{self.trigger}')"


class SkillManager:
    def __init__(self):
        self.skills_dir = config.SKILLS_DIR

    def parse_skill_file(self, file_path: Path) -> Skill:
        """Parses a markdown skill file extracting YAML frontmatter and body instructions."""
        content = file_path.read_text(encoding="utf-8")
        
        # Regex to capture YAML frontmatter (between first and second ---)
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        
        if not frontmatter_match:
            # If no frontmatter, treat the entire file as instructions
            return Skill(
                name=file_path.stem.replace("_", " ").title(),
                description="No description provided.",
                trigger="manual",
                instructions=content.strip(),
                file_path=file_path
            )

        yaml_block = frontmatter_match.group(1)
        instructions = frontmatter_match.group(2).strip()

        # Parse simple YAML key-values without PyYAML dependency
        metadata = {}
        for line in yaml_block.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip().lower()
            val = val.strip().strip('"').strip("'")
            metadata[key] = val

        return Skill(
            name=metadata.get("name", file_path.stem.replace("_", " ").title()),
            description=metadata.get("description", "No description provided."),
            trigger=metadata.get("trigger", "manual"),
            instructions=instructions,
            file_path=file_path
        )

    def load_all_skills(self) -> list:
        """Loads and parses all markdown skill files from the vault system folder."""
        config.ensure_directories()
        skills = []
        # Find all .md files in the skills folder (excluding README.md)
        for path in self.skills_dir.glob("*.md"):
            if path.name.lower() == "readme.md":
                continue
            try:
                skill = self.parse_skill_file(path)
                skills.append(skill)
            except Exception as e:
                print(f"Error parsing skill {path.name}: {e}")
        return skills

    def sync_skills_to_db(self, db_manager):
        """Indexes all loaded skills in the local vector database."""
        skills = self.load_all_skills()
        for skill in skills:
            relative_path = str(skill.file_path.relative_to(config.VAULT_PATH))
            skill_id = skill.file_path.stem
            db_manager.index_skill(
                skill_id=skill_id,
                name=skill.name,
                description=skill.description,
                trigger=skill.trigger,
                file_path=relative_path
            )
        print(f"Synced {len(skills)} skill(s) to the vector database.")


if __name__ == "__main__":
    print("Testing Skill Manager...")
    manager = SkillManager()
    
    # Create a dummy skill to test the parser
    dummy_skill_path = config.SKILLS_DIR / "test_organize_inbox.md"
    dummy_content = """---
name: "Sắp xếp Inbox"
description: "Phân loại các ghi chú mới trong Inbox vào đúng vị trí."
trigger: "khi cần dọn dẹp Inbox hoặc phân loại ghi chú"
---

# Instructions
1. Đọc nội dung file.
2. Tìm các thực thể chính.
3. Gợi ý di chuyển tới mục tương ứng.
"""
    try:
        config.ensure_directories()
        dummy_skill_path.write_text(dummy_content, encoding="utf-8")
        
        skills = manager.load_all_skills()
        print(f"Successfully loaded {len(skills)} skills:")
        for s in skills:
            print(f" - {s}")
            print(f"   Desc: {s.description}")
            print(f"   Instr length: {len(s.instructions)} chars")
            
        # Clean up test file
        if dummy_skill_path.exists():
            dummy_skill_path.unlink()
            
    except Exception as e:
        print(f"Error during skill manager testing: {e}")
