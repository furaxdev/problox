"""Historique de conversation par salon Discord — JSON sur disque, même
approche que `problox/state.py` (pas de DB, un fichier par salon)."""

from __future__ import annotations

import json
from pathlib import Path

MEMORY_DIR = Path("hermes_memory")


class ChannelMemory:
    def __init__(self, channel_id: int, max_messages: int, memory_dir: Path = MEMORY_DIR):
        self.channel_id = channel_id
        self.max_messages = max_messages
        self._path = memory_dir / f"{channel_id}.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self.messages: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def add(self, role: str, content: str | None, **extra) -> None:
        entry = {"role": role, "content": content, **extra}
        self.messages.append(entry)
        # on garde les N derniers échanges pour ne pas faire exploser le
        # contexte envoyé à DeepSeek à chaque tour
        if len(self.messages) > self.max_messages * 2:
            self.messages = self.messages[-self.max_messages * 2 :]
        self._save()

    def _save(self) -> None:
        self._path.write_text(json.dumps(self.messages, ensure_ascii=False, indent=2), encoding="utf-8")

    def reset(self) -> None:
        self.messages = []
        self._save()
