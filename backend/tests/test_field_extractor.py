import pytest

from app.services import field_extractor as fe

LAB_REPORT = """SUNRISE DIAGNOSTICS
Serving since 1990
Patient Name : Rahul Sharma
Age : 34 yrs   Sex : M
Ref By : Dr. Mehta
Date of Sample Collection : 14/02/2026

CBC
Test                 Result     Unit      Ref Range
Hemoglobin           14.2       g/dL      13.0 - 17.0
Total WBC Count      11.0       x10^3/uL  4.0 - 11.0
Platelet Count       2.4        lakhs     1.5 - 4.1
RBC Count            4.5        million/uL 4.0 - 5.5

LFT
SGPT (ALT)           45         U/L       0 - 40
"""

DISCHARGE_SUMMARY = """DISCHARGE SUMMARY
Patient : Amit Verma
Date of Discharge : 22/03/2026
Chief complaint: fever with cough for 5 days.
Admitted on 20/03/2026. The patient was started on antibiotics.
Hemoglobin was 10.2 g/dL at admission.
Discharge instructions: follow up in OPD.
"""

REFERRAL_LETTER = """REFERRAL LETTER
Date : 10/01/2026
Referring Doctor : Dr. Kavita Rao
Referred to : City General Hospital
Patient : Sneha Patil
She is being referred to the cardiology OPD for evaluation.
"""


def test_lab_report_header_fields():
    result = fe.extract(LAB_REPORT)
    assert result["patient_name"] == "Rahul Sharma"
    assert result["report_date"] == "2026-02-14"
    assert result["doctor_name"] == "Mehta"
    assert result["facility_name"] == "SUNRISE DIAGNOSTICS"
    assert result["report_type"] == "lab_panel"


def test_lab_report_values_with_original_case_units():
    result = fe.extract(LAB_REPORT)
    assert result["extracted_fields"] == {
        "hemoglobin": "14.2 g/dL",
        "wbc": "11.0 x10^3/uL",
        "platelet": "2.4 lakhs",
        "rbc": "4.5 million/uL",
        "sgpt": "45 U/L",
    }


def test_lab_report_ignores_reference_ranges_and_table_headers():
    result = fe.extract(LAB_REPORT)
    fields = result["extracted_fields"]
    assert "result" not in fields
    assert "ref range" not in fields
    assert all(v not in fields.values() for v in ("13.0 - 17.0", "0 - 40", "4.0 - 5.5"))


def test_discharge_summary():
    result = fe.extract(DISCHARGE_SUMMARY)
    assert result["patient_name"] == "Amit Verma"
    assert result["report_date"] == "2026-03-22"
    assert result["report_type"] == "discharge_summary"
    assert result["extracted_fields"] == {"hemoglobin": "10.2 g/dL"}


def test_referral_letter():
    result = fe.extract(REFERRAL_LETTER)
    assert result["patient_name"] == "Sneha Patil"
    assert result["report_date"] == "2026-01-10"
    assert result["doctor_name"] == "Kavita Rao"
    assert result["facility_name"] == "City General Hospital"
    assert result["report_type"] == "referral_letter"
    assert result["extracted_fields"] == {}


def test_noise_text_produces_no_lab_fields_or_names():
    result = fe.extract("LAB ONE\nWBC\nName : John\nDoctor : X\nGate : open\nWard : 3\nBed : 12\n")
    assert result["extracted_fields"] == {}
    assert result["patient_name"] is None
    assert result["report_date"] is None


def test_unstructured_text_is_other():
    result = fe.extract("NOTES\nSome random notes without any structure.\n")
    assert result["report_type"] == "other"
    assert result["extracted_fields"] == {}


def test_generic_name_label_excludes_doctor_hospital():
    assert fe.extract("Doctor Name : A. Kapoor\n")["patient_name"] is None
    assert fe.extract("Hospital Name : St. Mary's\n")["patient_name"] is None
    assert fe.extract("Patient Name : A. Kapoor\n")["patient_name"] == "A. Kapoor"


@pytest.mark.parametrize(
    ("raw_date", "expected"),
    [
        ("12/04/2026", "2026-04-12"),
        ("31/01/2026", "2026-01-31"),
        ("10/01/2026", "2026-01-10"),
        ("08/13/1999", "1999-08-13"),
        ("2026-02-05", "2026-02-05"),
        ("2026/02/05", "2026-02-05"),
        ("5th March 2026", "2026-03-05"),
        ("22 March 2026", "2026-03-22"),
        ("March 5, 2026", "2026-03-05"),
        ("5 Mar 2026", "2026-03-05"),
    ],
)
def test_date_normalization(raw_date, expected):
    result = fe.extract(f"Date : {raw_date}\n")
    assert result["report_date"] == expected


def test_date_of_birth_not_treated_as_report_date():
    result = fe.extract("Patient Name : Sam\nDate of Birth : 12/04/1990\nDate of Test : 12/04/2026\n")
    assert result["report_date"] == "2026-04-12"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Patient Name : JOHN DOE", "JOHN DOE"),
        ("Patient : Mary Jane", "Mary Jane"),
        ("Name of Patient : R. Nair", "R. Nair"),
        ("Patient: A. Kumar", "A. Kumar"),
        ("Mrs. : Shalini Gupta", "Shalini Gupta"),
    ],
)
def test_patient_name_variants(text, expected):
    assert fe.extract(text)[
        "patient_name"
    ] == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Dr. Sharma", "Sharma"),
        ("Doctor : Dr. N. Patel", "N. Patel"),
        ("Referred by: Dr. Smith Jones", "Smith Jones"),
        ("Consultant : Dr. A. B. Kumar", "A. B. Kumar"),
    ],
)
def test_doctor_name_variants(text, expected):
    assert fe.extract(text)["doctor_name"] == expected


def test_value_not_taken_from_reference_range_only_line():
    result = fe.extract("WBC 4.5 - 11.0 x10^3/uL\nHemoglobin 13.0 - 17.0 g/dL\n")
    assert result["extracted_fields"] == {}


def test_implausible_unit_is_dropped():
    result = fe.extract("WBC 11.0 say\n")
    assert result["extracted_fields"] == {"wbc": "11.0"}