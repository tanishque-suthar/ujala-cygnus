import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import UploadSelector from './pages/UploadSelector'
import OCRProcessing from './pages/OCRProcessing'
import XRayScreening from './pages/XRayScreening'
import BrainMRI from './pages/BrainMRI'
import LabResults from './pages/LabResults'
import PatientHistory from './pages/PatientHistory'
import Records from './pages/Records'
import Settings from './pages/Settings'
import PatientProfile from './pages/PatientProfile'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload-selector" element={<UploadSelector />} />
        <Route path="/ocr-processing" element={<OCRProcessing />} />
        <Route path="/xray-screening" element={<XRayScreening />} />
        <Route path="/brain-mri" element={<BrainMRI />} />
        <Route path="/lab-results" element={<LabResults />} />
        <Route path="/history" element={<PatientHistory />} />
        <Route path="/records" element={<Records />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/patients/:patientId" element={<PatientProfile />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
