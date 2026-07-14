export default function Header() {
  return (
    <header className="fixed top-0 left-[260px] right-0 h-16 bg-surface dark:bg-surface-dim border-b border-outline-variant dark:border-outline flex justify-between items-center px-margin z-40">
      <div className="flex items-center gap-4 flex-1">
        <div className="relative w-full max-w-md">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
          <input
            className="w-full pl-10 pr-4 py-2 bg-surface-container border border-outline-variant rounded-lg text-sm focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
            placeholder="Search patient ID or records..."
            type="text"
          />
        </div>
      </div>
      <div className="flex items-center gap-margin">
        <div className="flex items-center gap-4 border-r border-outline-variant pr-4">
          <button className="text-on-surface-variant hover:text-primary transition-opacity relative">
            <span className="material-symbols-outlined">notifications</span>
            <span className="absolute top-0 right-0 w-2 h-2 bg-error rounded-full" />
          </button>
          <button className="text-on-surface-variant hover:text-primary transition-opacity">
            <span className="material-symbols-outlined">help_outline</span>
          </button>
        </div>
        <button className="bg-primary text-on-primary px-4 py-2 rounded-lg text-sm font-semibold hover:bg-primary-container transition-all active:scale-95">
          Analyze
        </button>
        <div className="flex items-center gap-3">
          <div className="text-right hidden lg:block">
            <p className="text-sm font-semibold text-on-surface">Dr. Priya Sharma</p>
            <p className="text-xs text-on-surface-variant">Radiology Dept.</p>
          </div>
          <div className="w-10 h-10 rounded-full border border-outline-variant bg-primary-fixed flex items-center justify-center text-primary font-bold text-sm">
            PS
          </div>
        </div>
      </div>
    </header>
  )
}
