import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'

export default function OCRProcessing() {
  const navigate = useNavigate()
  const [isSaving, setIsSaving] = useState(false)

  const handleConfirm = (e) => {
    e.preventDefault()
    setIsSaving(true)
    setTimeout(() => {
      setIsSaving(false)
      navigate('/lab-results')
    }, 1500)
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 ml-[260px] flex flex-col">
        <Header />
        <div className="flex flex-1 pt-16 overflow-hidden">
          <section className="w-3/5 h-full flex flex-col bg-surface-container-lowest border-r border-outline-variant relative overflow-auto custom-scrollbar">
            <div className="p-md bg-white border-b border-outline-variant flex justify-between items-center sticky top-0 z-10">
              <div className="flex items-center gap-sm">
                <span className="material-symbols-outlined text-primary">visibility</span>
                <h2 className="text-lg font-semibold">Report Preview</h2>
              </div>
            </div>
            <div className="p-xl flex justify-center bg-[#2b2d31]">
              <div className="bg-white shadow-xl min-w-[600px] h-fit p-xl border border-outline-variant text-black">
                <div className="flex justify-between border-b-2 border-black pb-md mb-lg">
                  <div>
                    <h3 className="font-bold text-xl uppercase">City Diagnostic Center</h3>
                    <p className="text-xs">Sector 14, Gurgaon, Haryana</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs font-bold">REPORT ID: UJ-99283-A</p>
                    <p className="text-xs">Date: 24-Oct-2023</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-md mb-xl text-sm">
                  <div><span className="font-bold">PATIENT:</span> AMITABH SHARMA</div>
                  <div><span className="font-bold">REPORT TYPE:</span> CHEST X-RAY</div>
                </div>
                <div className="space-y-md">
                  <h4 className="font-bold border-b border-gray-300 pb-xs uppercase">Findings:</h4>
                  <p className="text-sm">Bilateral lung fields show normal vascularity. Heart size and configuration normal.</p>
                </div>
              </div>
            </div>
          </section>
          <section className="w-2/5 h-full bg-surface p-xl overflow-y-auto custom-scrollbar border-l border-outline-variant">
            <div className="mb-lg">
              <h2 className="text-xl font-bold">OCR Verification</h2>
              <p className="text-sm text-on-surface-variant">Review extracted information.</p>
            </div>
            <form className="space-y-lg" onSubmit={handleConfirm}>
              <div className="space-y-sm">
                <label className="text-xs text-on-surface-variant">PATIENT NAME</label>
                <input className="w-full bg-white border border-outline rounded p-md" defaultValue="AMITABH SHARMA" />
              </div>
              <div className="grid grid-cols-2 gap-lg">
                <div className="space-y-sm">
                  <label className="text-xs text-on-surface-variant">DATE</label>
                  <input className="w-full bg-white border border-outline rounded p-md" type="date" defaultValue="2023-10-24" />
                </div>
                <div className="space-y-sm">
                  <label className="text-xs text-on-surface-variant">REPORT TYPE</label>
                  <select className="w-full bg-white border border-outline rounded p-md">
                    <option>Chest X-Ray</option>
                    <option>Lab Panel</option>
                  </select>
                </div>
              </div>
              <div className="pt-xl border-t border-outline-variant flex gap-md">
                <button type="button" onClick={() => navigate(-1)} className="flex-1 bg-surface-container-high border border-outline-variant py-md rounded">
                  Discard
                </button>
                <button type="submit" className="flex-[2] bg-primary text-on-primary font-semibold py-md rounded shadow-lg flex items-center justify-center gap-sm">
                  {isSaving ? <span className="material-symbols-outlined animate-spin">sync</span> : <span className="material-symbols-outlined">verified</span>}
                  {isSaving ? 'Saving...' : 'Confirm & Save'}
                </button>
              </div>
            </form>
          </section>
        </div>
      </div>
    </div>
  )
}
