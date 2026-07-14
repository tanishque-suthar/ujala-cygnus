import { useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'

export default function Records() {
  const navigate = useNavigate()

  return (
    <MainLayout>
      <div className="flex justify-between mb-lg items-center">
        <div className="flex gap-2">
          <button className="bg-primary text-on-primary px-4 py-2 rounded-full text-xs">All Records</button>
          <button className="bg-white border border-outline-variant px-4 py-2 rounded-full text-xs">Radiology</button>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-lg">
        <div
          onClick={() => navigate('/brain-mri')}
          className="bg-white border border-outline-variant rounded-xl p-md cursor-pointer hover:border-primary transition-all group"
        >
          <div className="h-40 rounded-lg bg-surface-container-low mb-md overflow-hidden">
            <img
              className="w-full h-full object-cover group-hover:scale-110 transition-transform"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuASshIZuLiTzifhrlGa_yUyGotGHG3XZXF0AsT0dxMJdL5sv7ZBAdShepTPq5cmCEFGbFvz7PBbv7XAOCj9g4mHHZLoCqziz_gYgABilJTa14At_yIkpfB0mBrvmYdvDAmdhIeyniuABPfBge3CRhaiR_P14WSKV8cMOpeRuH2Lvq8c0ZZfG7Acos4XIH4F9bU8f5kCUqUl2Wr80Wn7abDS8JTCADYG_6idu01YUoD9bEXuTMGpE04t8g"
              alt="Brain MRI scan"
            />
          </div>
          <h4 className="font-semibold truncate">Brain_MRI_Oct24.dcm</h4>
          <p className="text-xs text-on-surface-variant mt-1">Oct 24, 2023</p>
        </div>
        <div
          onClick={() => navigate('/lab-results')}
          className="bg-white border border-outline-variant rounded-xl p-md cursor-pointer hover:border-primary transition-all group"
        >
          <div className="h-40 rounded-lg bg-surface-container-low mb-md flex items-center justify-center">
            <span className="material-symbols-outlined text-outline text-6xl">description</span>
          </div>
          <h4 className="font-semibold truncate">Blood_Work_Final.pdf</h4>
          <p className="text-xs text-on-surface-variant mt-1">Oct 21, 2023</p>
        </div>
      </div>
    </MainLayout>
  )
}
