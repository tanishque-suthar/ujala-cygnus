import io

import pytest
from PIL import Image, ImageDraw, ImageFont

from app.main import app
from app.services.ocr_service import OCRService

TESSERACT_AVAILABLE = OCRService.check_availability()

SAMPLE_REPORT = """SUNRISE DIAGNOSTICS
Patient Name : Rahul Sharma
Date : 14/02/2026
Test Result
Hemoglobin : 14.2 g/dL
WBC Count : 11.0 x10^3/uL
Platelets : 2.4 lakhs
"""


def _report_png() -> bytes:
    img = Image.new("L", (1400, 520), 255)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=36)
    y = 20
    for line in SAMPLE_REPORT.splitlines():
        draw.text((20, y), line, fill=0, font=font)
        y += 55
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.skipif(not TESSERACT_AVAILABLE, reason="tesseract not installed")
async def test_reports_upload_extracts_fields(client):
    app.state.ocr_service = OCRService()
    resp = await client.post(
        "/reports/upload",
        files={"file": ("report.png", _report_png(), "image/png")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["page_count"] == 1
    assert data["extracted_patient_name"] == "Rahul Sharma"
    assert data["extracted_report_date"] == "2026-02-14"
    assert data["extracted_report_type"] == "lab_panel"
    assert data["ocr_confidence"] is not None
    assert "SUNRISE DIAGNOSTICS" in data["raw_text"]
    fields = data["extracted_fields"]
    assert fields.get("hemoglobin", "").startswith("14.2")
    assert "wbc" in fields