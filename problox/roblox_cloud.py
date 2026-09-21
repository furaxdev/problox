"""Client minimal pour l'Open Cloud API de Roblox (seul canal d'automatisation
autorisé par les ToS — pas de cookie `.ROBLOSECURITY`, pas d'automation UI).

Docs: https://create.roblox.com/docs/cloud/reference/Place
"""

from __future__ import annotations

import time
from pathlib import Path

import httpx

BASE_URL = "https://apis.roblox.com"


class RobloxCloudError(RuntimeError):
    pass


class RobloxCloudClient:
    """Deux modes d'authentification:

    - `api_key=...` : clé Open Cloud statique (usage local/CLI, un seul
      compte, portée définie à la création de la clé).
    - `bearer_token=...` : access token OAuth (usage web multi-utilisateurs,
      portée limitée aux ressources choisies par l'utilisateur au moment du
      consentement — voir roblox_oauth.py).
    """

    def __init__(
        self,
        universe_id: str,
        place_id: str,
        api_key: str | None = None,
        bearer_token: str | None = None,
        min_seconds_between_calls: float = 1.0,
    ):
        if not api_key and not bearer_token:
            raise ValueError("api_key ou bearer_token requis")
        self._api_key = api_key
        self._bearer_token = bearer_token
        self.universe_id = universe_id
        self.place_id = place_id
        self._min_interval = min_seconds_between_calls
        self._last_call = 0.0

    def _headers(self, content_type: str = "application/json") -> dict:
        headers = {"Content-Type": content_type}
        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        else:
            headers["x-api-key"] = self._api_key
        return headers

    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.monotonic()

    def publish_place(self, rbxlx_path: Path, version_type: str = "Published") -> int:
        """Publie un fichier .rbxlx sur la place cible. Retourne le numéro de version.

        version_type: "Published" (live) ou "Saved" (brouillon, ne met pas le jeu en ligne).
        """
        self._throttle()
        url = (
            f"{BASE_URL}/universes/v1/{self.universe_id}/places/{self.place_id}/versions"
            f"?versionType={version_type}"
        )
        data = rbxlx_path.read_bytes()
        response = httpx.post(
            url,
            headers=self._headers(content_type="application/xml"),
            content=data,
            timeout=60.0,
        )
        if response.status_code >= 400:
            raise RobloxCloudError(f"Publish failed ({response.status_code}): {response.text}")
        return response.json().get("versionNumber", -1)

    def get_universe(self) -> dict:
        self._throttle()
        url = f"{BASE_URL}/cloud/v2/universes/{self.universe_id}"
        response = httpx.get(url, headers=self._headers(), timeout=30.0)
        if response.status_code >= 400:
            raise RobloxCloudError(f"Get universe failed ({response.status_code}): {response.text}")
        return response.json()


def list_universe_places(bearer_token: str, universe_id: str) -> list[dict]:
    """Liste les places d'un univers (nécessaire car OAuth n'autorise que
    l'univers ; il faut ensuite savoir quelle placeId cibler pour publier)."""
    response = httpx.get(
        f"{BASE_URL}/cloud/v2/universes/{universe_id}/places",
        headers={"Authorization": f"Bearer {bearer_token}"},
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RobloxCloudError(f"List places failed ({response.status_code}): {response.text}")
    return response.json().get("places", [])
