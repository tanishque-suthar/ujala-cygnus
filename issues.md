# Codebase Issues — Full Audit

Audit date: 2026-07-27
Services: Model Server (`stub_model_server/`), Backend (`backend/`), Frontend (`frontend/`)

---
✅ = Fixed  ⬜ = Not yet fixed

---

## CRITICAL

### ✅ 1. Prediction/confidence not displayed in frontend results

**File:** `frontend/src/pages/XRayScreening.jsx:163-196`

Added prediction badge and confidence percentage in a results header bar. Prediction shown as a color-coded badge (red for pneumonia, green for normal). Confidence shown as percentage.

### ✅ 2. `patientId` never passed from XRayScreening

**File:** `frontend/src/pages/XRayScreening.jsx`

Added a dropdown that lists existing patients for linking. Selected patient ID is passed to `screenXray()`. Backend now returns 404 if the provided patient_id doesn't exist instead of silently discarding it.

### ✅ 3. No timeout on frontend fetch calls

**File:** `frontend/src/api/client.js`

Added `fetchWithTimeout()` with `AbortController` — 60s default timeout, 120s for the screen endpoint. Request is also cancellable on unmount.

---

## HIGH

### ✅ 4. Synchronous inference blocks async event loop

**File:** `stub_model_server/main.py:68`

Wrapped `predict()` call in `loop.run_in_executor(None, ...)` so inference runs in a thread pool instead of blocking the event loop.

### ✅ 5. Model weights hardcoded, config class empty

**File:** `stub_model_server/config.py`

Added `model_weights: str = "densenet121-res224-all"` field to `Settings`, importable via `from config import settings`. Overridable via env var `MODEL_WEIGHTS`.

### ✅ 6. Uncaught model loading failure crashes app at startup

**File:** `stub_model_server/main.py:14-15`

Wrapped `init_model()` in `try/except` so the app starts regardless; `/health` endpoint reports model state.

### ✅ 7. Provided `patient_id` silently discarded when patient not found

**File:** `backend/app/routers/screen.py:76-80`

Changed to raise `HTTPException(404)` when `patient_id` is provided but doesn't match any patient. Files are cleaned up on failure.

### ✅ 8. Orphaned files if database transaction fails

**File:** `backend/app/routers/screen.py:71-104`

Added `try/except` around the DB transaction block. On any failure (404 or 500), `image_abs.unlink()` and `heatmap_abs.unlink()` are called before the error propagates.

### ✅ 9. Unhandled `KeyError` if model server response is malformed

**File:** `backend/app/routers/screen.py:59-63`

Changed to use `.get()` with `None` checks for `prediction`, `confidence`, `heatmap_base64`. Returns 502 with descriptive message if any are missing.

---

## MEDIUM

### ✅ 10. Model server error details discarded

**File:** `backend/app/services/model_client.py:31-33`

When the model server returns a non-200, the response body's `error` field is now extracted and appended to the exception message (e.g. `"Model server returned 500: GPU out of memory"`).

### ✅ 11. `patient_name` silently ignored for existing patients

**File:** `backend/app/routers/screen.py:76-78`

Resolved by Fix 7 — when `patient_id` is provided and the patient exists, the name from the DB is used (matching the caller's expectation of "using existing patient"). No silent ignore occurs.

### ✅ 12. Empty `patient_name` accepted without validation

**File:** `backend/app/routers/screen.py`

Added `if not patient_name.strip(): return JSONResponse(400, ...)` check before processing.

### ✅ 13. Grad-CAM skips 224×224 intermediate resize

**File:** `stub_model_server/inference.py:62-63`

Added an intermediate resize to 224×224 before scaling to the crop size: `cam → 224×224 → min_dim`. Aligns the heatmap with the model's actual feature space.

### ✅ 14. Redundant RGB→grayscale double conversion

**File:** `stub_model_server/main.py:60`

Changed `.convert("RGB")` to `.convert("L")` in main.py since preprocess_image immediately converts to grayscale anyway. No wasted memory.

### ✅ 15. "Analyze" button in Header has no onClick handler

**File:** `frontend/src/components/Header.jsx:24`

Added `import { useNavigate }` and wired `onClick={() => navigate('/xray-screening')}`.

### ✅ 16. Empty `.catch()` silently swallows API errors on three pages

**File:** `frontend/src/pages/Dashboard.jsx:40`, `frontend/src/pages/Records.jsx:42`, `frontend/src/pages/PatientHistory.jsx:39`

Replaced empty `.catch(() => {})` with `.catch(() => setLoadError('...'))` on all three pages. Error banner displayed at the top of each page's content area.

### ✅ 17. No request cancellation on unmount

**File:** `frontend/src/pages/XRayScreening.jsx:32-48`

Added `abortRef` with `useEffect` cleanup that calls `abortRef.current.abort()` on unmount. `AbortError` is caught and silently ignored. Also revokes blob URL on unmount.

### ✅ 18. No client-side file size validation

**File:** `frontend/src/pages/XRayScreening.jsx`

Added `selectFile()` check: `if (f.size > 10 * 1024 * 1024)` immediately shows error and rejects the file. Also done for drag-and-drop.

### ✅ 19. No 404 catch-all route

**File:** `frontend/src/App.jsx`

Added `<Route path="*" element={<NotFound />} />`. Created `frontend/src/pages/NotFound.jsx` with a friendly message and "Go to Dashboard" button.

### ✅ 20. CORS allows `localhost:5173` contrary to spec

**File:** `backend/app/main.py:35-37`

Removed `"http://localhost:5173"` from `allow_origins`. Only `http://localhost:3000` remains.

---

## LOW

### ✅ 21. `from matplotlib import colormaps` inside per-request function

**File:** `stub_model_server/inference.py:74-75`

Moved `from matplotlib import colormaps` to top of file (line 9).

### ✅ 22. Transform objects recreated on every request

**File:** `stub_model_server/inference.py:39-42`

Moved `_transform` creation to module level (between `_model = None` and `load_model()`).

### ✅ 23. MIME type check is case-sensitive

**File:** `stub_model_server/main.py:45`

Changed to `file.content_type.lower() not in allowed` with `None` guard.

### ✅ 24. Fragile `op_threshs` save-then-null pattern is undocumented

**File:** `stub_model_server/inference.py:17-18`

Added a block comment explaining why `op_threshs` is saved then nulled.
