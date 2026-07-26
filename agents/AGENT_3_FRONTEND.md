# Agent Instructions — Frontend

## Tech
React + Vite, Tailwind CSS v3 (Material Design 3 token palette). Runs on `localhost:3000`.

## Responsibility
Full medical portal UI. Upload chest X-ray images, display screening results (prediction, confidence, priority, heatmap, pathology scores), browse records, view patient history. Display only — never computes priority/confidence, uses values from Backend as-is.

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
- Priority badge (high/moderate/low) with color coding
- Prediction heading and confidence percentage
- **Pathology scores**: top 2 findings shown as compact badges, expandable "View all pathology scores" panel shows all 18 pathologies sorted by probability with progress bars (high scores ≥50% in red, others in blue)

## API Integration
- `POST /screen` — upload image + patient name, receive screening results
- `GET /patients`, `GET /patients/stats` — dashboard data
- `GET /patients/{id}` — patient profile
- `GET /image/{id}`, `GET /heatmap/{id}` — file streaming
- API client centralized in `src/api/client.js`

## Rules
- Never call Model Server directly — always go through Backend
- Never compute priority or confidence — display values from Backend as-is
- Never hardcode model names — use `model_used` from Backend response
- CORS: calls `localhost:8000` only
