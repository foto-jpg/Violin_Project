from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest


def test_run_oemer_sets_cuda_visible_devices(tmp_path):
    img = tmp_path / "score.png"
    img.write_bytes(b"\x89PNG")
    out_dir = tmp_path / "out"

    with (
        patch("app.services.oemer_engine.get_freest_gpu", return_value=1),
        patch("app.services.oemer_engine.subprocess.run") as mock_run,
    ):
        xml = out_dir / "score.musicxml"

        def side_effect(cmd, **kwargs):
            xml.parent.mkdir(parents=True, exist_ok=True)
            xml.write_text("<score/>")
            m = MagicMock()
            m.returncode = 0
            return m

        mock_run.side_effect = side_effect

        from app.services.oemer_engine import run_oemer
        result_path, gpu = run_oemer(img, out_dir)

        assert gpu == 1
        assert mock_run.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"] == "1"


def test_run_oemer_cpu_fallback(tmp_path):
    img = tmp_path / "score.png"
    img.write_bytes(b"\x89PNG")
    out_dir = tmp_path / "out"

    with (
        patch("app.services.oemer_engine.get_freest_gpu", return_value=-1),
        patch("app.services.oemer_engine.subprocess.run") as mock_run,
    ):
        xml = out_dir / "score.musicxml"

        def side_effect(cmd, **kwargs):
            xml.parent.mkdir(parents=True, exist_ok=True)
            xml.write_text("<score/>")
            m = MagicMock()
            m.returncode = 0
            return m

        mock_run.side_effect = side_effect

        from app.services.oemer_engine import run_oemer
        _, gpu = run_oemer(img, out_dir)

        assert gpu == -1
        assert mock_run.call_args.kwargs["env"]["CUDA_VISIBLE_DEVICES"] == ""


def test_run_oemer_raises_on_failure(tmp_path):
    img = tmp_path / "score.png"
    img.write_bytes(b"\x89PNG")

    with (
        patch("app.services.oemer_engine.get_freest_gpu", return_value=0),
        patch("app.services.oemer_engine.subprocess.run") as mock_run,
    ):
        m = MagicMock()
        m.returncode = 1
        m.stderr = "oemer crashed"
        mock_run.return_value = m

        from app.services.oemer_engine import run_oemer
        with pytest.raises(RuntimeError, match="oemer failed"):
            run_oemer(img, tmp_path / "out")
