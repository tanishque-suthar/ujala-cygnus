import { useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <MainLayout>
      <div className="flex flex-col items-center justify-center py-xl">
        <span className="material-symbols-outlined text-6xl text-outline mb-lg">map</span>
        <h2 className="text-2xl font-bold text-on-surface mb-sm">Page Not Found</h2>
        <p className="text-on-surface-variant mb-lg">The page you are looking for does not exist.</p>
        <button onClick={() => navigate('/')} className="bg-primary text-on-primary py-sm px-xl rounded-lg hover:opacity-90 transition-opacity">
          Go to Dashboard
        </button>
      </div>
    </MainLayout>
  )
}