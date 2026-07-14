import MainLayout from '../components/MainLayout'

export default function LabResults() {
  return (
    <MainLayout>
      <div className="max-w-[1200px] mx-auto">
        <div className="bg-white border border-outline-variant rounded p-lg mb-lg flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold">Complete Blood Count (CBC)</h2>
            <p className="text-on-surface-variant">Patient: Maria Santos | ID: UCP-8812</p>
          </div>
          <button className="bg-primary text-on-primary px-4 py-2 rounded">Download PDF</button>
        </div>
        <div className="bg-white border border-outline-variant rounded overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-surface-container-low text-secondary uppercase text-xs">
              <tr>
                <th className="px-lg py-4">Component</th>
                <th className="px-lg py-4">Result</th>
                <th className="px-lg py-4">Flag</th>
                <th className="px-lg py-4">Reference Range</th>
              </tr>
            </thead>
            <tbody className="text-sm divide-y divide-outline-variant">
              <tr>
                <td className="px-lg py-4 font-bold">White Blood Cell Count</td>
                <td className="px-lg py-4">6.4</td>
                <td className="px-lg py-4">
                  <span className="bg-tertiary-fixed px-2 py-0.5 rounded text-[10px] font-bold">NORMAL</span>
                </td>
                <td className="px-lg py-4">4.5 - 11.0</td>
              </tr>
              <tr className="bg-error/5">
                <td className="px-lg py-4 font-bold">Red Blood Cell Count</td>
                <td className="px-lg py-4">4.12</td>
                <td className="px-lg py-4">
                  <span className="bg-error-container text-error px-2 py-0.5 rounded text-[10px] font-bold">LOW</span>
                </td>
                <td className="px-lg py-4">4.20 - 5.40</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </MainLayout>
  )
}
