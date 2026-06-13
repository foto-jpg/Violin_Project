import uuid
from pathlib import Path

import magic
from pdf2image import convert_from_bytes
from loguru import logger

ALLOWED_MIME = {
    "image/png",
    "image/jpeg",
    "application/pdf",
}
MAX_BYTES = 50 * 1024 * 1024


def validate_upload(content: bytes, filename: str) -> str:
    if len(content) > MAX_BYTES:
        raise ValueError(f"File exceeds 50 MB limit ({len(content) // 1024 // 1024} MB)")
    mime = magic.from_buffer(content, mime=True)
    if mime not in ALLOWED_MIME:
        raise ValueError(f"Unsupported file type: {mime}")
    return mime


def save_upload(content: bytes, mime: str, uploads_dir: Path) -> tuple[str, Path]:
    job_id = uuid.uuid4().hex[:12]

    if mime == "application/pdf":
        logger.info("PDF detected - converting first page to PNG")
        images = convert_from_bytes(content, first_page=1, last_page=1, dpi=200)
        img = images[0]
        out_path = uploads_dir / f"{job_id}.png"
        img.save(out_path, "PNG")
    else:
        ext = ".png" if mime == "image/png" else ".jpg"
        out_path = uploads_dir / f"{job_id}{ext}"
        out_path.write_bytes(content)

    # Normalise the shared upload so both OMR engines see identical input.
    # Order matters: fix orientation first (trim/upscale assume horizontal
    # staves), then crop whitespace, then upscale low-resolution scans.
    auto_orient(out_path)
    trim_whitespace(out_path)
    upscale_for_omr(out_path)

    return job_id, out_path


def trim_whitespace(image_path: Path, margin: int = 40, threshold: int = 200) -> None:
    """Crop surrounding whitespace so sparse, mostly-blank pages still present
    enough staff signal to the OMR engines.

    oemer's staffline detection fails (``align_staffs`` -> "max() arg is an
    empty sequence") when the staff occupies only a small fraction of the page
    - exactly what happens with single-line scores rendered by music21.
    Trimming to the content bounding box (plus a margin) fixes it. No-op when
    content already fills the page, so dense real scans are untouched. Applied
    to the shared upload so the oemer/Audiveris comparison stays fair.
    """
    try:
        from PIL import Image
        import numpy as np

        with Image.open(image_path) as im:
            rgb = im.convert("RGB")
            gray = np.asarray(im.convert("L"))

        mask = gray < threshold
        if not mask.any():
            return  # blank image - nothing to crop

        ys, xs = np.where(mask)
        h, w = gray.shape
        x0 = max(0, int(xs.min()) - margin)
        y0 = max(0, int(ys.min()) - margin)
        x1 = min(w, int(xs.max()) + margin)
        y1 = min(h, int(ys.max()) + margin)

        # Already tight - leave dense scans untouched.
        if (x1 - x0) >= w * 0.98 and (y1 - y0) >= h * 0.98:
            return

        rgb.crop((x0, y0, x1, y1)).save(image_path)
        logger.info(f"Trimmed whitespace: ({w}x{h}) -> ({x1 - x0}x{y1 - y0})")
    except Exception as exc:
        logger.warning(f"trim_whitespace skipped ({image_path}): {exc}")


def _autocorr_peak(proj, lo: int = 3, hi: int = 80):
    """Return (peak_strength, lag) of a 1-D darkness projection's autocorrelation.

    Staff lines are an evenly-spaced pattern, so a projection taken across the
    line direction has a strong autocorrelation peak at the interline spacing.
    We skip the central lobe (line thickness) to the first valley, then take the
    top side peak. ``peak_strength`` (0..1) measures how periodic the axis is -
    used both to size the interline and to tell horizontal from vertical staves.
    """
    import numpy as np

    proj = proj - proj.mean()
    if np.allclose(proj, 0):
        return 0.0, None
    ac = np.correlate(proj, proj, mode="full")[len(proj) - 1:]
    if ac[0] <= 0:
        return 0.0, None
    ac = ac / ac[0]
    start = 1
    while start < hi and ac[start] < ac[start - 1]:
        start += 1
    lo = max(lo, start)
    seg = ac[lo:hi + 1]
    if len(seg) == 0:
        return 0.0, None
    return float(seg.max()), int(lo + seg.argmax())


def _estimate_interline(gray, lo: int = 3, hi: int = 80):
    """Estimate staff interline (px) - assumes staves are already horizontal."""
    import numpy as np

    score, lag = _autocorr_peak((gray < 128).astype(float).sum(axis=1), lo, hi)
    return float(lag) if (lag and score > 0) else None


