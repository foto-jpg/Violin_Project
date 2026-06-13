import os
import subprocess
from pathlib import Path

from loguru import logger

from app.config import settings


def run_audiveris(input_image: Path, output_dir: Path, timeout: int = 300) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    audiveris_bin = os.getenv("AUDIVERIS_BIN")
    if audiveris_bin:
        cmd = [
            audiveris_bin,
            "-batch", "-export",
            "-output", str(output_dir.resolve()),
            "--", str(input_image.resolve()),
        ]
        logger.info(f"Audiveris (binary): {' '.join(cmd)}")
    else:
        data_root = settings.data_dir.resolve()
        audiveris_input = Path("/data") / input_image.resolve().relative_to(data_root)
        audiveris_output = Path("/data") / output_dir.resolve().relative_to(data_root)
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{data_root}:/data",
            settings.audiveris_image,
            str(audiveris_input),
            str(audiveris_output),
        ]
        logger.info(f"Audiveris (docker): {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if result.returncode != 0:
        raise RuntimeError(f"Audiveris failed:\n{result.stderr[-2000:]}")

    for pattern in ("*.mxl", "*.musicxml", "*.xml"):
        hits = sorted(output_dir.rglob(pattern))
        hits = [h for h in hits if h.name not in {"book.xml"} and "sheet" not in h.name.lower()]
        if hits:
            return hits[0]

    raise FileNotFoundError(
        f"Audiveris produced no MusicXML in {output_dir}. "
        f"stdout: {result.stdout[-500:]}"
    )
