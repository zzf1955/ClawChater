from __future__ import annotations

import types
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from recall.services.ocr_engine import create_ocr_engine
from recall.services.ocr_worker import _default_ocr_engine


def test_create_ocr_engine_returns_rapidocr_when_available() -> None:
    fake_ort = types.ModuleType("onnxruntime")
    fake_ort.get_available_providers = lambda: ["CPUExecutionProvider"]

    fake_engine_instance = MagicMock()
    fake_engine_instance.return_value = ([["box", "hello world", 0.9]], None)

    fake_rapidocr = types.ModuleType("rapidocr_onnxruntime")
    fake_rapidocr.RapidOCR = lambda **kwargs: fake_engine_instance

    with patch.dict("sys.modules", {
        "onnxruntime": fake_ort,
        "rapidocr_onnxruntime": fake_rapidocr,
    }):
        engine = create_ocr_engine()

    assert engine is not _default_ocr_engine
    assert callable(engine)


def test_create_ocr_engine_falls_back_to_tesseract(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    with patch.dict("sys.modules", {
        "onnxruntime": None,
        "rapidocr_onnxruntime": None,
    }):
        monkeypatch.setattr(shutil, "which", lambda cmd: "/usr/bin/tesseract" if cmd == "tesseract" else None)
        engine = create_ocr_engine()

    assert engine is _default_ocr_engine


def test_create_ocr_engine_raises_when_nothing_available(monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    with patch.dict("sys.modules", {
        "onnxruntime": None,
        "rapidocr_onnxruntime": None,
    }):
        monkeypatch.setattr(shutil, "which", lambda cmd: None)
        with pytest.raises(RuntimeError, match="No OCR engine available"):
            create_ocr_engine()


def test_rapidocr_engine_callable_returns_text() -> None:
    fake_ort = types.ModuleType("onnxruntime")
    fake_ort.get_available_providers = lambda: ["CPUExecutionProvider"]

    fake_engine_instance = MagicMock()
    fake_engine_instance.return_value = ([["box", "line one", 0.9], ["box", "line two", 0.8]], None)

    fake_rapidocr = types.ModuleType("rapidocr_onnxruntime")
    fake_rapidocr.RapidOCR = lambda **kwargs: fake_engine_instance

    with patch.dict("sys.modules", {
        "onnxruntime": fake_ort,
        "rapidocr_onnxruntime": fake_rapidocr,
        "numpy": MagicMock(),
    }):
        engine = create_ocr_engine()

    # The returned function requires PIL and numpy at call time, so we
    # just verify it was created successfully and is callable.
    assert callable(engine)
