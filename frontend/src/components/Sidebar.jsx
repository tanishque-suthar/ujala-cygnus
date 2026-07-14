import { Link, useNavigate, useLocation } from 'react-router-dom'

const menuItems = [
  { path: '/', label: 'Dashboard', icon: 'dashboard' },
  { path: '/records', label: 'Records', icon: 'folder_open' },
  { path: '/history', label: 'History', icon: 'history' },
  { path: '/settings', label: 'Settings', icon: 'settings' },
]

export default function Sidebar() {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <aside className="w-[260px] h-screen fixed left-0 top-0 bg-surface dark:bg-surface-dim border-r border-outline-variant dark:border-outline flex flex-col py-lg z-50">
      <div className="px-margin mb-xl">
        <h1 className="font-sans text-xl font-bold text-primary dark:text-primary-fixed-dim">Ujala Cygnus</h1>
        <p className="font-sans text-xs text-on-surface-variant">Medical Portal</p>
      </div>
      <nav className="flex-1 space-y-1">
        {menuItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            className={`flex items-center px-margin py-3 border-l-2 transition-colors cursor-pointer active:scale-95 ${
              location.pathname === item.path
                ? 'border-primary bg-surface-container-low text-primary font-semibold'
                : 'border-transparent text-on-surface-variant hover:text-on-surface hover:bg-surface-container-high'
            }`}
          >
            <span className="material-symbols-outlined mr-3">{item.icon}</span>
            <span className="text-sm">{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="px-margin mt-auto">
        <button
          onClick={() => navigate('/upload-selector')}
          className="w-full bg-primary text-on-primary py-3 px-4 rounded flex items-center justify-center font-semibold text-sm hover:opacity-90 transition-all active:scale-95"
        >
          <span className="material-symbols-outlined mr-2">cloud_upload</span>
          Upload
        </button>
      </div>
    </aside>
  )
}
