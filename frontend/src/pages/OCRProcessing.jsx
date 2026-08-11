import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import { uploadReport, confirmReport, fetchPatients } from '../api/client'

export default function OCRProcessing() {
  const navigate = useNavigate()
  
  // State 1: Upload
  const [file, setFile] = useState(null)
  const [patients, setPatients] = useState([])
  const [selectedPatientId, setSelectedPatientId] = useState('')
  
  // State 2: Verification
  const [step, setStep] = useState(1) // 1: Upload, 2: Verification, 3: Success
  const [isUploading, setIsUploading] = useState(false)
  const [ocrData, setOcrData] = useState(null)
  const [previewUrl, setPreviewUrl] = useState(null)
  
  // Verification form state
  const [formData, setFormData] = useState({})
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState(null)

  useEffect(() => {
    fetchPatients().then(setPatients).catch(console.error)
  }, [])

  const handleFileDrop = (e) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      setFile(droppedFile)
      setPreviewUrl(URL.createObjectURL(droppedFile))
    }
  }

  const handleFileSelect = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0]
      setFile(selectedFile)
      setPreviewUrl(URL.createObjectURL(selectedFile))
    }
  }

  const handleUploadSubmit = async (e) => {
    e.preventDefault()
    if (!file) return

    setIsUploading(true)
    try {
      const data = await uploadReport(file)
      setOcrData(data)
      setFormData({
        patient_name: selectedPatientId ? patients.find(p => p.id === selectedPatientId)?.name : (data.extracted_patient_name || ''),
        report_date: data.extracted_report_date || '',
        report_type: data.extracted_report_type || 'lab_panel',
        doctor_name: data.extracted_doctor_name || '',
        facility_name: data.extracted_facility_name || '',
        extracted_fields: data.extracted_fields || {},
        // Demographic fields
        patient_age: '',
        patient_sex: '',
        patient_dob: '',
        patient_contact: '',
        patient_mrn: '',
        referring_physician: ''
      })
      setStep(2)
    } catch (err) {
      alert(err.message)
    } finally {
      setIsUploading(false)
    }
  }

  const handleConfirm = async (e) => {
    e.preventDefault()
    setIsSaving(true)
    setSaveError(null)
    
    try {
      const payload = {
        temp_id: ocrData.temp_id,
        patient_id: selectedPatientId || null,
        patient_name: formData.patient_name,
        report_type: formData.report_type,
        report_date: formData.report_date,
        doctor_name: formData.doctor_name,
        facility_name: formData.facility_name,
        extracted_fields: formData.extracted_fields,
        raw_text: ocrData.raw_text,
        // Include demographic fields if it's a new patient
        ...(!selectedPatientId && {
          patient_age: formData.patient_age ? parseInt(formData.patient_age, 10) : null,
          patient_sex: formData.patient_sex || null,
          patient_dob: formData.patient_dob || null,
          patient_contact: formData.patient_contact || null,
          patient_mrn: formData.patient_mrn || null,
          referring_physician: formData.referring_physician || null,
        })
      }
      
      const response = await confirmReport(payload)
      // Navigate to patient profile on success
      navigate(`/patients/${response.patient_id}`)
    } catch (err) {
      setSaveError(err.message)
      setIsSaving(false)
    }
  }

  const handleFieldChange = (key, value) => {
    setFormData(prev => ({
      ...prev,
      extracted_fields: {
        ...prev.extracted_fields,
        [key]: value
      }
    }))
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 ml-[260px] flex flex-col">
        <Header />
        
        {step === 1 && (
          <div className="flex-1 flex flex-col items-center justify-center p-xl">
            <h2 className="text-2xl font-bold mb-lg">Upload Medical Report</h2>
            <form onSubmit={handleUploadSubmit} className="bg-white p-xl rounded-xl border border-outline w-full max-w-2xl space-y-lg shadow-sm">
              <div 
                className="border-2 border-dashed border-outline-variant p-xl text-center rounded-lg hover:bg-surface-container transition-colors cursor-pointer"
                onDragOver={e => e.preventDefault()}
                onDrop={handleFileDrop}
                onClick={() => document.getElementById('file-upload').click()}
              >
                <input type="file" id="file-upload" className="hidden" onChange={handleFileSelect} accept="image/jpeg,image/png,application/pdf" />
                <span className="material-symbols-outlined text-4xl text-on-surface-variant mb-sm">upload_file</span>
                <p className="font-semibold">{file ? file.name : "Drag & drop a file here"}</p>
                <p className="text-sm text-on-surface-variant mt-1">Accepts JPEG, PNG, PDF (up to 20MB)</p>
              </div>

              <div className="space-y-md">
                <h3 className="font-semibold border-b pb-sm">Patient Information</h3>
                
                <div className="grid grid-cols-2 gap-md">
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-on-surface-variant mb-1">EXISTING PATIENT (OPTIONAL)</label>
                    <select 
                      className="w-full border rounded p-2"
                      value={selectedPatientId}
                      onChange={e => setSelectedPatientId(e.target.value)}
                    >
                      <option value="">-- Create New Patient --</option>
                      {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                    <p className="text-xs text-on-surface-variant mt-2">
                      Leave as "-- Create New Patient --" to automatically extract the patient's name from the report.
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-md pt-md">
                <button type="button" onClick={() => navigate(-1)} className="px-6 py-2 border rounded font-semibold text-on-surface hover:bg-surface-container">Cancel</button>
                <button 
                  type="submit" 
                  disabled={!file || isUploading}
                  className="px-6 py-2 bg-primary text-on-primary rounded font-semibold disabled:opacity-50 flex items-center gap-2"
                >
                  {isUploading ? <span className="material-symbols-outlined animate-spin text-sm">sync</span> : null}
                  {isUploading ? 'Processing...' : 'Upload & Extract'}
                </button>
              </div>
            </form>
          </div>
        )}

        {step === 2 && (
          <div className="flex flex-1 pt-16 overflow-hidden">
            <section className="w-1/2 h-full flex flex-col bg-surface-container-lowest border-r border-outline-variant relative overflow-auto custom-scrollbar">
              <div className="p-md bg-white border-b border-outline-variant flex justify-between items-center sticky top-0 z-10">
                <div className="flex items-center gap-sm">
                  <span className="material-symbols-outlined text-primary">visibility</span>
                  <h2 className="text-lg font-semibold">Report Preview</h2>
                </div>
                <div className="text-sm font-semibold">{ocrData?.page_count} Page(s)</div>
              </div>
              <div className="p-xl flex flex-col gap-lg items-center bg-[#2b2d31]">
                {file?.type === 'application/pdf' ? (
                  <embed src={previewUrl} type="application/pdf" className="w-full h-[800px] bg-white" />
                ) : (
                  <img src={previewUrl} alt="Report Preview" className="max-w-full shadow-xl bg-white" />
                )}
              </div>
            </section>
            
            <section className="w-1/2 h-full bg-surface p-xl overflow-y-auto custom-scrollbar">
              <div className="mb-lg">
                <h2 className="text-xl font-bold">OCR Verification</h2>
                <p className="text-sm text-on-surface-variant">Review and correct extracted information.</p>
              </div>
              
              {saveError && (
                <div className="mb-md p-3 bg-error-container text-on-error-container rounded flex gap-2">
                  <span className="material-symbols-outlined text-sm">error</span>
                  {saveError}
                </div>
              )}

              <form className="space-y-lg" onSubmit={handleConfirm}>
                <div className="bg-white p-xl rounded-xl border border-outline shadow-sm space-y-md">
                  <h3 className="font-semibold text-lg border-b pb-sm mb-md flex justify-between items-center">
                    Document Metadata
                    {selectedPatientId && <span className="text-xs bg-secondary text-on-secondary px-2 py-1 rounded-full">Existing Patient</span>}
                  </h3>
                  
                  <div className="space-y-sm">
                    <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Patient Name</label>
                    <input 
                      className="w-full bg-white border border-outline rounded p-md" 
                      value={formData.patient_name}
                      onChange={e => setFormData({...formData, patient_name: e.target.value})}
                      disabled={!!selectedPatientId}
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-lg">
                    <div className="space-y-sm">
                      <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Report Date</label>
                      <input 
                        className="w-full bg-white border border-outline rounded p-md" 
                        value={formData.report_date}
                        onChange={e => setFormData({...formData, report_date: e.target.value})}
                        placeholder="DD/MM/YYYY or YYYY-MM-DD"
                      />
                    </div>
                    <div className="space-y-sm">
                      <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Report Type</label>
                      <select 
                        className="w-full bg-white border border-outline rounded p-md"
                        value={formData.report_type}
                        onChange={e => setFormData({...formData, report_type: e.target.value})}
                      >
                        <option value="lab_panel">Lab Panel</option>
                        <option value="discharge_summary">Discharge Summary</option>
                        <option value="referral_letter">Referral Letter</option>
                        <option value="other">Other</option>
                      </select>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-lg">
                    <div className="space-y-sm">
                      <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Doctor Name</label>
                      <input 
                        className="w-full bg-white border border-outline rounded p-md" 
                        value={formData.doctor_name}
                        onChange={e => setFormData({...formData, doctor_name: e.target.value})}
                      />
                    </div>
                    <div className="space-y-sm">
                      <label className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">Facility Name</label>
                      <input 
                        className="w-full bg-white border border-outline rounded p-md" 
                        value={formData.facility_name}
                        onChange={e => setFormData({...formData, facility_name: e.target.value})}
                      />
                    </div>
                  </div>
                </div>

                {!selectedPatientId && (
                  <details className="bg-white p-xl rounded-xl border border-outline shadow-sm space-y-md group">
                    <summary className="font-semibold text-lg cursor-pointer list-none flex justify-between items-center border-b pb-sm">
                      New Patient Demographics
                      <span className="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
                    </summary>
                    <div className="grid grid-cols-2 gap-md pt-md">
                      <div className="space-y-xs">
                        <label className="text-xs text-on-surface-variant uppercase">Age</label>
                        <input type="number" className="w-full border rounded p-2" value={formData.patient_age} onChange={e => setFormData({...formData, patient_age: e.target.value})} />
                      </div>
                      <div className="space-y-xs">
                        <label className="text-xs text-on-surface-variant uppercase">Sex</label>
                        <select className="w-full border rounded p-2" value={formData.patient_sex} onChange={e => setFormData({...formData, patient_sex: e.target.value})}>
                          <option value="">Unspecified</option>
                          <option value="M">Male</option>
                          <option value="F">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      <div className="space-y-xs">
                        <label className="text-xs text-on-surface-variant uppercase">DOB</label>
                        <input type="text" className="w-full border rounded p-2" placeholder="YYYY-MM-DD" value={formData.patient_dob} onChange={e => setFormData({...formData, patient_dob: e.target.value})} />
                      </div>
                      <div className="space-y-xs">
                        <label className="text-xs text-on-surface-variant uppercase">Contact</label>
                        <input type="text" className="w-full border rounded p-2" value={formData.patient_contact} onChange={e => setFormData({...formData, patient_contact: e.target.value})} />
                      </div>
                      <div className="space-y-xs">
                        <label className="text-xs text-on-surface-variant uppercase">MRN</label>
                        <input type="text" className="w-full border rounded p-2" value={formData.patient_mrn} onChange={e => setFormData({...formData, patient_mrn: e.target.value})} />
                      </div>
                      <div className="space-y-xs">
                        <label className="text-xs text-on-surface-variant uppercase">Ref. Physician</label>
                        <input type="text" className="w-full border rounded p-2" value={formData.referring_physician} onChange={e => setFormData({...formData, referring_physician: e.target.value})} />
                      </div>
                    </div>
                  </details>
                )}

                <div className="bg-white p-xl rounded-xl border border-outline shadow-sm">
                  <h3 className="font-semibold text-lg border-b pb-sm mb-md">Extracted Fields</h3>
                  <div className="space-y-sm">
                    {Object.entries(formData.extracted_fields || {}).map(([key, val], idx) => (
                      <div key={idx} className="flex gap-2">
                        <input className="flex-1 bg-surface-container border border-outline rounded p-2 text-sm font-semibold" value={key} readOnly />
                        <input className="flex-[2] bg-white border border-outline rounded p-2 text-sm" value={val} onChange={e => handleFieldChange(key, e.target.value)} />
                      </div>
                    ))}
                    {Object.keys(formData.extracted_fields || {}).length === 0 && (
                      <p className="text-sm text-on-surface-variant italic">No structured fields extracted.</p>
                    )}
                  </div>
                </div>

                <details className="bg-white p-xl rounded-xl border border-outline shadow-sm group">
                  <summary className="font-semibold text-lg cursor-pointer list-none flex justify-between items-center border-b pb-sm">
                    Raw OCR Text
                    <span className="material-symbols-outlined text-on-surface-variant group-open:rotate-180 transition-transform">expand_more</span>
                  </summary>
                  <pre className="mt-md p-md bg-surface-container-lowest border rounded text-xs whitespace-pre-wrap max-h-64 overflow-y-auto">
                    {ocrData?.raw_text}
                  </pre>
                </details>

                <div className="pt-lg border-t border-outline-variant flex gap-md sticky bottom-0 bg-surface py-md z-10">
                  <button type="button" onClick={() => { setStep(1); setOcrData(null); }} className="flex-1 bg-surface-container-high border border-outline-variant py-md rounded font-semibold hover:bg-surface-container">
                    Cancel
                  </button>
                  <button type="submit" disabled={isSaving} className="flex-[2] bg-primary text-on-primary font-semibold py-md rounded shadow-lg flex items-center justify-center gap-sm disabled:opacity-50">
                    {isSaving ? <span className="material-symbols-outlined animate-spin">sync</span> : <span className="material-symbols-outlined">verified</span>}
                    {isSaving ? 'Saving...' : 'Confirm & Save'}
                  </button>
                </div>
              </form>
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
