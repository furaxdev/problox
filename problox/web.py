"""Serveur web ProbloxDev : pilote l'agent (thème, run, logs, design, build)
depuis un navigateur plutôt que la CLI. Même orchestrateur en dessous.
"""

from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from problox import orchestrator
from problox.config import load_config
from problox.state import AgentState

logger = logging.getLogger("problox")

STATIC_DIR = Path(__file__).resolve().parent / "webapp"
BUILD_DIR = orchestrator.BUILD_DIR

app = FastAPI(title="ProbloxDev")


class _LogBuffer(logging.Handler):
    """Capture les logs de l'agent en mémoire pour l'UI (polling simple)."""

    def __init__(self, capacity: int = 2000) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.capacity = capacity
        self._lock = threading.Lock()

    def emit(self, record: logging.LogRecord) -> None:
        with self._lock:
            self.lines.append(self.format(record))
            if len(self.lines) > self.capacity:
                self.lines = self.lines[-self.capacity :]

    def tail(self, offset: int) -> tuple[list[str], int]:
        with self._lock:
            return self.lines[offset:], len(self.lines)


_log_buffer = _LogBuffer()
_log_buffer.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.getLogger("problox").addHandler(_log_buffer)
logging.getLogger("problox").setLevel(logging.INFO)


class RunState:
    def __init__(self) -> None:
        self.status: str = "idle"  # idle | running | done | error
        self.theme: str | None = None
        self.error: str | None = None
        self._lock = threading.Lock()

    def start(self, theme: str) -> bool:
        with self._lock:
            if self.status == "running":
                return False
            self.status = "running"
            self.theme = theme
            self.error = None
            return True

    def finish(self, error: str | None = None) -> None:
        with self._lock:
            self.status = "error" if error else "done"
            self.error = error


_run_state = RunState()


class RunRequest(BaseModel):
    theme: str
    autonomous: bool = False
    max_iterations: int = 1


def _run_in_background(req: RunRequest) -> None:
    config = load_config()
    try:
        orchestrator.run(
            req.theme,
            config,
            autonomous=req.autonomous,
            max_iterations=req.max_iterations,
        )
        _run_state.finish()
    except Exception as exc:  # noqa: BLE001 - on veut afficher n'importe quelle erreur dans l'UI
        logger.exception("Le run a échoué")
        _run_state.finish(error=str(exc))


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text())


@app.get("/api/status")
def status() -> dict[str, Any]:
    config = load_config()
    state = AgentState.load()
    tools = {tool: bool(shutil.which(tool)) for tool in ("rojo", "selene", "stylua", "aftman", "wally")}
    return {
        "run": {
            "status": _run_state.status,
            "theme": _run_state.theme,
            "error": _run_state.error,
        },
        "config": {
            "anthropic_ready": config.has_anthropic_credentials,
            "roblox_ready": config.has_roblox_credentials,
            "missing_roblox_vars": config.missing_roblox_vars(),
        },
        "tools": tools,
        "agent_state": {
            "iteration": state.iteration,
            "theme": state.theme,
            "last_place_version": state.last_place_version,
        },
        "build_available": (BUILD_DIR / "place.rbxlx").exists(),
    }


@app.post("/api/run")
def start_run(req: RunRequest) -> dict[str, Any]:
    if not req.theme.strip():
        raise HTTPException(400, "Thème vide.")
    if not _run_state.start(req.theme):
        raise HTTPException(409, "Un run est déjà en cours.")
    thread = threading.Thread(target=_run_in_background, args=(req,), daemon=True)
    thread.start()
    return {"started": True}


@app.get("/api/logs")
def logs(offset: int = 0) -> dict[str, Any]:
    lines, new_offset = _log_buffer.tail(offset)
    return {"lines": lines, "offset": new_offset}


@app.get("/api/design")
def design() -> dict[str, Any]:
    state = AgentState.load()
    if not state.design_history:
        raise HTTPException(404, "Aucun design généré pour l'instant.")
    return state.design_history[-1]


@app.get("/api/build/place.rbxlx")
def download_build() -> FileResponse:
    path = BUILD_DIR / "place.rbxlx"
    if not path.exists():
        raise HTTPException(404, "Aucun build disponible — installe Rojo (scripts/setup_sandbox.sh) puis relance un run.")
    return FileResponse(path, filename="place.rbxlx", media_type="application/xml")


if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
