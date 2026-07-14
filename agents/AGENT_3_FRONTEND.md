# Agent Instructions — Frontend

## Tech
React + Vite, Tailwind CSS v3. Runs on `localhost:3000`.

## Responsibility
Full medical portal UI. Upload chest X-ray images, display screening
results (prediction, confidence, priority, heatmap), browse records,
view patient history. Display only — never computes priority/confidence
beyond formatting values received from Backend.

## Pages & Routes

| Route | Component | Purpose |
| --- | --- | --- |
| `/` | Dashboard | Stats cards, recent uploads table, notifications |
| `/upload-selector` | UploadSelector | Choose between Report (OCR) and Scan (X-Ray) |
| `/ocr-processing` | OCRProcessing | Split-pane report preview + editable OCR form |
| `/xray-screening` | XRayScreening | Upload → loading → results (original + heatmap) |
| `/brain-mri` | BrainMRI | MRI viewer with slice slider, findings, impression |
| `/lab-results` | LabResults | CBC table with normal/low flags |
| `/history` | PatientHistory | Chronological table of interactions |
| `/records` | Records | Card grid of past uploads |
| `/settings` | Settings | Portal configuration (placeholder) |

## Shared Components

- **Sidebar** — fixed left nav (260px), 4 menu items + Upload CTA
- **Header** — fixed top bar with search, notifications, user info
- **MainLayout** — composes Sidebar + Header + content area

## API Integration (planned)

The X-Ray Screening page will call `POST /screen` on the Backend
(`localhost:8000`) to upload an image and display results. Until wired
up, mock data with `setTimeout` simulates the analysis flow.

## Explicit rules
- Do not call the Model Server directly — always go through Backend.
- Do not compute priority or confidence — display values from Backend as-is.
- CORS: this app runs on `localhost:3000` and calls `localhost:8000` only.
- Do not hardcode model names in UI — use values returned by the Backend.
