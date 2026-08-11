"""Typed field extraction from OCR'd medical record text.

Turnaround: raw OCR text -> header fields (patient/date/doctor/facility),
report type, and a curated panel of lab values. Only known lab tests are
captured, so generic "key: value" noise never reaches extracted_fields.
"""

from __future__ import annotations

import re

REPORT_TYPE_OTHER = "other"

LAB_TESTS: dict[str, tuple[str, ...]] = {
    "hemoglobin": ("hemoglobin", "haemoglobin", "hgb", "hb"),
    "hematocrit": ("hematocrit", "hct", "packed cell volume", "pcv"),
    "wbc": ("total leukocyte count", "leukocyte count", "white blood cell", "wbc", "tlc"),
    "rbc": ("red blood cell count", "erythrocyte count", "rbc"),
    "platelet": ("platelet count", "platelet", "platelets", "plt"),
    "mcv": ("mean corpuscular volume", "mcv"),
    "mch": ("mean corpuscular hemoglobin", "mch"),
    "mchc": ("mean corpuscular hemoglobin concentration", "mchc"),
    "neutrophils": ("neutrophils", "neutrophil"),
    "lymphocytes": ("lymphocytes", "lymphocyte"),
    "eosinophils": ("eosinophils", "eosinophil"),
    "monocytes": ("monocytes", "monocyte"),
    "sgpt": ("alanine transaminase", "sgpt", "alt"),
    "sgot": ("aspartate transaminase", "sgot", "ast"),
    "alkaline_phosphatase": ("alkaline phosphatase", "alk phos", "alp"),
    "total_bilirubin": ("total bilirubin", "serum bilirubin"),
    "direct_bilirubin": ("direct bilirubin",),
    "indirect_bilirubin": ("indirect bilirubin",),
    "total_protein": ("total protein", "serum protein"),
    "albumin": ("serum albumin", "albumin"),
    "globulin": ("globulin",),
    "urea": ("blood urea", "urea"),
    "creatinine": ("serum creatinine", "creatinine"),
    "uric_acid": ("uric acid",),
    "sodium": ("sodium", "na"),
    "potassium": ("potassium", "k"),
    "chloride": ("chloride", "cl"),
    "calcium": ("serum calcium", "calcium"),
    "total_cholesterol": ("total cholesterol", "cholesterol"),
    "triglycerides": ("triglycerides", "triglyceride", "tg"),
    "hdl": ("hdl cholesterol", "hdl"),
    "ldl": ("ldl cholesterol", "ldl"),
    "vldl": ("vldl",),
    "tsh": ("thyroid stimulating hormone", "tsh"),
    "ft3": ("triiodothyronine", "free t3", "ft3"),
    "ft4": ("thyroxine", "free t4", "ft4"),
    "hba1c": ("glycated hemoglobin", "glycosylated hemoglobin", "hba1c"),
    "fasting_glucose": ("fasting blood sugar", "fasting glucose", "fbs"),
    "postprandial_glucose": ("post prandial blood sugar", "postprandial blood sugar", "ppbs"),
    "random_glucose": ("random blood sugar", "rbs"),
}

_LABEL_TERMS = sorted(
    (term for syns in LAB_TESTS.values() for term in syns), key=len, reverse=True
)
_LABEL_RE = re.compile(r"(?<![a-z0-9])(?:" + "|".join(map(re.escape, _LABEL_TERMS)) + r")")

_NUMBER_RE = re.compile(r"(?<![a-zA-Z0-9µ%.\-^])\d+(?:\.\d+)?")
_DASH_RE = re.compile(r"[-–—]")
_UNIT_RE = re.compile(r"[a-zA-Zμµ/][a-zA-Zμµ%^/0-9.]{0,9}")
_KNOWN_UNITS = {"dl", "g", "mg", "mcg", "ug", "ng", "mmol", "umol", "meq", "ml", "ul", "l", "u", "gm", "pg", "lb", "lakhs", "lakh", "crore"}

