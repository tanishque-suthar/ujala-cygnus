import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'
import { fetchPatientStats, fetchPatients } from '../api/client'

const PRIORITY_COLOR = {
  high: 'bg-error-container',
  moderate: 'bg-[#fef3c7]',
  low: 'bg-tertiary-fixed-dim',
}

const DOC_TYPE_LABEL = {
  xray: 'Chest X-Ray',
  brain_mri: 'Brain MRI',
  ct: 'Abdominal CT',
  text_report: 'Text Report',
}

function initials(name) {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({ total_patients: null, total_documents: null })
  const [patients, setPatients] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([fetchPatientStats(), fetchPatients()])
      .then(([s, p]) => {
        setStats(s)
        setPatients(p)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const todayLabel = new Date().toLocaleDateString('en-IN', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

  const recentPatients = patients.slice(0, 5)

  return (
    <MainLayout>
      <div className="max-w-container-max mx-auto space-y-lg">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg items-end">
          <div className="md:col-span-8">
            <h2 className="text-2xl font-bold text-on-background">Medical Dashboard</h2>
            <p className="text-base text-on-surface-variant mt-base">Welcome back, Dr. Sharma. Here is an overview of your medical records and pending tasks.</p>
          </div>
          <div className="md:col-span-4 flex justify-end gap-sm">
            <div className="bg-surface border border-outline-variant p-4 rounded-lg flex items-center gap-4 w-full">
              <div className="p-3 bg-primary-fixed text-primary rounded-lg">
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>calendar_today</span>
              </div>
              <div>
                <p className="text-xs text-on-surface-variant uppercase tracking-wider">Today's Date</p>
                <p className="text-lg font-semibold text-on-surface">{todayLabel}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg">
          <div className="md:col-span-3 bg-white border border-outline-variant p-lg rounded-xl flex flex-col justify-between h-full">
            <div>
              <div className="w-10 h-10 rounded-lg bg-surface-container-low flex items-center justify-center text-primary mb-md">
                <span className="material-symbols-outlined">folder_shared</span>
              </div>
              <p className="text-sm text-on-surface-variant">Total Records</p>
              <p className="text-2xl font-bold mt-xs">
                {loading ? '—' : (stats.total_documents ?? 0).toLocaleString()}
              </p>
            </div>
            <div className="mt-md flex items-center text-tertiary text-sm">
              <span className="material-symbols-outlined text-sm mr-1">folder_open</span>
              <span>{loading ? '—' : stats.total_patients ?? 0} patients</span>
            </div>
          </div>

          <div className="md:col-span-3 bg-white border border-outline-variant p-lg rounded-xl flex flex-col justify-between h-full">
            <div>
              <div className="w-10 h-10 rounded-lg bg-primary-fixed flex items-center justify-center text-primary mb-md">
                <span className="material-symbols-outlined">person</span>
              </div>
              <p className="text-sm text-on-surface-variant">Total Patients</p>
              <p className="text-2xl font-bold mt-xs">
                {loading ? '—' : (stats.total_patients ?? 0).toLocaleString()}
              </p>
            </div>
            <div className="mt-md flex items-center text-primary text-sm">
              <span className="material-symbols-outlined text-sm mr-1">history</span>
              <span>All time</span>
            </div>
          </div>

          <div
            className="md:col-span-6 bg-white border border-outline-variant rounded-xl p-lg relative overflow-hidden group cursor-pointer"
            onClick={() => navigate('/upload-selector')}
          >
            <div className="absolute top-0 right-0 p-4 opacity-10 pointer-events-none transition-transform group-hover:scale-110">
              <span className="material-symbols-outlined text-9xl">cloud_upload</span>
            </div>
            <div className="relative z-10 flex flex-col h-full">
              <h3 className="text-lg font-semibold mb-md">Quick Actions</h3>
              <div className="flex-1 border-2 border-dashed border-outline-variant rounded-lg bg-surface-container-lowest flex flex-col items-center justify-center p-xl transition-all hover:bg-surface-container-low">
                <span className="material-symbols-outlined text-primary text-5xl mb-sm">upload_file</span>
                <p className="text-base font-semibold text-primary">Upload Scan</p>
                <p className="text-xs text-on-surface-variant mt-xs">Drag and drop MRI, CT, or X-Ray files here</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-lg">
          <div className="lg:col-span-8 bg-white border border-outline-variant rounded-xl overflow-hidden">
            <div className="p-lg border-b border-outline-variant flex justify-between items-center">
              <h3 className="text-lg font-semibold">Recent Patients</h3>
              <Link to="/records" className="text-primary text-sm font-semibold hover:underline">View All</Link>
            </div>
            <div className="overflow-x-auto">
              {loading ? (
                <div className="p-lg text-sm text-on-surface-variant">Loading…</div>
              ) : recentPatients.length === 0 ? (
                <div className="p-lg text-sm text-on-surface-variant">No patients yet. Upload a scan to get started.</div>
              ) : (
                <table className="w-full text-left">
                  <thead className="bg-surface text-on-surface-variant text-xs uppercase tracking-wider">
                    <tr>
                      <th className="px-lg py-4 border-b border-outline-variant font-semibold">Patient Name</th>
                      <th className="px-lg py-4 border-b border-outline-variant font-semibold">Records</th>
                      <th className="px-lg py-4 border-b border-outline-variant font-semibold">Registered</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-outline-variant text-sm">
                    {recentPatients.map((p) => (
                      <tr
                        key={p.id}
                        className="hover:bg-surface-container-lowest transition-colors cursor-pointer"
                        onClick={() => navigate(`/patients/${p.id}`)}
                      >
                        <td className="px-lg py-4 flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container text-xs">
                            {initials(p.name)}
                          </div>
                          <span>{p.name}</span>
                        </td>
                        <td className="px-lg py-4">{p.record_count}</td>
                        <td className="px-lg py-4 text-on-surface-variant">
                          {new Date(p.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
          <div className="lg:col-span-4 space-y-lg">
            <div className="bg-white border border-outline-variant rounded-xl p-lg">
              <div className="flex items-center justify-between mb-md">
                <h3 className="text-lg font-semibold">Quick Nav</h3>
              </div>
              <div className="space-y-sm">
                <button onClick={() => navigate('/records')} className="w-full flex items-center gap-3 p-md bg-surface-container-lowest rounded-lg hover:bg-surface-container transition-colors text-sm">
                  <span className="material-symbols-outlined text-primary">folder_open</span>
                  All Records
                </button>
                <button onClick={() => navigate('/history')} className="w-full flex items-center gap-3 p-md bg-surface-container-lowest rounded-lg hover:bg-surface-container transition-colors text-sm">
                  <span className="material-symbols-outlined text-primary">history</span>
                  Patient History
                </button>
                <button onClick={() => navigate('/upload-selector')} className="w-full flex items-center gap-3 p-md bg-surface-container-lowest rounded-lg hover:bg-surface-container transition-colors text-sm">
                  <span className="material-symbols-outlined text-primary">upload_file</span>
                  New Upload
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