def _osd_rotation(rgb, min_conf: float = 2.0, max_side: int = 1200):
    """Use Tesseract OSD to find how many degrees to rotate text upright.

    Returns 0/90/180/270 (clockwise degrees to apply), or None when Tesseract is
    unavailable or not confident. Run only after staves are horizontal - OSD
    needs roughly horizontal text, which sheet titles/markings then provide.
    """
    import os
    import re
    import subprocess
    import tempfile

    from PIL import Image

    img = rgb
    if max(img.size) > max_side:
        s = max_side / max(img.size)
        img = img.resize((round(img.width * s), round(img.height * s)))

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    try:
        img.save(tmp.name)
        out = subprocess.run(
            ["tesseract", tmp.name, "-", "--psm", "0"],
            capture_output=True, text=True, timeout=30,
        ).stdout
    except Exception:
        return None
    finally:
        os.unlink(tmp.name)

    rot = re.search(r"Rotate:\s*(\d+)", out)
    conf = re.search(r"Orientation confidence:\s*([\d.]+)", out)
    if not rot or not conf or float(conf.group(1)) < min_conf:
        return None
    return int(rot.group(1)) % 360


def auto_orient(image_path: Path) -> None:
    """Rotate phone-photo scores upright so the OMR engines can read them.

    Two failure modes are corrected: a sideways photo (staff lines run
    vertically -> Audiveris fails at SCALE) and an upside-down one. Step 1
    compares the autocorrelation periodicity of the row vs column projection; if
    the columns are clearly the more periodic axis the staves are vertical, so
    we rotate 90°. Step 2 uses Tesseract OSD on the now-horizontal image to fix
    a 180° flip. No-op for already-upright scans. Applied to the shared upload
    so both engines see identical input.
    """
    try:
        from PIL import Image
        import numpy as np

        with Image.open(image_path) as im:
            rgb = im.convert("RGB")

        changed = False

        # Step 1 - sideways? (staff lines vertical)
        dark = (np.asarray(rgb.convert("L")) < 128).astype(float)
        row_score, _ = _autocorr_peak(dark.sum(axis=1))   # periodicity if horizontal
        col_score, _ = _autocorr_peak(dark.sum(axis=0))   # periodicity if vertical
        if col_score > 0.3 and col_score > row_score * 1.3:
            rgb = rgb.transpose(Image.ROTATE_270)         # 90° clockwise
            changed = True
            logger.info(
                f"auto_orient: rotated 90° (vertical staves; "
                f"col={col_score:.2f} > row={row_score:.2f})"
            )

        # Step 2 - upside down / residual 90° via OSD
        rot = _osd_rotation(rgb)
        if rot in (90, 180, 270):
            rgb = rgb.rotate(-rot, expand=True)           # PIL rotates CCW
            changed = True
            logger.info(f"auto_orient: applied OSD rotation {rot}°")

        if changed:
            rgb.save(image_path)
    except Exception as exc:
        logger.warning(f"auto_orient skipped ({image_path}): {exc}")


def upscale_for_omr(
    image_path: Path,
    min_interline: int = 13,
    target_interline: int = 20,
    max_factor: float = 4.0,
    max_pixels: int = 30_000_000,
) -> None:
    """Upscale only genuinely low-resolution scores so the staff interline is
    large enough for the OMR engines.

    Audiveris flags a sheet invalid when the interline is too small (~9 px in a
    low-DPI phone photo). But upscaling an already-adequate image hurts: a clean
    single staff at interline ~14 recognises fine, yet enlarging it to ~24
    leaves interpolation artifacts that break staff-line clustering. So we only
    act when interline < ``min_interline``, lifting it to ``target_interline``.
    Applied to the shared upload so both engines see identical input.
    """
    try:
        from PIL import Image
        import numpy as np

        with Image.open(image_path) as im:
            rgb = im.convert("RGB")
            interline = _estimate_interline(np.asarray(im.convert("L")))

        if not interline or interline <= 0 or interline >= min_interline:
            return  # unknown, or already adequate - leave untouched

        factor = min(target_interline / interline, max_factor)
        if factor < 1.05:
            return

        # Guard against producing an enormous image.
        if rgb.width * rgb.height * factor * factor > max_pixels:
            factor = (max_pixels / (rgb.width * rgb.height)) ** 0.5
            if factor < 1.05:
                return

        new_size = (round(rgb.width * factor), round(rgb.height * factor))
        rgb.resize(new_size, Image.LANCZOS).save(image_path)
        logger.info(
            f"Upscaled for OMR: interline≈{interline:.0f}px, x{factor:.2f} "
            f"-> {new_size[0]}x{new_size[1]}"
        )
    except Exception as exc:
        logger.warning(f"upscale_for_omr skipped ({image_path}): {exc}")
