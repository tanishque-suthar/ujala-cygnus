import { Link, useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'

const recentUploads = [
  { name: 'Robert Hoffman', initials: 'RH', type: 'Chest X-Ray', date: 'Oct 24, 09:15 AM', status: 'Complete', color: 'bg-tertiary-fixed-dim' },
  { name: 'Maria Santos', initials: 'MS', type: 'Brain MRI', date: 'Oct 23, 04:30 PM', status: 'Analyzing', color: 'bg-primary-fixed' },
  { name: 'John Doe', initials: 'JD', type: 'Abdominal CT', date: 'Oct 23, 11:20 AM', status: 'Pending', color: 'bg-error-container' },
]

export default function Dashboard() {
  const navigate = useNavigate()

  return (
    <MainLayout>
      <div className="max-w-container-max mx-auto space-y-lg">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-lg items-end">
          <div className="md:col-span-8">
            <h2 className="text-2xl font-bold text-on-background">Medical Dashboard</h2>
            <p className="text-base text-on-surface-variant mt-base">Welcome back, Dr. Jenkins. Here is an overview of your medical records and pending tasks.</p>
          </div>
          <div className="md:col-span-4 flex justify-end gap-sm">
            <div className="bg-surface border border-outline-variant p-4 rounded-lg flex items-center gap-4 w-full">
              <div className="p-3 bg-primary-fixed text-primary rounded-lg">
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>calendar_today</span>
              </div>
              <div>
                <p className="text-xs text-on-surface-variant uppercase tracking-wider">Today's Date</p>
                <p className="text-lg font-semibold text-on-surface">Oct 24, 2023</p>
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
              <p className="text-2xl font-bold mt-xs">1,284</p>
            </div>
            <div className="mt-md flex items-center text-tertiary text-sm">
              <span className="material-symbols-outlined text-sm mr-1">trending_up</span>
              <span>12% from last month</span>
            </div>
          </div>

          <div className="md:col-span-3 bg-white border border-outline-variant p-lg rounded-xl flex flex-col justify-between h-full">
            <div>
              <div className="w-10 h-10 rounded-lg bg-error-container flex items-center justify-center text-error mb-md">
                <span className="material-symbols-outlined">pending_actions</span>
              </div>
              <p className="text-sm text-on-surface-variant">Pending Analysis</p>
              <p className="text-2xl font-bold mt-xs">24</p>
            </div>
            <div className="mt-md flex items-center text-error text-sm">
              <span className="material-symbols-outlined text-sm mr-1">warning</span>
              <span>4 High Priority</span>
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
              <h3 className="text-lg font-semibold">Recent Uploads</h3>
              <Link to="/records" className="text-primary text-sm font-semibold hover:underline">View All</Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead className="bg-surface text-on-surface-variant text-xs uppercase tracking-wider">
                  <tr>
                    <th className="px-lg py-4 border-b border-outline-variant font-semibold">Patient Name</th>
                    <th className="px-lg py-4 border-b border-outline-variant font-semibold">Report Type</th>
                    <th className="px-lg py-4 border-b border-outline-variant font-semibold">Date</th>
                    <th className="px-lg py-4 border-b border-outline-variant font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant text-sm">
                  {recentUploads.map((row, i) => (
                    <tr
                      key={i}
                      className="hover:bg-surface-container-lowest transition-colors cursor-pointer"
                      onClick={() => row.status === 'Complete' ? navigate('/brain-mri') : null}
                    >
                      <td className="px-lg py-4 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container text-xs">
                          {row.initials}
                        </div>
                        <span>{row.name}</span>
                      </td>
                      <td className="px-lg py-4">{row.type}</td>
                      <td className="px-lg py-4 text-on-surface-variant">{row.date}</td>
                      <td className="px-lg py-4">
                        <span className={`px-3 py-1 rounded-full ${row.color} text-xs font-bold uppercase tracking-tighter flex items-center w-fit`}>
                          <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${row.status === 'Complete' ? 'bg-tertiary' : row.status === 'Analyzing' ? 'bg-primary animate-pulse' : 'bg-error'}`} />
                          {row.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="lg:col-span-4 space-y-lg">
            <div className="bg-white border border-outline-variant rounded-xl p-lg">
              <div className="flex items-center justify-between mb-md">
                <h3 className="text-lg font-semibold">Notifications</h3>
                <span className="bg-error text-on-error text-[10px] px-1.5 rounded-full font-bold">3</span>
              </div>
              <div className="space-y-md">
                <div className="flex gap-4 p-md bg-error-container rounded-lg border border-error/10">
                  <span className="material-symbols-outlined text-error" style={{ fontVariationSettings: "'FILL' 1" }}>error</span>
                  <div>
                    <p className="text-sm font-bold text-on-error-container">Critical Review Required</p>
                    <p className="text-xs text-on-error-container/80">Scan ID #8921 shows abnormal growth patterns.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
