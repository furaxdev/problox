from pathlib import Path
from unittest.mock import MagicMock, patch

from problox import rojo_project


def test_build_passes_relative_output_filename_not_full_path(tmp_path):
    """Régression: avec un out_dir relatif (cas réel en prod: sessions/<id>/build),
    repasser out_dir/place.rbxlx comme -o alors que cwd=out_dir fait résoudre
    le chemin deux fois et rojo échoue avec 'No such file or directory'."""
    out_dir = tmp_path / "sessions" / "abc123" / "build"
    out_dir.mkdir(parents=True)

    fake_result = MagicMock(returncode=0, stdout="", stderr="")
    with patch("problox.rojo_project.shutil.which", return_value="/usr/bin/rojo"), patch(
        "problox.rojo_project.subprocess.run", return_value=fake_result
    ) as mock_run:
        rojo_project.build(out_dir)

    args, kwargs = mock_run.call_args
    command = args[0]
    o_index = command.index("-o")
    assert command[o_index + 1] == "place.rbxlx"
    assert kwargs["cwd"] == out_dir


def test_build_raises_with_stderr_detail(tmp_path):
    out_dir = tmp_path / "build"
    out_dir.mkdir()

    fake_result = MagicMock(returncode=1, stdout="", stderr="boom")
    with patch("problox.rojo_project.shutil.which", return_value="/usr/bin/rojo"), patch(
        "problox.rojo_project.subprocess.run", return_value=fake_result
    ):
        try:
            rojo_project.build(out_dir)
            assert False, "should have raised"
        except rojo_project.RojoBuildError as exc:
            assert "boom" in str(exc)
