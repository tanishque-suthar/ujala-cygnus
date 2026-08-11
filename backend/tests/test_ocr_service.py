import pytest
from PIL import Image, ImageDraw, ImageFont

from app.services.ocr_service import OCRService

TESSERACT_AVAILABLE = OCRService.check_availability()


def _text_image(text: str = "MONKEY 123") -> Image.Image:
    img = Image.new("L", (900, 140), 255)
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), text, fill=0, font=ImageFont.load_default(size=44))
    return img


def test_preprocess_greyscales_and_upscales():
    small = Image.new("RGB", (100, 80), (200, 200, 200))
    out = OCRService.preprocess(small)
    assert out.mode == "L"
    assert min(out.size) == OCRService.TARGET_SHORT_SIDE


def test_preprocess_keeps_large_images():
    big = Image.new("RGB", (2000, 1800), (200, 200, 200))
    out = OCRService.preprocess(big)
    assert out.size == big.size


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract not installed")
def test_extract_from_image_returns_text_and_confidence():
    text, confidence = OCRService().extract_from_image(_text_image())
    assert "123" in text
    assert confidence > 0


def test_pdf_text_layer_is_preferred(monkeypatch):
    svc = OCRService()
    monkeypatch.setattr(svc, "_pdftotext", lambda _b: "HELLO WORLD\n\n\fPAGE TWO CONTENT")
    text, pages, confidence = svc.extract_from_pdf(b"fake")
    assert pages == 2
    assert confidence == 100.0
    assert "PAGE BREAK" in text
    assert "HELLO WORLD" in text


def test_pdf_ocr_fallback_when_no_text_layer(monkeypatch):
    svc = OCRService()
    monkeypatch.setattr(svc, "_pdftotext", lambda _b: None)
    monkeypatch.setattr(
        "app.services.ocr_service.convert_from_bytes",
        lambda _b, **kw: [Image.new("L", (300, 300), 255)],
    )
    monkeypatch.setattr(svc, "extract_from_image", lambda _img: ("PAGE ONE TEXT", 60.0))
    text, pages, confidence = svc.extract_from_pdf(b"fake")
    assert pages == 1
    assert confidence == 60.0
    assert "PAGE ONE TEXT" in text


def test_pdftotext_missing_falls_back(monkeypatch):
    svc = OCRService()
    monkeypatch.setattr(svc, "_pdftotext", lambda _b: None)
    monkeypatch.setattr(
        "app.services.ocr_service.convert_from_bytes",
        lambda _b, **kw: [Image.new("L", (300, 300), 255)],
    )
    monkeypatch.setattr(svc, "extract_from_image", lambda _img: ("TXT", 50.0))
    text, pages, _ = svc.extract_from_pdf(b"fake")
    assert pages == 1
    assert text == "TXT"