"""Backend web ProbloxDev (déployé sur Render, appelé par le frontend Vercel).

Multi-utilisateurs : chaque visiteur obtient une session (cookie signé), se
connecte à SON compte Roblox via OAuth (voir roblox_oauth.py), choisit une
expérience qu'il a autorisée, puis pilote l'agent — sans jamais partager de
clé API brute avec ProbloxDev.

⚠️ Le SessionStore ci-dessous est en mémoire (process unique). C'est
suffisant pour une instance Render standard (single instance, pas
d'autoscaling), mais un restart perd les sessions actives (l'utilisateur doit
juste se reconnecter) et un déploiement multi-instance nécessiterait de
déplacer ça vers Redis/une DB. Documenté ici plutôt que caché.
"""

from __future__ import annotations

import logging
import secrets
import shutil
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from itsdangerous import BadSignature, URLSafeTimedSerializer
from pydantic import BaseModel

from problox import orchestrator, roblox_cloud, roblox_oauth
from problox.config import load_config
from problox.state import AgentState

logger = logging.getLogger("problox")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CONFIG = load_config()

# Un cookie `Secure` n'est JAMAIS renvoyé par un client HTTP correct sur une
# connexion http:// en clair — seulement https://. En prod (Vercel<->Render,
# cross-site) il faut Secure+SameSite=None. En dev local (`problox web` sur
# http://127.0.0.1) Secure casserait silencieusement toute la session : rien
# n'indique l'erreur, le cookie est juste ignoré au retour (bug réel trouvé
# en écrivant les tests de ce fichier). ALLOWED_ORIGINS n'est renseigné qu'en
# déploiement réel, d'où son usage comme signal ici.
_COOKIE_SECURE = bool(CONFIG.allowed_origins)
_COOKIE_SAMESITE = "none" if _COOKIE_SECURE else "lax"

SESSIONS_DIR = Path("sessions")
COOKIE_NAME = "problox_session"
COOKIE_MAX_AGE = 60 * 60 * 24 * 30  # 30 jours
SESSION_IDLE_TTL = 60 * 60 * 2  # 2h sans activité -> la session est purgée
RUN_COOLDOWN_SECONDS = 15  # anti-abus: espace mini entre deux runs par session

_serializer = URLSafeTimedSerializer(CONFIG.session_secret or secrets.token_urlsafe(32))

app = FastAPI(title="ProbloxDev API")

