# Codebase Issues — Full Audit

Audit date: 2026-07-27
Services: Model Server (`stub_model_server/`), Backend (`backend/`), Frontend (`frontend/`)

---

## CRITICAL

### 1. Prediction/confidence not displayed in frontend results

**File:** `frontend/src/pages/XRayScreening.jsx:163-196`

The results section shows `patient_name`, `model_used`, `pathology_scores`, `op_threshs`, and `heatmap_base64` — but never renders `result.prediction` or `result.confidence`. The doctor never sees the primary answer: "Is this pneumonia or not?"

### 2. `patientId` never passed from XRayScreening

**File:** `frontend/src/api/client.js:14`, `frontend/src/pages/XRayScreening.jsx:37`

`screenXray()` accepts an optional `patientId` param but `XRayScreening.jsx` never passes it. All new scans create a new patient entry, causing potential patient record duplication.

### 3. No timeout on frontend fetch calls

**File:** `frontend/src/api/client.js:3-28`

Neither `request()` nor `screenXray()` uses `AbortController`. If the backend hangs, the UI shows a "loading" spinner forever with no recovery.

---

## HIGH

### 4. Synchronous inference blocks async event loop

**File:** `stub_model_server/main.py:68`, `stub_model_server/inference.py:89-132`

`predict()` is synchronous but called directly from an `async` endpoint handler without `run_in_executor`. Under concurrent requests, all are serialized.

### 5. Model weights hardcoded, config class empty

**File:** `stub_model_server/config.py:1-8`, `stub_model_server/inference.py:16`

`Settings` class declares zero fields. `"densenet121-res224-all"` is hardcoded with no env-var mechanism to change it.

### 6. Uncaught model loading failure crashes app at startup

**File:** `stub_model_server/main.py:12-15`

`init_model()` called in `lifespan` with zero error handling. If model download fails or GPU is OOM, the exception propagates uncaught and the entire FastAPI app crashes before `/health` is ever reachable.

### 7. Provided `patient_id` silently discarded when patient not found

**File:** `backend/app/routers/screen.py:76-80`

When a caller provides a `patient_id` that doesn't exist in the DB, the code generates a new random UUID instead of returning 404 or using the provided ID. The document ends up associated with an unexpected patient ID.

### 8. Orphaned files if database transaction fails

**File:** `backend/app/routers/screen.py:71-104`

Image and heatmap files are written to disk before the DB transaction begins. If the transaction fails, orphaned files accumulate on disk with no cleanup.

### 9. Unhandled `KeyError` if model server response is malformed

**File:** `backend/app/routers/screen.py:59-63`

If the model server returns HTTP 200 but with missing keys (`prediction`, `confidence`, `heatmap_base64`), Python raises an unhandled `KeyError` resulting in an opaque 500 instead of a 502.

---

## MEDIUM

### 10. Model server error details discarded

**File:** `backend/app/services/model_client.py:31-33`

When the model server returns a non-200 error, the response body with diagnostic info is discarded and replaced with a generic message. Operators cannot debug issues from backend responses.

### 11. `patient_name` silently ignored for existing patients

**File:** `backend/app/routers/screen.py:76-78`

When `patient_id` matches an existing patient, the provided `patient_name` is silently ignored with no warning or update. Callers may think they're renaming the patient.

### 12. Empty `patient_name` accepted without validation

**File:** `backend/app/routers/screen.py:39`

`patient_name` is required via `Form(...)` but there is no non-empty validation. An empty string creates a patient with no name in the database.

### 13. Grad-CAM skips 224×224 intermediate resize

**File:** `stub_model_server/inference.py:62-63`

CAM is upscaled directly from 7×7 to the original crop size, skipping the 224×224 intermediate. The heatmap may be slightly misaligned with what the model actually saw.

### 14. Redundant RGB→grayscale double conversion

**File:** `stub_model_server/main.py:60`, `stub_model_server/inference.py:33`

`main.py` converts the upload to `RGB`, then `inference.py` immediately converts it back to grayscale `"L"`. Wastes memory, especially for grayscale X-rays.

### 15. "Analyze" button in Header has no onClick handler

**File:** `frontend/src/components/Header.jsx:24`

A dead button — clicking it does nothing.

### 16. Empty `.catch()` silently swallows API errors on three pages

**File:** `frontend/src/pages/Dashboard.jsx:40`, `frontend/src/pages/Records.jsx:42`, `frontend/src/pages/PatientHistory.jsx:39`

`Promise.catch(() => {})` suppresses all errors. Pages show "Loading..." indefinitely when the backend is down.

### 17. No request cancellation on unmount

**File:** `frontend/src/pages/XRayScreening.jsx:32-48`

If the user navigates away during an upload, the async handler runs to completion and calls `setState` on an unmounted component, causing React warnings and potential race conditions.

### 18. No client-side file size validation

**File:** `frontend/src/pages/XRayScreening.jsx:94`

Backend rejects files >10 MB, but frontend sends the file first and waits for the round-trip to learn it's too large.

### 19. No 404 catch-all route

**File:** `frontend/src/App.jsx:13-29`

Navigating to an undefined path renders a completely blank page.

### 20. CORS allows `localhost:5173` contrary to spec

**File:** `backend/app/main.py:35-37`

Spec says allow `localhost:3000` only, but code also allows Vite dev server port `5173`.

---

## LOW

| # | Issue | File | Line(s) |
|---|-------|------|---------|
| 21 | `from matplotlib import colormaps` inside per-request function (minor overhead) | `stub_model_server/inference.py` | 74-75 |
| 22 | Transform objects recreated on every request instead of at module level | `stub_model_server/inference.py` | 39-42 |
| 23 | MIME type check is case-sensitive | `stub_model_server/main.py` | 45 |
| 24 | Fragile `op_threshs` save-then-null pattern is undocumented | `stub_model_server/inference.py` | 17-18 |
| 25 | DICOM advertised in UploadSelector UI but not accepted by file input | `UploadSelector.jsx:38` vs `XRayScreening.jsx:94` | — |
| 26 | Mock/hardcoded data in OCRProcessing, BrainMRI, LabResults pages | multiple files | — |
| 27 | Field name inconsistency: `date` vs `uploaded_at` across PatientHistory/Records | `PatientHistory.jsx:28` vs `Records.jsx:38` | — |
| 28 | No ESLint/Prettier configured in frontend | `frontend/package.json` | — |
