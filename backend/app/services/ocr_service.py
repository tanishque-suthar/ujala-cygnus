import shutil
import subprocess

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image, ImageFilter, ImageOps

PAGE_BREAK = "\n\n--- PAGE BREAK ---\n\n"


class OCRService:
    TESS_CONFIG = "--psm 6"
    MIN_TEXT_LAYER_CHARS = 40
    TARGET_SHORT_SIDE = 1600

    @staticmethod
    def check_availability() -> bool:
        """Verify Tesseract is installed at startup."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False

    @staticmethod
    def preprocess(image: Image.Image) -> Image.Image:
        """Grayscale, upscale short side, autocontrast, and sharpen."""
        gray = ImageOps.grayscale(image)
        short_side = min(gray.size)
        if short_side < OCRService.TARGET_SHORT_SIDE:
            scale = OCRService.TARGET_SHORT_SIDE / short_side
            gray = gray.resize(
                (round(gray.width * scale), round(gray.height * scale)),
                Image.Resampling.LANCZOS,
            )
        gray = ImageOps.autocontrast(gray, cutoff=1)
        return gray.filter(ImageFilter.UnsharpMask(radius=2, percent=150))

    def extract_from_image(self, image: Image.Image) -> tuple[str, float]:
        """OCR a single image, returning (text, mean-word-confidence)."""
        processed = self.preprocess(image)
        text = pytesseract.image_to_string(processed, config=self.TESS_CONFIG)
        return text, self._mean_confidence(processed)

    @staticmethod
    def _pdftotext(pdf_bytes: bytes) -> str | None:
        """Extract text-layer content. Returns None when absent/too short."""
        if not shutil.which("pdftotext"):
            return None
        proc = subprocess.run(
            ["pdftotext", "-", "-"], input=pdf_bytes, capture_output=True, timeout=60
        )
        if proc.returncode != 0:
            return None
        text = proc.stdout.decode("utf-8", errors="replace")
        return text if len(text.strip()) >= OCRService.MIN_TEXT_LAYER_CHARS else None

    def extract_from_pdf(self, pdf_bytes: bytes) -> tuple[str, int, float]:
        """OCR a PDF, returning (text, page_count, confidence).

        Uses the embedded text layer when available (confidence 100.0),
        otherwise rasterizes pages at 300 DPI and OCRs them.
        """
        text_layer = self._pdftotext(pdf_bytes)
        if text_layer is not None:
            pages = [p for p in text_layer.split("\f") if p.strip()]
            return PAGE_BREAK.join(pages), max(len(pages), 1), 100.0

        images = convert_from_bytes(pdf_bytes, dpi=300)
        texts, confs = [], []
        for page in images:
            text, conf = self.extract_from_image(page)
            texts.append(text)
            confs.append(conf)
        return PAGE_BREAK.join(texts), len(images), sum(confs) / len(confs)

    def _mean_confidence(self, image: Image.Image) -> float:
        data = pytesseract.image_to_data(
            image, config=self.TESS_CONFIG, output_type=pytesseract.Output.DICT
        )
        confs = [int(c) for c in data["conf"] if c != "-1"]
        return round(sum(confs) / len(confs), 1) if confs else 0.0