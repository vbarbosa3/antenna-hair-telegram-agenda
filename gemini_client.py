"""Integração opcional com a Gemini API."""
from __future__ import annotations

import os
from pathlib import Path


def _load_local_env() -> None:
    """Carrega GEMINI_API_KEY de um .env local, se existir.

    Isso ajuda no Windows quando a variável foi salva em arquivo, sem exibir
    a chave nos logs. A variável já definida no terminal sempre tem prioridade.
    """
    env_file = Path(__file__).with_name(".env")
    if not env_file.exists() or os.environ.get("GEMINI_API_KEY", "").strip():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "GEMINI_API_KEY":
            os.environ["GEMINI_API_KEY"] = value.strip().strip('"').strip("'")
            return


class GeminiClient:
    def __init__(self) -> None:
        from google import genai

        _load_local_env()
        api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY está vazia.")
        self.client = genai.Client(api_key=api_key)
        # Modelo estável para respostas curtas de atendimento.
        self.model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.system_prompt = Path(__file__).with_name("prompt_gemini.txt").read_text(encoding="utf-8")

    def answer(self, user_text: str) -> str:
        prompt = f"{self.system_prompt}\n\nMensagem da cliente:\n{user_text}"
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError("O Gemini retornou uma resposta vazia.")
        return text.strip()
