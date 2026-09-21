"""Construit le fichier .rbxlx à partir du projet Rojo généré, via la CLI `rojo`."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class RojoNotFoundError(RuntimeError):
    pass


def build(out_dir: Path) -> Path:
    """Exécute `rojo build default.project.json -o place.rbxlx` dans out_dir."""
    if shutil.which("rojo") is None:
        raise RojoNotFoundError(
            "`rojo` introuvable dans le PATH. Lance scripts/setup_sandbox.sh "
            "pour installer la toolchain (Aftman/Rojo)."
        )

    output_path = out_dir / "place.rbxlx"
    subprocess.run(
        ["rojo", "build", "default.project.json", "-o", str(output_path)],
        cwd=out_dir,
        check=True,
    )
    return output_path


def lint_and_format(out_dir: Path) -> list[str]:
    """Best-effort: selene + stylua si dispo. Ne bloque jamais le build."""
    warnings: list[str] = []
    src_dir = out_dir / "src"

    if shutil.which("stylua"):
        subprocess.run(["stylua", str(src_dir)], check=False)
    else:
        warnings.append("stylua introuvable — code non formaté.")

    if shutil.which("selene"):
        result = subprocess.run(
            ["selene", str(src_dir)], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            warnings.append(f"selene a signalé des problèmes:\n{result.stdout}")
    else:
        warnings.append("selene introuvable — code non linté.")

    return warnings
