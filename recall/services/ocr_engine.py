from __future__ import annotations

import logging
import os
import shutil
import sys
from pathlib import Path

from recall.services.ocr_worker import OCRCallable, _default_ocr_engine

_logger = logging.getLogger(__name__)


def _register_nvidia_dll_dirs() -> None:
    """Add nvidia package DLL directories to PATH so LoadLibrary can find them."""
    if sys.platform != "win32":
        return
    import site

    added: list[str] = []
    for sp in site.getsitepackages():
        nvidia_base = Path(sp) / "nvidia"
        if not nvidia_base.is_dir():
            continue
        for pkg_dir in nvidia_base.iterdir():
            bin_dir = pkg_dir / "bin"
            if bin_dir.is_dir():
                bin_str = str(bin_dir)
                if bin_str not in os.environ.get("PATH", ""):
                    added.append(bin_str)
    if added:
        os.environ["PATH"] = os.pathsep.join(added) + os.pathsep + os.environ.get("PATH", "")
        _logger.debug("added to PATH: %s", added)


def _create_rapidocr_engine() -> OCRCallable:
    _register_nvidia_dll_dirs()
    import onnxruntime as ort
    from rapidocr_onnxruntime import RapidOCR

    providers = ort.get_available_providers()
    use_cuda = "CUDAExecutionProvider" in providers
    _logger.info("RapidOCR providers=%s use_cuda=%s", providers, use_cuda)

    engine = RapidOCR(
        det_use_cuda=use_cuda,
        cls_use_cuda=use_cuda,
        rec_use_cuda=use_cuda,
    )

    def ocr_fn(image_path: Path) -> str | None:
        import numpy as np
        from PIL import Image

        img = np.array(Image.open(image_path))
        result, _ = engine(img)
        if not result:
            return ""
        text_lines = [line[1] for line in result]
        return "\n".join(text_lines)

    return ocr_fn


def create_ocr_engine() -> OCRCallable:
    try:
        return _create_rapidocr_engine()
    except ImportError:
        _logger.info("RapidOCR not available, checking tesseract fallback")

    if shutil.which("tesseract") is not None:
        _logger.info("using tesseract OCR engine")
        return _default_ocr_engine

    raise RuntimeError(
        "No OCR engine available: install rapidocr-onnxruntime or tesseract"
    )
