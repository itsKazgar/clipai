"""
llm.py — Multi-LLM support for CLIP.AI
Supports: Claude, OpenAI, Ollama (Hermes3, Llama, Mistral, etc), Gemini
"""
import os, json

class LLMClient:
    def __init__(self, provider="claude", model=None, api_key=None, base_url=None):
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or "http://localhost:11434"
        self.client = None
        self._setup()

    def _setup(self):
        if self.provider == "claude":
            try:
                import anthropic
                key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
                if key:
                    self.client = anthropic.Anthropic(api_key=key)
                    self.model = self.model or "claude-sonnet-4-20250514"
            except ImportError:
                pass

        elif self.provider == "openai":
            try:
                import openai
                key = self.api_key or os.environ.get("OPENAI_API_KEY")
                if key:
                    self.client = openai.OpenAI(api_key=key)
                    self.model = self.model or "gpt-4o"
            except ImportError:
                pass

        elif self.provider == "gemini":
            try:
                import google.generativeai as genai
                key = self.api_key or os.environ.get("GEMINI_API_KEY")
                if key:
                    genai.configure(api_key=key)
                    self.model = self.model or "gemini-1.5-pro"
                    self.client = genai.GenerativeModel(self.model)
            except ImportError:
                pass

        elif self.provider in ("ollama", "hermes3", "llama", "mistral", "kimi"):
            self.model = self.model or {
                "ollama":   "llama3",
                "hermes3":  "hermes3",
                "llama":    "llama3",
                "mistral":  "mistral",
                "kimi":     "kimi",
            }.get(self.provider, "llama3")
            self.client = "ollama"

    def chat(self, system, user):
        """Send a message and return the response text."""
        if self.provider == "claude" and self.client:
            msg = self.client.messages.create(
                model=self.model, max_tokens=500,
                system=system,
                messages=[{"role":"user","content":user}])
            return msg.content[0].text

        elif self.provider == "openai" and self.client:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"system","content":system},{"role":"user","content":user}])
            return resp.choices[0].message.content

        elif self.provider == "gemini" and self.client:
            resp = self.client.generate_content(f"{system}\n\n{user}")
            return resp.text

        elif self.provider in ("ollama","hermes3","llama","mistral","kimi"):
            import urllib.request
            payload = json.dumps({
                "model": self.model,
                "prompt": f"{system}\n\n{user}",
                "stream": False
            }).encode()
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=payload,
                headers={"Content-Type":"application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return json.loads(r.read()).get("response","")
            except Exception as e:
                return f"Ollama error: {e}"

        return None

    def available(self):
        return self.client is not None

    def describe(self):
        if self.client:
            return f"{self.provider}/{self.model}"
        return f"{self.provider} (not configured)"
