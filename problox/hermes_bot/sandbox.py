"""Exécution de code Python sandboxée pour l'outil `execute_code`.

⚠️ Limite honnête : ceci est un sandbox "best effort" par subprocess +
rlimits (CPU, mémoire, pas de fork bomb), PAS une isolation kernel comme
Docker/gVisor/Firecracker. Ça suffit à empêcher un script maladroit de
planter la machine, mais PAS un utilisateur malveillant déterminé
(évasion de sandbox, accès réseau non bloqué ici au niveau OS). D'où :
- outil réservé aux admins configurés (voir config.py, `admin_user_ids`)
- recommandation forte dans docs/HERMES_BOT.md de faire tourner tout le
  process du bot lui-même dans un conteneur/VM jetable isolé du reste de
  l'infra si des utilisateurs non-admins doivent un jour y avoir accès.
"""

from __future__ import annotations

import resource
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SandboxResult:
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


def _limit_resources(memory_limit_mb: int) -> None:
    mem_bytes = memory_limit_mb * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_NPROC, (32, 32))
    resource.setrlimit(resource.RLIMIT_FSIZE, (5 * 1024 * 1024, 5 * 1024 * 1024))


def run_python(code: str, timeout_seconds: float = 10.0, memory_limit_mb: int = 256) -> SandboxResult:
    with tempfile.TemporaryDirectory(prefix="hermes-sandbox-") as tmp:
        script_path = Path(tmp) / "snippet.py"
        script_path.write_text(code, encoding="utf-8")

        try:
            proc = subprocess.run(
                [sys.executable, "-I", str(script_path)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                preexec_fn=lambda: _limit_resources(memory_limit_mb),
            )
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(
                stdout=(exc.stdout or ""),
                stderr=(exc.stderr or "") + "\n[sandbox] délai dépassé, processus tué",
                exit_code=-1,
                timed_out=True,
            )

        return SandboxResult(
            stdout=proc.stdout[-8000:],
            stderr=proc.stderr[-4000:],
            exit_code=proc.returncode,
            timed_out=False,
        )
