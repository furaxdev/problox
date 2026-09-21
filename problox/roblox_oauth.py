"""OAuth 2.0 (Authorization Code + PKCE) contre le fournisseur Roblox.

C'est ce qui permet à ProbloxDev d'être un outil "global" : au lieu que
chaque utilisateur doive générer et coller une clé Open Cloud API brute
(portée illimitée sur ses expériences), il clique "Connecter Roblox",
choisit sur l'écran de consentement Roblox *quelles* expériences il autorise,
et ProbloxDev reçoit un access_token limité à ces ressources-là.

Un seul "OAuth App" Roblox est nécessaire côté ProbloxDev (CLIENT_ID/SECRET
créés une fois par l'opérateur du service sur le Creator Dashboard) ; chaque
visiteur du site s'authentifie ensuite avec son propre compte.

⚠️ Vérifie les chemins d'endpoints ci-dessous contre
https://create.roblox.com/docs/cloud/reference/oauth2 au moment du setup —
c'est une doc qui peut évoluer côté Roblox.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

AUTHORIZE_URL = "https://apis.roblox.com/oauth/v1/authorize"
TOKEN_URL = "https://apis.roblox.com/oauth/v1/token"
REVOKE_URL = "https://apis.roblox.com/oauth/v1/token/revoke"
USERINFO_URL = "https://apis.roblox.com/oauth/v1/userinfo"
RESOURCES_URL = "https://apis.roblox.com/oauth/v1/token/resources"

# Scopes Open Cloud demandés en plus de l'identité: l'utilisateur choisit sur
# l'écran de consentement Roblox à quelles expériences ils s'appliquent.
DEFAULT_SCOPES = "openid profile universe-places:read universe-places:write"


class RobloxOAuthError(RuntimeError):
    pass


@dataclass
class OAuthApp:
    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: str = DEFAULT_SCOPES


@dataclass
class PKCEChallenge:
    verifier: str
    challenge: str
    state: str

    @classmethod
    def generate(cls) -> "PKCEChallenge":
        verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
        digest = hashlib.sha256(verifier.encode()).digest()
        challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        state = secrets.token_urlsafe(24)
        return cls(verifier=verifier, challenge=challenge, state=state)


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str | None
    expires_at: float  # epoch seconds
    id_token: str | None = None

    @property
    def is_expired(self) -> bool:
        return time.time() >= (self.expires_at - 30)  # marge de 30s

    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "id_token": self.id_token,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TokenSet":
        return cls(**data)


def build_authorize_url(app: OAuthApp, pkce: PKCEChallenge) -> str:
    params = {
        "client_id": app.client_id,
        "redirect_uri": app.redirect_uri,
        "scope": app.scopes,
        "response_type": "code",
        "state": pkce.state,
        "code_challenge": pkce.challenge,
        "code_challenge_method": "S256",
    }
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def exchange_code(app: OAuthApp, code: str, code_verifier: str) -> TokenSet:
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": app.redirect_uri,
            "client_id": app.client_id,
            "client_secret": app.client_secret,
            "code_verifier": code_verifier,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RobloxOAuthError(f"Échange du code OAuth échoué ({response.status_code}): {response.text}")
    data = response.json()
    return TokenSet(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        expires_at=time.time() + data.get("expires_in", 3600),
        id_token=data.get("id_token"),
    )


def refresh_tokens(app: OAuthApp, refresh_token: str) -> TokenSet:
    response = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": app.client_id,
            "client_secret": app.client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RobloxOAuthError(f"Refresh du token OAuth échoué ({response.status_code}): {response.text}")
    data = response.json()
    return TokenSet(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", refresh_token),
        expires_at=time.time() + data.get("expires_in", 3600),
        id_token=data.get("id_token"),
    )


def ensure_fresh(app: OAuthApp, tokens: TokenSet) -> TokenSet:
    if not tokens.is_expired:
        return tokens
    if not tokens.refresh_token:
        raise RobloxOAuthError("Token expiré et aucun refresh_token disponible — reconnexion nécessaire.")
    return refresh_tokens(app, tokens.refresh_token)


def fetch_userinfo(access_token: str) -> dict:
    response = httpx.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RobloxOAuthError(f"userinfo échoué ({response.status_code}): {response.text}")
    return response.json()


def fetch_granted_resources(app: OAuthApp, access_token: str) -> list[dict]:
    """Liste les univers/places/assets que l'utilisateur a autorisés sur l'écran
    de consentement (l'app n'a accès qu'à ça, jamais à tout le compte)."""
    response = httpx.post(
        RESOURCES_URL,
        data={
            "token": access_token,
            "client_id": app.client_id,
            "client_secret": app.client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30.0,
    )
    if response.status_code >= 400:
        raise RobloxOAuthError(f"Liste des ressources échouée ({response.status_code}): {response.text}")
    data = response.json()
    resources = data.get("resource_infos") or data.get("resources") or []
    universes: list[dict] = []
    for entry in resources:
        for universe in entry.get("owner", {}).get("universes", []) or entry.get("universes", []) or []:
            universes.append(universe)
    return universes or resources
