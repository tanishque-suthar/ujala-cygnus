import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import re
from pathlib import Path

class OCRService:
    @staticmethod
    def check_availability() -> bool:
        """Verify Tesseract is installed at startup."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except pytesseract.TesseractNotFoundError:
            return False

    def extract_from_image(self, image: Image.Image) -> str:
        return pytesseract.image_to_string(image)

    def extract_from_pdf(self, pdf_bytes: bytes) -> tuple[str, int]:
        pages = convert_from_bytes(pdf_bytes)
        texts = [pytesseract.image_to_string(page) for page in pages]
        return "\n\n--- PAGE BREAK ---\n\n".join(texts), len(pages)

    def extract_fields(self, raw_text: str) -> dict:
        """Best-effort regex extraction of structured fields."""
        fields = {}
        # Patient name patterns
        for pattern in [r"(?:PATIENT|Patient|Name)\s*:\s*([^|\n]+)", r"(?:Patient Name)\s*:\s*([^|\n]+)"]:
            m = re.search(pattern, raw_text)
            if m:
                fields["patient_name"] = m.group(1).strip()
                break
        # Date patterns
        for pattern in [r"(?:Date|DATE)\s*:\s*([\d\-/]+\w*[\d\-/]*)", r"(\d{1,2}[-/]\w{3}[-/]\d{4})"]:
            m = re.search(pattern, raw_text)
            if m:
                fields["report_date"] = m.group(1).strip()
                break
        # Doctor/Facility
        for pattern in [r"(?:Dr\.|Doctor|Physician)\s*:?\s*([^|\n]+)"]:
            m = re.search(pattern, raw_text)
            if m:
                fields["doctor_name"] = m.group(1).strip()
                break
        # Key-value pairs (e.g., "Hemoglobin : 14.2 g/dL")
        kv_pattern = r"([A-Za-z][\w\s]{2,30}?)\s*[:\-]\s*([\d.]+\s*[a-zA-Z/%]*)"
        for match in re.finditer(kv_pattern, raw_text):
            key = match.group(1).strip()
            val = match.group(2).strip()
            if key.lower() not in {"patient", "name", "date", "report id", "doctor", "physician"}:
                fields[key] = val
        return fields
