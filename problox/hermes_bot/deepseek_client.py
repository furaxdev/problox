"""Client minimal pour l'API DeepSeek (compatible OpenAI: /chat/completions,
tool calling au même format que l'API OpenAI). Pas de SDK openai en
dépendance pour rester léger — juste httpx, comme roblox_cloud.py."""

from __future__ import annotations

from typing import Any

import httpx


class DeepSeekError(RuntimeError):
    pass


class DeepSeekClient:
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com", model: str = "deepseek-chat"):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self.model = model

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.4,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Retourne le message assistant brut (dict OpenAI-style) : contient
        soit `content` (texte), soit `tool_calls` (liste d'appels d'outils à
        exécuter avant de rappeler chat() avec les résultats)."""
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if response.status_code >= 400:
            raise DeepSeekError(f"DeepSeek API error ({response.status_code}): {response.text}")

        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            raise DeepSeekError(f"Réponse DeepSeek inattendue (pas de choices): {data}")
        return choices[0]["message"]
