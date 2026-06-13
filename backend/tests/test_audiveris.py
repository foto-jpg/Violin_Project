import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from app.services.audiveris import run_audiveris


@pytest.fixture()
def fake_dirs(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    results = tmp_path / "results"
    results.mkdir()
    img = uploads / "test.png"
    img.write_bytes(b"\x89PNG")
    return img, results, tmp_path


def _mock_run_success(output_dir: Path, stem: str):
    def side_effect(cmd, **kwargs):
        (output_dir / f"{stem}.xml").write_text("<score/>")
        m = MagicMock()
        m.returncode = 0
        m.stdout = ""
        m.stderr = ""
        return m
    return side_effect


def test_run_audiveris_returns_xml_path(fake_dirs):
    img, results, data_root = fake_dirs

    with (
        patch("app.services.audiveris.settings") as mock_settings,
        patch("app.services.audiveris.subprocess.run") as mock_run,
    ):
        mock_settings.data_dir = data_root
        mock_settings.data_volume_name = "omr-demo-data"
        mock_settings.audiveris_image = "violin-checker-audiveris:latest"

        out_dir = results / "job1"
        mock_run.side_effect = _mock_run_success(out_dir, "test")

        result = run_audiveris(img, out_dir, timeout=30)
        assert result.suffix in (".xml", ".mxl", ".musicxml")


def test_run_audiveris_raises_on_nonzero_exit(fake_dirs):
    img, results, data_root = fake_dirs

    with (
        patch("app.services.audiveris.settings") as mock_settings,
        patch("app.services.audiveris.subprocess.run") as mock_run,
    ):
        mock_settings.data_dir = data_root
        mock_settings.data_volume_name = "omr-demo-data"
        mock_settings.audiveris_image = "violin-checker-audiveris:latest"

        m = MagicMock()
        m.returncode = 1
        m.stderr = "Audiveris crashed"
        mock_run.return_value = m

        with pytest.raises(RuntimeError, match="Audiveris failed"):
            run_audiveris(img, results / "job2", timeout=30)


def test_run_audiveris_raises_when_xml_missing(fake_dirs):
    img, results, data_root = fake_dirs

    with (
        patch("app.services.audiveris.settings") as mock_settings,
        patch("app.services.audiveris.subprocess.run") as mock_run,
    ):
        mock_settings.data_dir = data_root
        mock_settings.data_volume_name = "omr-demo-data"
        mock_settings.audiveris_image = "violin-checker-audiveris:latest"

        m = MagicMock()
        m.returncode = 0
        m.stdout = ""
        mock_run.return_value = m

        with pytest.raises(FileNotFoundError):
            run_audiveris(img, results / "job3", timeout=30)
