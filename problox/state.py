"""Mémoire persistante de l'agent entre deux runs (fichier JSON local)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

STATE_PATH = Path(".problox_state.json")


@dataclass
class AgentState:
    iteration: int = 0
    theme: str | None = None
    design_history: list[dict] = field(default_factory=list)
    last_place_version: int | None = None

    @classmethod
    def load(cls, path: Path = STATE_PATH) -> "AgentState":
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(**data)

    def save(self, path: Path = STATE_PATH) -> None:
        path.write_text(json.dumps(asdict(self), indent=2, ensure_ascii=False))

    def record_iteration(self, design: dict) -> None:
        self.iteration += 1
        self.design_history.append(design)