_TYPE_RULES = [
    (
        "lab_panel",
        re.compile(
            r"hemoglobin|\bwbc\b|platelet|creatinine|bilirubin|cholesterol|triglycerid|"
            r"\btsh\b|hba1c|lipid profile|liver function|renal function|complete blood"
            r" count|blood sugar|fasting blood|blood cell",
            re.I,
        ),
    ),
    (
        "discharge_summary",
        re.compile(r"discharge summary|discharge instructions|chief complaint|admitt\w+|"
                   r"date of discharge|follow[ -]?up care|discharged on", re.I),
    ),
    (
        "referral_letter",
        re.compile(r"referral|referred|reference letter|reference of", re.I),
    ),
]

_TYPE_RANK = {"lab_panel": 0, "discharge_summary": 1, "referral_letter": 2}

_PATIENT_PATTERNS = [
    re.compile(r"patient\s*(?:name)?\s*[:=\-]\s*([^\n|]{2,60})", re.I),
    re.compile(r"name\s+of\s+(?:the\s+)?patient\s*[:=\-]\s*([^\n|]{2,60})", re.I),
    re.compile(r"(?:mr\.?|mrs\.?|ms\.?|master)\s*[:=\-]\s*([^\n|]{2,60})", re.I),
    re.compile(r"\bname\s*[:=\-]\s*([^\n|]{2,60})", re.I),
]
_EXCLUDED_NAME_LABELS = re.compile(
    r"(?:hospital|doctor|physician|facility|clinic|laboratory|lab|report|test|drug|"
    r"company|institute|centre|center|brand|ward|department)"
)

_DATE_LABEL_RE = re.compile(
    r"date\s+of\s+(?!birth\b)(?:the\s+)?(?:test|report|collection|sample|admission|"
    r"discharge|consultation|issue|visit|procedure)?|(?:test|report|collection|sample)"
    r"\s+date|\bdate\b",
    re.I,
)
_DATE_VALUE_RE = re.compile(
    r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})"
    r"|\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})"
    r"|\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})[,]?\s+(\d{4})"
    r"|\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?[,]?\s+(\d{4})",
    re.I,
)

_NAME_WORD = r"(?:[A-Z]\.|[A-Z][A-Za-z'\-]*)"
_DOCTOR_RE = re.compile(
    r"(?<![a-z])(?:dr\.?|doctor|physician|consultant)[^\S\n]*[:=\-]?[^\S\n]*"
    r"(?:dr\.?[^\S\n]+)?(" + _NAME_WORD + r"(?:[^\S\n]+" + _NAME_WORD + r"){0,2})",
    re.I,
)

_FACILITY_PATTERNS = [
    re.compile(r"(?:referred|reference)\s+to\s*[:=\-]\s*([A-Za-z][^\n|]{2,59})", re.I),
    re.compile(
        r"(?:facility|hospital|clinic|centre|center|institute|laboratory|lab)\s*[:=\-]\s*"
        r"([A-Za-z][^\n|]{2,59})",
        re.I,
    ),
]
_FACILITY_SUFFIX_RE = re.compile(
    r"^[A-Z][A-Za-z0-9 .&'\-]{2,49}\b(?:hospital|clinic|diagnostics|center|centre|institute|"
    r"imaging|labs?|nursing home)\b\.?$",
    re.I,
)

_MONTHS = {
    name: i
    for i, name in enumerate(
        ["january", "february", "march", "april", "may", "june", "july", "august",
         "september", "october", "november", "december"],
        1,
    )
}
for name, num in list(_MONTHS.items()):
    _MONTHS[name[:3]] = num


def _is_value_candidate(line: str, start: int, end: int) -> bool:
    """A number is a lab value only if it isn't bound to a reference range."""
    before = line[:start].rstrip()
    after = line[end:]
    if before and before[-1] in "-–—":
        return False
    m = re.match(r"\s*[-–—]\s*\d", after)
    return m is None


def _plausible_unit(token: str) -> bool:
    if not token:
        return True
    if any(c in token for c in "/%^µ"):
        return True
    return token.lower() in _KNOWN_UNITS


