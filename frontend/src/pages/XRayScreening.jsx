import { useState, useRef, useCallback } from 'react'
import MainLayout from '../components/MainLayout'
import { screenXray } from '../api/client'

const PRIORITY_STYLES = {
  high: { bg: 'bg-error', text: 'text-on-error', label: 'HIGH PRIORITY', icon: 'warning', heading: 'text-error' },
  moderate: { bg: 'bg-[#f59e0b]', text: 'text-white', label: 'MODERATE PRIORITY', icon: 'info', heading: 'text-[#f59e0b]' },
  low: { bg: 'bg-tertiary', text: 'text-on-tertiary', label: 'LOW PRIORITY', icon: 'check_circle', heading: 'text-tertiary' },
}

function formatPrediction(prediction) {
  return prediction === 'pneumonia' ? 'Pneumonia Detected' : 'Normal — No Findings'
}

export default function XRayScreening() {
  const [state, setState] = useState('upload')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  const selectFile = useCallback((f) => {
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError(null)
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragActive(false)
    const dropped = e.dataTransfer?.files?.[0]
    if (dropped) selectFile(dropped)
  }, [selectFile])

  const handleAnalyze = async () => {
    if (!file) return
    setState('loading')
    setError(null)
    try {
      const data = await screenXray(file)
      setResult(data)
      setState('results')
    } catch (err) {
      let message = err.message || 'Something went wrong'
      if (err.status === 413) message = 'File exceeds the 10 MB size limit.'
      else if (err.status === 502) message = 'Model server is unavailable. Please try again later.'
      else if (err.status === 400) message = err.message || 'Invalid file. Please upload a JPEG or PNG image.'
      setError(message)
      setState('upload')
    }
  }

  const reset = () => {
    setState('upload')
    setFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
    setResult(null)
    setError(null)
  }

  const priority = result ? (PRIORITY_STYLES[result.priority] || PRIORITY_STYLES.low) : null

  return (
    <MainLayout>
      <div className="max-w-container-max mx-auto p-xl">
        <div className="mb-xl">
          <h2 className="text-xl font-bold text-primary">Chest X-Ray Screening</h2>
          <p className="text-on-surface-variant">AI-Assisted Diagnostic Tool for Pulmonary Pathology</p>
        </div>

        {state === 'upload' && (
          <div className="flex flex-col items-center">
            <div className="bg-surface-container-lowest w-full max-w-[640px] border border-outline-variant rounded-xl p-xl flex flex-col items-center gap-lg">
              {error && (
                <div className="w-full bg-error-container text-on-error-container text-sm px-md py-sm rounded-lg flex items-center gap-sm">
                  <span className="material-symbols-outlined text-[18px]">error</span>
                  {error}
                </div>
              )}

              <input
                ref={inputRef}
                type="file"
                accept="image/jpeg,image/png"
                className="hidden"
                onChange={(e) => selectFile(e.target.files?.[0])}
              />

              <div
                onClick={() => inputRef.current?.click()}
                onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                className={`w-full h-64 border-2 border-dashed border-outline-variant rounded-lg bg-surface-container-low flex flex-col items-center justify-center gap-md cursor-pointer hover:bg-surface-container transition-colors ${dragActive ? 'drag-active' : ''}`}
              >
                {preview ? (
                  <img src={preview} alt="Selected X-ray" className="max-h-full max-w-full object-contain rounded" />
                ) : (
                  <>
                    <div className="w-16 h-16 rounded-full bg-primary-fixed flex items-center justify-center text-primary">
                      <span className="material-symbols-outlined text-[32px]">upload_file</span>
                    </div>
                    <p className="text-lg font-semibold">Click or Drop X-Ray here</p>
                    <p className="text-sm text-secondary">JPEG or PNG, up to 10 MB</p>
                  </>
                )}
              </div>

              {file && (
                <div className="w-full flex items-center justify-between">
                  <span className="text-sm text-on-surface-variant truncate max-w-[70%]">{file.name}</span>
                  <div className="flex gap-sm">
                    <button onClick={() => { setFile(null); setPreview(null) }} className="text-sm text-secondary hover:text-on-surface py-xs px-md rounded-lg border border-outline-variant">
                      Clear
                    </button>
                    <button onClick={handleAnalyze} className="bg-primary text-on-primary py-sm px-xl rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                      Analyze
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {state === 'loading' && (
          <div className="flex flex-col items-center">
            <div className="bg-surface-container-lowest w-full max-w-[640px] border border-outline-variant rounded-xl p-xl flex flex-col items-center gap-xl">
              <div className="relative w-24 h-24">
                <div className="absolute inset-0 border-4 border-primary-fixed rounded-full" />
                <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="material-symbols-outlined text-primary text-[32px] pulse-soft">clinical_notes</span>
                </div>
              </div>
              <div className="text-center w-full">
                <p className="text-lg font-semibold text-on-surface mb-md">Analyzing chest X-ray...</p>
                <div className="progress-bar-indeterminate rounded-full" />
                <p className="text-xs text-secondary mt-md italic">Running pathology detection model...</p>
              </div>
            </div>
          </div>
        )}

        {state === 'results' && result && (
          <div className="bg-surface-container-lowest w-full max-w-[960px] border border-outline-variant rounded-xl overflow-hidden mx-auto">
            <div className="px-xl py-lg border-b border-outline-variant flex justify-between items-center">
              <h3 className="text-lg font-semibold text-on-surface">Screening Results</h3>
              <span className={`${priority.bg} ${priority.text} text-xs px-md py-xs rounded-full flex items-center gap-xs`}>
                <span className="material-symbols-outlined text-[14px]" style={{ fontVariationSettings: "'FILL' 1" }}>{priority.icon}</span>
                {priority.label}
              </span>
            </div>
            <div className="p-xl grid grid-cols-1 md:grid-cols-2 gap-xl">
              <div className="space-y-sm">
                <p className="text-xs text-secondary uppercase tracking-widest">Original Image</p>
                <div className="aspect-square bg-black rounded-lg overflow-hidden border border-outline-variant">
                  <img className="w-full h-full object-cover" src={preview} alt="Original chest X-ray" />
                </div>
              </div>
              <div className="space-y-sm">
                <p className="text-xs text-secondary uppercase tracking-widest">Heatmap Overlay</p>
                <div className="aspect-square bg-black rounded-lg overflow-hidden border border-outline-variant">
                  <img className="w-full h-full object-cover" src={`data:image/png;base64,${result.heatmap_base64}`} alt="Heatmap overlay" />
                </div>
              </div>
            </div>
            <div className="px-xl py-xl bg-surface-container-low border-t border-outline-variant">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-xl">
                <div className="space-y-xs">
                  <h4 className={`text-lg font-semibold ${priority.heading}`}>{formatPrediction(result.prediction)}</h4>
                  <p className="text-sm text-on-surface-variant">
                    Confidence: <span className="font-semibold text-on-surface">{(result.confidence * 100).toFixed(1)}%</span>
                    <span className="mx-sm text-outline">·</span>
                    Model: <span className="font-semibold text-on-surface">{result.model_used}</span>
                  </p>
                </div>
                <button onClick={reset} className="bg-primary text-on-primary py-sm px-xl rounded-lg hover:opacity-90 transition-opacity">
                  Analyze Another
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}
