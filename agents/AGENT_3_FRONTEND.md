# Agent Instructions — Frontend

## Tech
React + Vite, Tailwind CSS v3 (Material Design 3 token palette). Runs on `localhost:3000`.

## Responsibility
Full medical portal UI. Upload chest X-ray images, process text-based medical reports (lab panels, discharge summaries, referral letters via OCR), display screening & report results, browse records, view expanded patient history and demographics. Display only — uses values from Backend as-is; threshold comparisons are done client-side using `op_threshs`.

## Pages & Routes

| Route | Component | Purpose |
|---|---|---|
| `/` | Dashboard | Stats cards, recent uploads table |
| `/upload-selector` | UploadSelector | Choose between Report (OCR) and Scan (X-Ray) |
| `/ocr-processing` | OCRProcessing | Three-state report workflow: Upload → Verification → Success |
| `/xray-screening` | XRayScreening | Upload → loading → results (prediction badge, confidence, heatmap, pathology scores) |
| `/brain-mri` | BrainMRI | MRI viewer with slice slider, findings, impression |
| `/lab-results` | LabResults | CBC table with normal/low flags |
| `/history` | PatientHistory | Chronological table of interactions |
| `/records` | Records | Card grid of past uploads (X-rays and medical reports) |
| `/settings` | Settings | Portal configuration (placeholder) |
| `/patients/:id` | PatientProfile | Patient detail with expanded demographics, documents, scan results, and report result view modals |
| `*` | NotFound | 404 catch-all with navigation back to dashboard |

## Shared Components
- **Sidebar** — fixed left nav (260px), menu items + Upload CTA
- **Header** — fixed top bar with search, notifications, user info
- **MainLayout** — composes Sidebar + Header + content area
- **PathologyScores** — findings chip logic + collapsible detailed score bars (used by XRayScreening, Records, PatientProfile)

## OCR Processing Flow (`/ocr-processing`)
- **State 1: Upload**
  - Accepts JPEG, PNG, and PDF documents (up to 20 MB)
  - Patient selector dropdown ("— New patient —" default or link to an existing patient)
  - Click or drag-and-drop file upload zone
  - Submit triggers `POST /reports/upload` (`uploadReport`) to run local OCR
- **State 2: Verification**
  - Split-pane layout:
    - **Left pane**: Live document preview (inline image view or PDF viewer via `<embed>` / page previews)
    - **Right pane**: Editable form pre-filled with OCR-extracted fields:
      - Patient name, report date, report type dropdown (`lab_panel`, `discharge_summary`, `referral_letter`, `other`)
      - Doctor name, facility name
      - Extracted key-value pairs table with add/remove row controls
      - Collapsible raw OCR text section
      - Collapsible patient demographics section (age, sex, DOB, contact, MRN, referring physician)
  - Submit triggers `POST /reports/confirm` (`confirmReport`) to persist records
- **State 3: Success**
  - Confirmation card summarizing saved document and patient details, with a direct link to the patient profile

## X-Ray Screening Results Display
- Prediction badge (red for any non-normal finding, green for normal) with label capitalized for display
- Side-by-side original image and heatmap overlay (base64 PNG from backend)
- Model name displayed in the results footer (sourced from `model_used` in backend response — never hardcoded)
- **Findings display** — driven by `NON_PATHOLOGY_LABELS = {'lung opacity', 'support device'}` in `src/components/PathologyScores.jsx`:
  - `support device`: shown as a distinct amber chip ("Support Device Detected") if flagged above threshold — not listed under pathology findings
  - `lung opacity`: silently suppressed from displayed findings (nonspecific co-occurring descriptor; still shown in detailed scores)
  - All other labels where `score >= op_threshs[name]` → shown as red badges under "Flagged Findings", sorted descending by score
  - If no pathology findings AND no support device → "No findings above threshold"
- **Detailed scores** (collapsed by default): toggle "View detailed pathology scores" with expand icon — all labels sorted descending, neutral gray progress bars, with caveat: "These are raw model scores, not calibrated probabilities."
- All labels capitalized for display via `str.replace(/(^\w|\s\w)/g, c => c.toUpperCase())`

## X-Ray Screening Upload
- Patient name input (required, validated non-empty; "Analyze" disabled until both file and name present)
- Optional patient selector dropdown ("— New patient —" default) lists existing patients for linking scans
- File input accepts JPEG/PNG, validates size ≤ 10 MB client-side before upload; click or drag-and-drop onto the drop zone, with live image preview
- 60s default timeout on API calls; 120s for `POST /screen`; uses `AbortController` for cancellation (aborts on unmount / "Analyze Another")
- Loading state shows spinner with indeterminate progress bar
- Error handling: 413 → size limit, 502 → model server unavailable, 400 → validation message, AbortError → silently ignored (user navigated away)

## Records & Patient Profile Display
- **Records (`/records`)**:
  - Displays grid cards for both scan documents and report documents
  - `document_type === "report"` shows report type badge, extracted date, doctor name, and truncated raw text preview instead of heatmap
- **Patient Profile (`/patients/:id`)**:
  - Profile header displays expanded patient demographic fields: age, sex, DOB, contact, MRN, referring physician, medical history
  - Document history section lists both X-ray scans and medical reports
  - Clicking a report document opens a modal viewing extracted fields, raw text, and report file preview

## API Integration
- `uploadReport(file)` — `POST /reports/upload` (120s timeout, accepts image/PDF ≤ 20 MB)
- `confirmReport(data)` — `POST /reports/confirm` (60s timeout, persists Patient + Document + ReportResult)
- `reportFileUrl(documentId)` — `GET /reports/{documentId}/file` streaming helper
- `screenXray(file, patientName, patientId)` — `POST /screen` (120s timeout)
- `fetchPatients`, `fetchPatientStats`, `fetchPatient`, `fetchPatientDocuments`, `fetchDocument`
- `imageUrl(docId)`, `heatmapUrl(scanId)`
- Centralized in `src/api/client.js`
- All pages display load errors in a red banner when API calls fail (no silent `.catch()`)

## Rules
- Never call Model Server directly — always go through Backend
- Never hardcode model names — use `model_used` from Backend response
- Threshold comparison (`score >= op_threshs[name]`) is done client-side in `PathologyScores.jsx` (rendered by XRayScreening, Records, and PatientProfile) — `op_threshs` comes from Backend
- CORS: calls `localhost:8000` only (`VITE_API_URL`, default `http://localhost:8000`)