def _extract_lab_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        line = stripped.lower()
        if not line or len(line) > 300:
            continue
        label_matches = list(_LABEL_RE.finditer(line))
        if not label_matches:
            continue
        numbers = [
            (m.start(), m.end(), m.group(0))
            for m in _NUMBER_RE.finditer(line)
            if _is_value_candidate(line, m.start(), m.end())
        ]
        for lm in label_matches:
            canonical = None
            for name, syns in LAB_TESTS.items():
                if lm.group(0) in syns:
                    canonical = name
                    break
            if canonical is None or canonical in values:
                continue
            for start, end, num in numbers:
                if start < lm.start():
                    continue
                rest = line[end:]
                unit = ""
                um = _UNIT_RE.match(rest.lstrip())
                if um and _plausible_unit(um.group(0)):
                    offset = end + len(rest) - len(rest.lstrip())
                    unit = " " + stripped[offset : offset + len(um.group(0))]
                values[canonical] = f"{stripped[start:end]}{unit}"
                break
    return values


def _normalize_date(raw: str) -> str | None:
    raw = raw.strip().rstrip(".,;")
    m = re.match(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$", raw)
    if m:
        y, mo, d = m.groups()
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    m = re.match(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})$", raw)
    if m:
        a, b, y = m.groups()
        if int(b) > 12:
            mo, d = a, b
        else:
            mo, d = b, a
        y = f"20{y}" if len(y) == 2 else y
        return f"{y}-{int(mo):02d}-{int(d):02d}"
    m = re.match(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})[,]?\s+(\d{4})$", raw)
    if m:
        d, month, y = m.groups()
        mo = _MONTHS.get(month.lower())
        if mo:
            return f"{y}-{mo:02d}-{int(d):02d}"
    m = re.match(r"([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?[,]?\s+(\d{4})$", raw)
    if m:
        month, d, y = m.groups()
        mo = _MONTHS.get(month.lower())
        if mo:
            return f"{y}-{mo:02d}-{int(d):02d}"
    return None


def _first_header_match(patterns: list[re.Pattern], text: str) -> str | None:
    for pattern in patterns:
        for m in pattern.finditer(text):
            value = m.group(1).strip()
            if value.startswith((":", "-", "=", "|")) or not value:
                continue
            return value
    return None


def _extract_patient_name(text: str) -> str | None:
    for pattern in _PATIENT_PATTERNS:
        for m in pattern.finditer(text):
            value = m.group(1).strip()
            if value.startswith((":", "-", "=", "|")) or not value:
                continue
            if value[0].isdigit():
                continue
            if pattern is _PATIENT_PATTERNS[-1]:
                context = text[max(0, m.start() - 40) : m.start()].lower()
                if _EXCLUDED_NAME_LABELS.search(context):
                    continue
            return value
    return None


def _extract_report_date(text: str) -> str | None:
    for m in _DATE_VALUE_RE.finditer(text):
        context = text[max(0, m.start() - 25) : m.start()].lower()
        if "birth" in context or "dob" in context:
            continue
        normalized = _normalize_date(m.group(0))
        if normalized is not None:
            return normalized
    return None


def _extract_doctor(text: str) -> str | None:
    m = _DOCTOR_RE.search(text)
    if not m:
        return None
    return m.group(1).strip()


def _extract_facility(text: str) -> str | None:
    value = _first_header_match(_FACILITY_PATTERNS, text)
    if value:
        return value
    for line in text.splitlines()[:6]:
        if _FACILITY_SUFFIX_RE.match(line.strip()):
            return line.strip()
    return None


def _infer_report_type(text: str) -> str:
    scores = {name: len(rule.findall(text)) for name, rule in _TYPE_RULES}
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], _TYPE_RANK[kv[0]]))
    if ranked[0][1] == 0:
        return REPORT_TYPE_OTHER
    return ranked[0][0]


def extract(raw_text: str) -> dict:
    """Extract structured fields from OCR'd record text."""
    return {
        "patient_name": _extract_patient_name(raw_text),
        "report_date": _extract_report_date(raw_text),
        "doctor_name": _extract_doctor(raw_text),
        "facility_name": _extract_facility(raw_text),
        "report_type": _infer_report_type(raw_text),
        "extracted_fields": _extract_lab_values(raw_text),
    }