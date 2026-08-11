#!/usr/bin/env python3
"""Evaluate field extractor accuracy on the OCR text corpus.

Each sample is {name}.txt with a sibling {name}.expected.json. Runs the
extractor and reports per-sample pass/fail, plus field-level precision/recall.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from app.services import field_extractor  # noqa: E402

HEADER_FIELDS = ("patient_name", "report_date", "doctor_name", "facility_name", "report_type")


def load_corpus(corpus_dir: Path):
    samples = []
    for txt_path in sorted(corpus_dir.glob("*.txt")):
        expected_path = txt_path.with_suffix(".expected.json")
        if not expected_path.exists():
            print(f"WARN: no expected file for {txt_path.name}, skipping")
            continue
        samples.append(
            (
                txt_path.stem,
                txt_path.read_text(),
                json.loads(expected_path.read_text()),
            )
        )
    return samples


def main():
    parser = argparse.ArgumentParser(description="Evaluate field extractor on OCR corpus")
    parser.add_argument("--corpus-dir", default=str(ROOT / "evaluation" / "ocr_test_set"))
    args = parser.parse_args()

    samples = load_corpus(Path(args.corpus_dir))
    if not samples:
        print("ERROR: no samples found")
        sys.exit(1)

    results = []
    for name, text, expected in samples:
        actual = field_extractor.extract(text)
        mismatches = []
        for field in HEADER_FIELDS:
            if actual[field] != expected[field]:
                mismatches.append(f"  {field}: expected {expected[field]!r}, got {actual[field]!r}")
        exp_labs = expected.get("extracted_fields", {})
        act_labs = actual["extracted_fields"]
        for k, v in exp_labs.items():
            if act_labs.get(k) != v:
                mismatches.append(f"  lab[{k}]: expected {v!r}, got {act_labs.get(k)!r}")
        for k in act_labs:
            if k not in exp_labs:
                mismatches.append(f"  extra lab[{k}] = {act_labs[k]!r}")

        if mismatches:
            print(f"FAIL {name}")
            for mm in mismatches:
                print(mm)
        else:
            print(f"ok   {name}")
        results.append((name, expected, actual))

    stats = {"tp": 0, "fp": 0, "fn": 0}
    for name, expected, actual in results:
        exp_labs = set(expected.get("extracted_fields", {}))
        act_labs = set(actual["extracted_fields"])
        stats["tp"] += len(exp_labs & act_labs)
        stats["fp"] += len(act_labs - exp_labs)
        stats["fn"] += len(exp_labs - act_labs)

    p = stats["tp"] / (stats["tp"] + stats["fp"]) if stats["tp"] + stats["fp"] else 0.0
    r = stats["tp"] / (stats["tp"] + stats["fn"]) if stats["tp"] + stats["fn"] else 0.0
    print("\nLab-field precision: {:.2f}  recall: {:.2f}".format(p, r))
    passed = len(results) - sum(
        1 for _, exp, act in results
        if any(exp.get(f) != act.get(f) for f in HEADER_FIELDS)
        or exp.get("extracted_fields", {}) != act["extracted_fields"]
    )
    print(f"{passed}/{len(results)} samples matched expected output")


if __name__ == "__main__":
    main()