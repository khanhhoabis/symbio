import os
import json
import urllib.request
import config
from db import VectorDBManager
from skills import SkillManager

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class HermesCore:
    def __init__(self):
        config.ensure_directories()
        self.db_manager = VectorDBManager()
        self.skill_manager = SkillManager()
        self.client = None
        
        # Initialize Gemini client if configured
        if config.LLM_PROVIDER == "gemini" and config.GEMINI_API_KEY and GEMINI_AVAILABLE:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY)
            
        # Initialize tables in LanceDB if available
        try:
            self.db_manager.initialize_tables()
            self.skill_manager.sync_skills_to_db(self.db_manager)
        except Exception as e:
            print(f"Warning: Could not initialize database tables: {e}")

    def call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API via official google-genai Client SDK."""
        if not GEMINI_AVAILABLE or not self.client:
            raise ImportError("google-genai client is not installed or configured.")
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in environment.")
            
        response = self.client.models.generate_content(
            model=config.LLM_MODEL,
            contents=prompt,
        )
        return response.text

    def call_ollama(self, prompt: str) -> str:
        """Call local Ollama endpoint via raw HTTP requests."""
        url = f"{config.OLLAMA_HOST.rstrip('/')}/api/generate"
        data = json.dumps({
            "model": config.LLM_MODEL,
            "prompt": prompt,
            "stream": False
        }).encode("utf-8")
        
        req = urllib.request.Request(
            url, data=data,
            headers={'Content-Type': 'application/json'},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            return res_body["response"]

    def run(self, user_request: str) -> str:
        """Main execution loop of the Hermes Agent."""
        print(f"\n[Hermes] Nhận yêu cầu: '{user_request}'")
        
        # 1. Query Vector DB for relevant context notes
        context_notes = []
        try:
            context_notes = self.db_manager.query_notes(user_request, limit=3)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  (Không thể truy vấn ghi chú: {e})")

        # 2. Query Vector DB for matching skills
        matching_skills = []
        try:
            matching_skills = self.db_manager.find_matching_skill(user_request)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  (Không thể tìm kiếm kỹ năng: {e})")

        # 3. Build structured prompt (Nous Research Style)
        prompt_parts = []
        
        # System instructions
        system_instruction = (
            "You are Symbio's Hermes Core, a local-first, self-improving AI agent. "
            "You are designed to assist the user with knowledge management and tasks.\n"
            "COGNITIVE RULES:\n"
            "1. You MUST organize your thought process inside a `<thought>` block before outputting your response.\n"
            "2. If relevant notes are provided, synthesize them to give a contextual response.\n"
            "3. If matching skills instructions are provided, follow them step-by-step to fulfill the task."
        )
        prompt_parts.append(f"<system>\n{system_instruction}\n</system>")

        # Context Notes Section
        if context_notes:
            prompt_parts.append("\n<context_notes>")
            for idx, note in enumerate(context_notes):
                prompt_parts.append(
                    f"Note {idx+1} [Path: {note.get('path')}]:\n"
                    f"Tags: {note.get('tags')}\n"
                    f"Content:\n{note.get('content')}\n"
                )
            prompt_parts.append("</context_notes>")

        # Skills Instructions Section
        if matching_skills:
            # Load the actual instruction content from disk for matched skill
            matched = matching_skills[0]  # Take the top match
            skill_id = matched.get("id")
            skill_file_path = config.VAULT_PATH / matched.get("file_path")
            
            try:
                parsed_skill = self.skill_manager.parse_skill_file(skill_file_path)
                prompt_parts.append(
                    f"\n<matched_skill name=\"{parsed_skill.name}\">\n"
                    f"Description: {parsed_skill.description}\n"
                    f"Instructions to execute:\n{parsed_skill.instructions}\n"
                    f"</matched_skill>"
                )
                print(f"  (Kích hoạt Kỹ năng: '{parsed_skill.name}')")
            except Exception as e:
                print(f"  (Lỗi khi nạp nội dung kỹ năng {skill_id}: {e})")

        # User query
        prompt_parts.append(f"\n<user_request>\n{user_request}\n</user_request>")
        
        full_prompt = "\n".join(prompt_parts)

        # 4. Invoke LLM provider
        print(f"  (Đang gửi yêu cầu tới LLM Provider: {config.LLM_PROVIDER} - Model: {config.LLM_MODEL})...")
        
        try:
            if config.LLM_PROVIDER == "gemini":
                response_text = self.call_gemini(full_prompt)
            elif config.LLM_PROVIDER == "ollama":
                response_text = self.call_ollama(full_prompt)
            else:
                response_text = "Lỗi: Provider không hợp lệ."
            
            return response_text
        except Exception as e:
            return f"Lỗi thực thi LLM: {e}"


if __name__ == "__main__":
    # Test runner shell
    agent = HermesCore()
    print("\nHermes Core Shell is ready.")
    
    # Simple prompt test
    response = agent.run("Xin chào, bạn là ai? Hãy cho tôi biết mục tiêu dự án Symbio.")
    print("\n--- LLM Response ---")
    print(response)
