# Agent Instructions — Frontend

## Tech
React + Vite, Tailwind CSS v3 (Material Design 3 token palette). Runs on `localhost:3000`.

## Responsibility
Full medical portal UI. Upload chest X-ray images, display screening results (heatmap, flagged findings, detailed pathology scores), browse records, view patient history. Display only — uses values from Backend as-is; threshold comparisons are done client-side using `op_threshs`.

## Pages & Routes

| Route | Component | Purpose |
|---|---|---|
| `/` | Dashboard | Stats cards, recent uploads table |
| `/upload-selector` | UploadSelector | Choose between Report (OCR) and Scan (X-Ray) |
| `/ocr-processing` | OCRProcessing | Split-pane report preview + editable OCR form |
| `/xray-screening` | XRayScreening | Upload → loading → results (original + heatmap + pathology scores) |
| `/brain-mri` | BrainMRI | MRI viewer with slice slider, findings, impression |
| `/lab-results` | LabResults | CBC table with normal/low flags |
| `/history` | PatientHistory | Chronological table of interactions |
| `/records` | Records | Card grid of past uploads |
| `/settings` | Settings | Portal configuration (placeholder) |

## Shared Components
- **Sidebar** — fixed left nav (260px), menu items + Upload CTA
- **Header** — fixed top bar with search, notifications, user info
- **MainLayout** — composes Sidebar + Header + content area

## X-Ray Screening Results Display
- Side-by-side original image and Grad-CAM heatmap overlay
- Model name displayed in the results footer
- **Flagged Findings** (default view): pathologies where `score >= op_threshs[name]`, shown as red badges with no numeric score. If zero flagged → "No findings above threshold"
  - Lung Opacity special rule: if Lung Opacity is flagged AND at least one of Consolidation/Infiltration/Effusion is also flagged → Lung Opacity is suppressed from the flagged list
  - If Lung Opacity is flagged alone → relabeled as "General Opacity (nonspecific)"
- **Detailed scores** (collapsed by default): toggle "View detailed pathology scores ▾" — all 18 pathologies sorted descending, neutral gray progress bars, labels say "model score" in spirit, with caveat: "These are raw model scores, not calibrated probabilities."
- No prediction heading or confidence percentage displayed

## API Integration
- `POST /screen` — upload image + patient name, receive screening results (includes `pathology_scores`, `op_threshs`, `heatmap_base64`, `model_used`)
- `GET /patients`, `GET /patients/stats` — dashboard data
- `GET /patients/{id}` — patient profile
- `GET /image/{id}`, `GET /heatmap/{id}` — file streaming
- API client centralized in `src/api/client.js`

## Rules
- Never call Model Server directly — always go through Backend
- Never hardcode model names — use `model_used` from Backend response
- Threshold comparison (`score >= op_threshs[name]`) is done client-side in `XRayScreening.jsx` to determine flagged findings — `op_threshs` comes from Backend
- CORS: calls `localhost:8000` only
