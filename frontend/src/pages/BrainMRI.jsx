import { useState } from 'react'
import MainLayout from '../components/MainLayout'

export default function BrainMRI() {
  const [slice, setSlice] = useState(42)

  return (
    <MainLayout>
      <div className="max-w-container-max mx-auto p-lg">
        <div className="flex justify-between items-end mb-lg">
          <div>
            <h2 className="text-xl font-bold text-primary mb-xs">Brain MRI Result</h2>
            <p className="text-sm text-on-surface-variant">Patient: Maria Santos | Date: Oct 24, 2023</p>
          </div>
          <div className="flex gap-sm">
            <button className="px-md py-sm border border-primary text-primary rounded-lg">Print</button>
            <button className="px-md py-sm bg-primary text-on-primary rounded-lg">Download PDF</button>
          </div>
        </div>
        <div className="grid grid-cols-12 gap-lg">
          <div className="col-span-8 space-y-lg">
            <div className="bg-black border border-outline-variant rounded-xl overflow-hidden flex flex-col h-[520px] relative">
              <img
                className="w-full h-full object-contain"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuASshIZuLiTzifhrlGa_yUyGotGHG3XZXF0AsT0dxMJdL5sv7ZBAdShepTPq5cmCEFGbFvz7PBbv7XAOCj9g4mHHZLoCqziz_gYgABilJTa14At_yIkpfB0mBrvmYdvDAmdhIeyniuABPfBge3CRhaiR_P14WSKV8cMOpeRuH2Lvq8c0ZZfG7Acos4XIH4F9bU8f5kCUqUl2Wr80Wn7abDS8JTCADYG_6idu01YUoD9bEXuTMGpE04t8g"
                alt="Brain MRI scan"
              />
              <div className="absolute bottom-0 w-full bg-surface-container-low/80 p-md flex items-center gap-md">
                <input
                  type="range"
                  min="1"
                  max="60"
                  value={slice}
                  onChange={(e) => setSlice(e.target.value)}
                  className="flex-1 accent-primary"
                />
                <span className="text-white font-mono">{slice} / 60</span>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-lg">
              <div className="bg-white border border-outline-variant rounded-xl p-lg">
                <h3 className="text-lg font-semibold text-primary mb-md">Findings</h3>
                <p className="text-sm leading-relaxed text-on-surface-variant">
                  Ventricular system is normal. No evidence of acute intracranial hemorrhage.
                </p>
              </div>
              <div className="bg-white border border-outline-variant rounded-xl p-lg">
                <h3 className="text-lg font-semibold text-primary mb-md">Impression</h3>
                <ul className="list-disc pl-4 text-sm text-on-surface-variant">
                  <li>No acute abnormality.</li>
                  <li>Mild chronic vessel changes.</li>
                </ul>
              </div>
            </div>
          </div>
          <div className="col-span-4 space-y-lg">
            <div className="bg-white border border-outline-variant rounded-xl p-md">
              <p className="text-xs uppercase text-secondary mb-md">Report Status</p>
              <span className="bg-tertiary-container text-on-tertiary-container px-2 py-1 rounded text-xs font-bold">COMPLETE</span>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
