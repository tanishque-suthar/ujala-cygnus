import MainLayout from '../components/MainLayout'

const historyData = [
  { date: 'Oct 24, 2023', cat: 'Blood Test', doc: 'Dr. Arpit Sharma', status: 'Final' },
  { date: 'Oct 21, 2023', cat: 'MRI Scan', doc: 'Dr. Neha Kapoor', status: 'Draft' },
]

export default function PatientHistory() {
  return (
    <MainLayout>
      <div className="mb-xl">
        <h2 className="text-2xl font-bold">Patient History</h2>
        <p className="text-on-surface-variant">Complete chronological record of medical interactions.</p>
      </div>
      <div className="bg-white border border-outline-variant rounded-xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-primary text-on-primary">
            <tr>
              <th className="px-lg py-4">Date</th>
              <th className="px-lg py-4">Category</th>
              <th className="px-lg py-4">Provider</th>
              <th className="px-lg py-4">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-outline-variant">
            {historyData.map((row, i) => (
              <tr key={i} className="hover:bg-surface-container transition-colors">
                <td className="px-lg py-4">{row.date}</td>
                <td className="px-lg py-4">{row.cat}</td>
                <td className="px-lg py-4">{row.doc}</td>
                <td className="px-lg py-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${row.status === 'Final' ? 'bg-tertiary-container text-on-tertiary-container' : 'bg-secondary-container'}`}>
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </MainLayout>
  )
}
