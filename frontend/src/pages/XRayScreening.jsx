import { useState, useRef, useCallback, useEffect } from 'react'
import MainLayout from '../components/MainLayout'
import PathologyScores from '../components/PathologyScores'
import { screenXray, fetchPatients } from '../api/client'

const MAX_FILE_SIZE = 10 * 1024 * 1024

export default function XRayScreening() {
  const [state, setState] = useState('upload')
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [patientName, setPatientName] = useState('')
  const [selectedPatientId, setSelectedPatientId] = useState('')
  const [patients, setPatients] = useState([])
  const inputRef = useRef(null)
  const abortRef = useRef(null)

  useEffect(() => {
    fetchPatients()
      .then(setPatients)
      .catch(() => {})
  }, [])

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort()
      if (preview) URL.revokeObjectURL(preview)
    }
  }, [preview])

  const selectFile = useCallback((f) => {
    if (!f) return
    if (f.size > MAX_FILE_SIZE) {
      setError('File exceeds the 10 MB size limit.')
      return
    }
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

  const canAnalyze = file && patientName.trim().length > 0

  const handleAnalyze = async () => {
    if (!canAnalyze) return
    const controller = new AbortController()
    abortRef.current = controller
    setState('loading')
    setError(null)
    try {
      const data = await screenXray(
        file,
        patientName.trim(),
        selectedPatientId || null,
        controller.signal
      )
      if (controller.signal.aborted) return
      setResult(data)
      setState('results')
    } catch (err) {
      if (err.name === 'AbortError') return
      let message = err.message || 'Something went wrong'
      if (err.status === 413) message = 'File exceeds the 10 MB size limit.'
      else if (err.status === 502) message = 'Model server is unavailable. Please try again later.'
      else if (err.status === 400) message = err.message || 'Invalid file. Please upload a JPEG or PNG image.'
      setError(message)
      setState('upload')
    }
  }

  const reset = () => {
    if (abortRef.current) abortRef.current.abort()
    setState('upload')
    setFile(null)
    if (preview) URL.revokeObjectURL(preview)
    setPreview(null)
    setResult(null)
    setError(null)
    setPatientName('')
    setSelectedPatientId('')
  }

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

              <div className="w-full">
                <label className="block text-sm font-medium text-on-surface mb-xs">
                  Patient Name <span className="text-error">*</span>
                </label>
                <input
                  type="text"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder="e.g. Priya Mehta"
                  className="w-full px-md py-sm border border-outline-variant rounded-lg bg-surface text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
              </div>

              {patients.length > 0 && (
                <div className="w-full">
                  <label className="block text-sm font-medium text-on-surface mb-xs">
                    Link to existing patient (optional)
                  </label>
                  <select
                    value={selectedPatientId}
                    onChange={(e) => setSelectedPatientId(e.target.value)}
                    className="w-full px-md py-sm border border-outline-variant rounded-lg bg-surface text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                  >
                    <option value="">— New patient —</option>
                    {patients.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
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
                    <button
                      onClick={handleAnalyze}
                      disabled={!canAnalyze}
                      className="bg-primary text-on-primary py-sm px-xl rounded-lg text-sm font-medium hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Analyze
                    </button>
                  </div>
                </div>
              )}

              {file && !patientName.trim() && (
                <p className="text-xs text-secondary w-full">Enter a patient name to enable analysis.</p>
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
                <p className="text-lg font-semibold text-on-surface mb-md">Analyzing chest X-ray…</p>
                <div className="progress-bar-indeterminate rounded-full" />
                <p className="text-xs text-secondary mt-md italic">Running pathology detection model…</p>
              </div>
            </div>
          </div>
        )}

        {state === 'results' && result && (
          <div className="bg-surface-container-lowest w-full max-w-[960px] border border-outline-variant rounded-xl overflow-hidden mx-auto">
            <div className="px-xl py-lg border-b border-outline-variant">
              <h3 className="text-lg font-semibold text-on-surface">Screening Results</h3>
              <p className="text-xs text-on-surface-variant mt-0.5">Patient: <span className="font-semibold">{result.patient_name}</span></p>
            </div>
            <div className="px-xl py-lg border-b border-outline-variant flex flex-wrap gap-lg items-center">
              <div className="flex items-center gap-md">
                <span className="text-xs text-secondary uppercase tracking-widest">Prediction</span>
                <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                  result.prediction === 'normal'
                    ? 'bg-tertiary-container text-on-tertiary-container'
                    : 'bg-error-container text-error'
                }`}>
                  {result.prediction.replace(/(^\w|\s\w)/g, c => c.toUpperCase())}
                </span>
              </div>
              <div className="flex items-center gap-md">
                <span className="text-xs text-secondary uppercase tracking-widest">Confidence</span>
                <span className="text-sm font-semibold">{(result.confidence * 100).toFixed(1)}%</span>
              </div>
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
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-xl">
                <div className="space-y-xs flex-1">
                  <p className="text-sm text-on-surface-variant">
                    Model: <span className="font-semibold text-on-surface">{result.model_used}</span>
                  </p>
                  <PathologyScores scores={result.pathology_scores} opThreshs={result.op_threshs} />
                </div>
                <button onClick={reset} className="bg-primary text-on-primary py-sm px-xl rounded-lg hover:opacity-90 transition-opacity shrink-0">
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