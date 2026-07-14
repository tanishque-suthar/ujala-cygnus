import { useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'

export default function UploadSelector() {
  const navigate = useNavigate()

  return (
    <MainLayout>
      <section className="flex-1 p-xl flex flex-col items-center justify-center">
        <div className="max-w-4xl w-full text-center mb-xl">
          <h2 className="text-2xl font-bold text-on-surface mb-xs">Select Upload Type</h2>
          <p className="text-base text-secondary max-w-xl mx-auto">
            Choose the appropriate category for your clinical data to initiate specialized processing and AI diagnostics.
          </p>
        </div>
        <div className="grid md:grid-cols-2 gap-lg max-w-5xl w-full">
          <div className="bg-white border border-outline-variant rounded-xl p-xl flex flex-col items-center text-center hover:shadow-lg transition-all duration-300">
            <div className="w-20 h-20 bg-primary-fixed rounded-full flex items-center justify-center mb-lg">
              <span className="material-symbols-outlined text-primary text-4xl">description</span>
            </div>
            <h3 className="text-xl font-bold text-on-surface mb-sm">Medical Report</h3>
            <p className="text-sm text-on-surface-variant mb-xl leading-relaxed">
              Upload clinical reports, discharge summaries, or prescriptions for AI-powered OCR analysis.
            </p>
            <button
              onClick={() => navigate('/ocr-processing')}
              className="mt-auto w-full bg-primary text-on-primary py-md px-xl rounded-lg font-bold text-base hover:bg-primary-container transition-colors active:scale-95 flex items-center justify-center gap-sm"
            >
              Select Report <span className="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>
          <div className="bg-white border border-outline-variant rounded-xl p-xl flex flex-col items-center text-center hover:shadow-lg transition-all duration-300">
            <div className="w-20 h-20 bg-tertiary-fixed rounded-full flex items-center justify-center mb-lg">
              <span className="material-symbols-outlined text-tertiary text-4xl">radiology</span>
            </div>
            <h3 className="text-xl font-bold text-on-surface mb-sm">Diagnostic Scan</h3>
            <p className="text-sm text-on-surface-variant mb-xl leading-relaxed">
              Upload DICOM, JPEG, or PNG images for automated pathology screening and heatmaps.
            </p>
            <button
              onClick={() => navigate('/xray-screening')}
              className="mt-auto w-full border-2 border-primary text-primary bg-transparent py-md px-xl rounded-lg font-bold text-base hover:bg-primary-fixed transition-colors active:scale-95 flex items-center justify-center gap-sm"
            >
              Select Scan <span className="material-symbols-outlined">arrow_forward</span>
            </button>
          </div>
        </div>
      </section>
    </MainLayout>
  )
}
