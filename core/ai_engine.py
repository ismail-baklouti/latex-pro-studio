"""
Latex Pro Studio - AI Engine
Handles interactions with AI providers like Google Gemini for LaTeX code generation and assistance. 
GitHub: https://github.com/ismail-baklouti/latex-pro-studio
"""

import logging
import threading
import os
from typing import Optional, Callable

# Support both the old and new Google Gemini libraries
GEMINI_AVAILABLE = False
try:
    # Try the NEW library first (google-genai)
    from google import genai
    NEW_GEMINI = True
    GEMINI_AVAILABLE = True
except ImportError:
    try:
        # Fallback to OLD library (google-generativeai)
        import google.generativeai as genai
        NEW_GEMINI = False
        GEMINI_AVAILABLE = True
    except ImportError:
        GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIEngine:
    def __init__(self, api_keys: dict):
        # Store API keys per provider (e.g., 'gemini', 'openai', 'anthropic')
        self.api_keys = api_keys or {}
        # Attachments are file paths added to the AI context
        self.attachments = []

    # --- API Key Management ---
    def set_api_key(self, provider: str, key: str):
        self.api_keys[provider.lower()] = key

    def get_api_key(self, provider: str):
        return self.api_keys.get(provider.lower())

    # --- Attachment Management ---
    def add_attachment(self, path: str) -> bool:
        try:
            if os.path.exists(path):
                if path not in self.attachments:
                    self.attachments.append(path)
                return True
        except Exception:
            pass
        return False

    def remove_attachment(self, path: str) -> bool:
        try:
            if path in self.attachments:
                self.attachments.remove(path)
                return True
        except Exception:
            pass
        return False

    def list_attachments(self):
        return list(self.attachments)

    def get_response(self, provider: str, user_prompt: str, context_code: str = "", callback: Optional[Callable] = None):
        def task():
            key = self.api_keys.get(provider.lower())
            if not key:
                if callback: callback(f"Error: API Key for {provider} not found.")
                return

            try:
                p = provider.lower()
                if p == "gemini":
                    response = self._call_gemini(key, user_prompt, context_code)
                elif p == "openai":
                    response = self._call_openai(key, user_prompt, context_code)
                elif p == "anthropic":
                    response = self._call_anthropic(key, user_prompt, context_code)
                else:
                    response = "Provider not supported yet."
                
                if callback: callback(response)
            except Exception as e:
                if callback: callback(f"AI Error: {str(e)}")

        threading.Thread(target=task, daemon=True).start()

    def _call_gemini(self, key, prompt, context):
        if not GEMINI_AVAILABLE:
            return "Library missing. Run: pip install google-genai"

        # Compose the full prompt with available context and attachments
        full_prompt = f"LaTeX Context:\n{context}\n\nRequest: {prompt}\n"
        # If attachments were added, try to include small textual extracts
        if self.attachments:
            full_prompt += "\n--- Attachments Summary ---\n"
            for p in self.attachments:
                try:
                    if p.lower().endswith('.pdf'):
                        try:
                            import fitz
                            doc = fitz.open(p)
                            text = ''
                            # Extract first 2 pages for context
                            for i in range(min(2, doc.page_count)):
                                page = doc.load_page(i)
                                text += page.get_text()
                            doc.close()
                            snippet = text.strip()[:200]
                            full_prompt += f"[PDF:{os.path.basename(p)}] {snippet}\n"
                        except Exception:
                            full_prompt += f"[PDF:{os.path.basename(p)}] (text extraction failed)\n"
                    elif any(p.lower().endswith(ext) for ext in ('.tex', '.txt', '.py', '.java', '.c', '.cpp', '.md')):
                        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                            txt = f.read(2000)
                            snippet = txt.strip()[:500]
                            full_prompt += f"[FILE:{os.path.basename(p)}] {snippet}\n"
                    else:
                        full_prompt += f"[FILE:{os.path.basename(p)}] (binary or unsupported)\n"
                except Exception:
                    full_prompt += f"[FILE:{os.path.basename(p)}] (could not read)\n"

        if NEW_GEMINI:
            client = genai.Client(api_key=key)
            response = client.models.generate_content(model="gemini-1.5-flash", contents=full_prompt)
            return response.text
        else:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(full_prompt)
            return response.text

    def _call_openai(self, key, prompt, context):
        try:
            import openai
        except Exception:
            return "openai package missing. Run: pip install openai"

        openai.api_key = key
        full_prompt = f"LaTeX Context:\n{context}\n\nRequest: {prompt}"
        # include attachments summaries as above
        if self.attachments:
            full_prompt += "\n\nAttachments:\n"
            for p in self.attachments:
                full_prompt += f"- {os.path.basename(p)}\n"

        try:
            resp = openai.ChatCompletion.create(model='gpt-4o-mini', messages=[{'role':'user','content':full_prompt}], max_tokens=800)
            return resp['choices'][0]['message']['content']
        except Exception as e:
            return f"OpenAI Error: {e}"

    def _call_anthropic(self, key, prompt, context):
        try:
            from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
        except Exception:
            try:
                import anthropic
            except Exception:
                return "anthropic package missing. Run: pip install anthropic"
            return "anthropic package present but import failed"

        client = Anthropic(api_key=key)
        full_prompt = f"{HUMAN_PROMPT}LaTeX Context:\n{context}\n\nRequest: {prompt}{AI_PROMPT}"
        try:
            resp = client.completions.create(model="claude-2.1", prompt=full_prompt, max_tokens_to_sample=800)
            # Response structure may vary; attempt common access patterns
            if isinstance(resp, dict):
                return resp.get('completion') or resp.get('text') or str(resp)
            return str(resp)
        except Exception as e:
            return f"Anthropic Error: {e}"