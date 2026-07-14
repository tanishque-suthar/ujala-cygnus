import Sidebar from './Sidebar'
import Header from './Header'

export default function MainLayout({ children }) {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <Header />
      <main className="ml-[260px] pt-16 min-h-screen p-margin">
        {children}
      </main>
    </div>
  )
}
