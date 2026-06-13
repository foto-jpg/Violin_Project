import os
import subprocess
from pathlib import Path

from loguru import logger

from app.services.gpu_selector import get_freest_gpu


def run_oemer(input_image: Path, output_dir: Path, timeout: int = 600) -> tuple[Path, int]:
    output_dir.mkdir(parents=True, exist_ok=True)

    gpu_id = get_freest_gpu()
    env = os.environ.copy()
    if gpu_id >= 0:
        env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
        logger.info(f"Running oemer on GPU {gpu_id}")
    else:
        env["CUDA_VISIBLE_DEVICES"] = ""
        logger.warning("Running oemer on CPU (slow)")

    cmd = [
        "python", "-m", "app.services._ort_patch",
        str(input_image), "-o", str(output_dir),
    ]
    result = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(f"oemer failed:\n{result.stderr[-2000:]}")

    expected_xml = output_dir / f"{input_image.stem}.musicxml"
    if not expected_xml.exists():
        alt = output_dir / f"{input_image.stem}.xml"
        if alt.exists():
            return alt, gpu_id
        raise FileNotFoundError(f"Expected MusicXML not found: {expected_xml}")

    return expected_xml, gpu_id