if CONFIG.allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(CONFIG.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# --------------------------------------------------------------------------
# Sessions
# --------------------------------------------------------------------------


class _LogBuffer:
    def __init__(self, capacity: int = 2000) -> None:
        self.lines: list[str] = []
        self.capacity = capacity
        self._lock = threading.Lock()

    def append(self, line: str) -> None:
        with self._lock:
            self.lines.append(line)
            if len(self.lines) > self.capacity:
                self.lines = self.lines[-self.capacity :]

    def tail(self, offset: int) -> tuple[list[str], int]:
        with self._lock:
            return self.lines[offset:], len(self.lines)


@dataclass
class SessionData:
    session_id: str
    pending_pkce: roblox_oauth.PKCEChallenge | None = None
    tokens: roblox_oauth.TokenSet | None = None
    roblox_user: dict | None = None
    available_universes: list[dict] = field(default_factory=list)
    selected_universe_id: str | None = None
    selected_place_id: str | None = None
    run_status: str = "idle"  # idle | running | done | error
    run_theme: str | None = None
    run_error: str | None = None
    logs: _LogBuffer = field(default_factory=_LogBuffer)
    last_seen: float = field(default_factory=time.monotonic)
    last_run_at: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @property
    def build_dir(self) -> Path:
        return SESSIONS_DIR / self.session_id / "build"

    @property
    def state_path(self) -> Path:
        return SESSIONS_DIR / self.session_id / "state.json"

    @property
    def connected(self) -> bool:
        return self.tokens is not None

    def start_run(self, theme: str) -> tuple[bool, float]:
        """Retourne (ok, secondes_a_attendre). ok=False sans raison temporelle
        (secondes=0) signifie qu'un run est déjà en cours."""
        with self._lock:
            if self.run_status == "running":
                return False, 0.0
            elapsed = time.monotonic() - self.last_run_at
            if elapsed < RUN_COOLDOWN_SECONDS:
                return False, RUN_COOLDOWN_SECONDS - elapsed
            self.run_status = "running"
            self.run_theme = theme
            self.run_error = None
            self.last_run_at = time.monotonic()
            return True, 0.0

    def finish_run(self, error: str | None = None) -> None:
        with self._lock:
            self.run_status = "error" if error else "done"
            self.run_error = error


_sessions: dict[str, SessionData] = {}
_sessions_lock = threading.Lock()


def _get_or_create_session(session_cookie: str | None, response: Response) -> SessionData:
    session_id: str | None = None
    if session_cookie:
        try:
            session_id = _serializer.loads(session_cookie, max_age=COOKIE_MAX_AGE)
        except BadSignature:
            session_id = None

    with _sessions_lock:
        if session_id and session_id in _sessions:
            existing = _sessions[session_id]
            existing.last_seen = time.monotonic()
            return existing

        session_id = secrets.token_urlsafe(24)
        session = SessionData(session_id=session_id)
        _sessions[session_id] = session

    signed = _serializer.dumps(session_id)
    response.set_cookie(
        COOKIE_NAME,
        signed,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
    )
    return session


def _reap_idle_sessions() -> None:
    """Purge les sessions inactives depuis plus de SESSION_IDLE_TTL — sans ça,
    sessions/ grossit sans limite sur une instance longue durée (chaque run
    laisse un dossier build/ derrière lui). Ne touche jamais un run en cours."""
    while True:
        time.sleep(600)
        now = time.monotonic()
        with _sessions_lock:
            stale = [
                sid
                for sid, s in _sessions.items()
                if s.run_status != "running" and (now - s.last_seen) > SESSION_IDLE_TTL
            ]
            for sid in stale:
                del _sessions[sid]
        for sid in stale:
            shutil.rmtree(SESSIONS_DIR / sid, ignore_errors=True)
        if stale:
            logger.info("Sessions purgées (inactives >%ds): %d", SESSION_IDLE_TTL, len(stale))


threading.Thread(target=_reap_idle_sessions, daemon=True).start()


def _oauth_app() -> roblox_oauth.OAuthApp:
    if not CONFIG.has_oauth_app:
        raise HTTPException(
            503,
            "OAuth Roblox non configuré côté serveur (ROBLOX_OAUTH_CLIENT_ID/"
            "SECRET/REDIRECT_URI manquants). Voir docs/OAUTH_SETUP.md.",
        )
    return roblox_oauth.OAuthApp(
        client_id=CONFIG.roblox_oauth_client_id,
        client_secret=CONFIG.roblox_oauth_client_secret,
        redirect_uri=CONFIG.roblox_oauth_redirect_uri,
    )


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------


@app.get("/api/auth/roblox/login")
def roblox_login(response: Response, problox_session: str | None = Cookie(default=None)) -> RedirectResponse:
    app_ = _oauth_app()
    session = _get_or_create_session(problox_session, response)

    pkce = roblox_oauth.PKCEChallenge.generate()
    session.pending_pkce = pkce
    url = roblox_oauth.build_authorize_url(app_, pkce)

    redirect = RedirectResponse(url)
    for header, value in response.raw_headers:
        redirect.raw_headers.append((header, value))
    return redirect


@app.get("/api/auth/roblox/callback")
def roblox_callback(
    code: str,
    state: str,
    response: Response,
    problox_session: str | None = Cookie(default=None),
) -> RedirectResponse:
    app_ = _oauth_app()
    session = _get_or_create_session(problox_session, response)

    if not session.pending_pkce or session.pending_pkce.state != state:
        raise HTTPException(400, "État OAuth invalide ou expiré — relance la connexion.")

    verifier = session.pending_pkce.verifier
    session.pending_pkce = None

    try:
        tokens = roblox_oauth.exchange_code(app_, code, verifier)
        session.tokens = tokens
        session.roblox_user = roblox_oauth.fetch_userinfo(tokens.access_token)
        session.available_universes = roblox_oauth.fetch_granted_resources(app_, tokens.access_token)

        if session.available_universes:
            first = session.available_universes[0]
            universe_id = str(first.get("id") or first.get("universeId") or "")
            session.selected_universe_id = universe_id or None
            if universe_id:
                places = roblox_cloud.list_universe_places(tokens.access_token, universe_id)
                if places:
                    session.selected_place_id = str(places[0].get("id") or places[0].get("placeId") or "")
    except roblox_oauth.RobloxOAuthError as exc:
        logger.error("OAuth callback failed: %s", exc)
        raise HTTPException(400, f"Connexion Roblox échouée: {exc}") from exc

    target = f"{CONFIG.frontend_url or '/'}?connected=1"
    redirect = RedirectResponse(target)
    for header, value in response.raw_headers:
        redirect.raw_headers.append((header, value))
    return redirect


@app.post("/api/auth/logout")
def logout(response: Response, problox_session: str | None = Cookie(default=None)) -> dict:
    if problox_session:
        try:
            session_id = _serializer.loads(problox_session, max_age=COOKIE_MAX_AGE)
            with _sessions_lock:
                _sessions.pop(session_id, None)
        except BadSignature:
            pass
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@app.get("/api/me")
def me(response: Response, problox_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    session = _get_or_create_session(problox_session, response)
    return {
        "connected": session.connected,
        "user": session.roblox_user,
        "available_universes": session.available_universes,
        "selected_universe_id": session.selected_universe_id,
        "selected_place_id": session.selected_place_id,
    }


class SelectExperienceRequest(BaseModel):
    universe_id: str
    place_id: str


@app.post("/api/experiences/select")
def select_experience(
    req: SelectExperienceRequest,
    response: Response,
    problox_session: str | None = Cookie(default=None),
) -> dict:
    session = _get_or_create_session(problox_session, response)
    if not session.connected:
        raise HTTPException(401, "Connecte d'abord un compte Roblox.")
    session.selected_universe_id = req.universe_id
    session.selected_place_id = req.place_id
    return {"ok": True}


# --------------------------------------------------------------------------
# Agent
# --------------------------------------------------------------------------


class RunRequest(BaseModel):
    theme: str
    autonomous: bool = False
    max_iterations: int = 1


def _run_in_background(session: SessionData, req: RunRequest) -> None:
    session.build_dir.parent.mkdir(parents=True, exist_ok=True)

    client: roblox_cloud.RobloxCloudClient | None = None
    if session.connected and session.selected_universe_id and session.selected_place_id:
        try:
            app_ = _oauth_app()
            session.tokens = roblox_oauth.ensure_fresh(app_, session.tokens)
            client = roblox_cloud.RobloxCloudClient(
                universe_id=session.selected_universe_id,
                place_id=session.selected_place_id,
                bearer_token=session.tokens.access_token,
            )
        except roblox_oauth.RobloxOAuthError as exc:
            session.logs.append(f"[auth] Impossible de rafraîchir le token Roblox: {exc}")

    try:
        orchestrator.run(
            req.theme,
            CONFIG,
            autonomous=req.autonomous,
            max_iterations=req.max_iterations,
            build_dir=session.build_dir,
            state_path=session.state_path,
            roblox_client=client,
            log=session.logs.append,
        )
        session.finish_run()
    except Exception as exc:  # noqa: BLE001 - remonté dans l'UI de la session
        logger.exception("Run failed for session %s", session.session_id)
        session.logs.append(f"[erreur] {exc}")
        session.finish_run(error=str(exc))


@app.post("/api/run")
def start_run(
    req: RunRequest,
    response: Response,
    problox_session: str | None = Cookie(default=None),
) -> dict:
    session = _get_or_create_session(problox_session, response)
    if not req.theme.strip():
        raise HTTPException(400, "Thème vide.")
    ok, wait_seconds = session.start_run(req.theme)
    if not ok:
        if wait_seconds > 0:
            raise HTTPException(
                429,
                f"Merci d'attendre encore {wait_seconds:.0f}s avant de relancer un run (anti-abus).",
                headers={"Retry-After": str(int(wait_seconds) + 1)},
            )
        raise HTTPException(409, "Un run est déjà en cours pour cette session.")
    thread = threading.Thread(target=_run_in_background, args=(session, req), daemon=True)
    thread.start()
    return {"started": True}


@app.get("/api/status")
def status(response: Response, problox_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    session = _get_or_create_session(problox_session, response)
    state = AgentState.load(session.state_path)
    tools = {tool: bool(shutil.which(tool)) for tool in ("rojo", "selene", "stylua", "aftman", "wally")}
    return {
        "run": {"status": session.run_status, "theme": session.run_theme, "error": session.run_error},
        "config": {
            "anthropic_ready": CONFIG.has_anthropic_credentials,
            "oauth_configured": CONFIG.has_oauth_app,
            "roblox_connected": session.connected,
        },
        "tools": tools,
        "agent_state": {
            "iteration": state.iteration,
            "theme": state.theme,
            "last_place_version": state.last_place_version,
        },
        "build_available": (session.build_dir / "place.rbxlx").exists(),
    }


@app.get("/api/logs")
def logs(
    response: Response,
    offset: int = 0,
    problox_session: str | None = Cookie(default=None),
) -> dict[str, Any]:
    session = _get_or_create_session(problox_session, response)
    lines, new_offset = session.logs.tail(offset)
    return {"lines": lines, "offset": new_offset}


@app.get("/api/design")
def design(response: Response, problox_session: str | None = Cookie(default=None)) -> dict[str, Any]:
    session = _get_or_create_session(problox_session, response)
    state = AgentState.load(session.state_path)
    if not state.design_history:
        raise HTTPException(404, "Aucun design généré pour l'instant.")
    return state.design_history[-1]


@app.get("/api/build/place.rbxlx")
def download_build(response: Response, problox_session: str | None = Cookie(default=None)) -> FileResponse:
    session = _get_or_create_session(problox_session, response)
    path = session.build_dir / "place.rbxlx"
    if not path.exists():
        raise HTTPException(404, "Aucun build disponible pour cette session.")
    return FileResponse(path, filename="place.rbxlx", media_type="application/xml")


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/")
def root() -> dict:
    return {
        "service": "ProbloxDev API",
        "docs": "/docs",
        "frontend": CONFIG.frontend_url,
        "health": "/api/health",
    }
