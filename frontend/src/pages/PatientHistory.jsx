import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'
import { fetchPatients, fetchPatientDocuments } from '../api/client'

const DOC_TYPE_LABEL = {
  xray: 'Chest X-Ray',
  brain_mri: 'Brain MRI',
  ct: 'Abdominal CT',
  text_report: 'Text Report',
}

export default function PatientHistory() {
  const navigate = useNavigate()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchPatients()
      .then(async (patients) => {
        const allRows = await Promise.all(
          patients.map(async (p) => {
            const docs = await fetchPatientDocuments(p.id)
            return docs.map((d) => ({
              patient_id: p.id,
              patient_name: p.name,
              date: d.uploaded_at,
              category: DOC_TYPE_LABEL[d.document_type] ?? d.document_type,
              filename: d.filename,
            }))
          })
        )
        const flat = allRows
          .flat()
          .sort((a, b) => new Date(b.date) - new Date(a.date))
        setRows(flat)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <MainLayout>
      <div className="mb-xl">
        <h2 className="text-2xl font-bold">Patient History</h2>
        <p className="text-on-surface-variant">Complete chronological record of medical interactions.</p>
      </div>
      <div className="bg-white border border-outline-variant rounded-xl overflow-hidden">
        {loading ? (
          <div className="p-lg text-sm text-on-surface-variant">Loading…</div>
        ) : rows.length === 0 ? (
          <div className="p-lg text-sm text-on-surface-variant">No history yet.</div>
        ) : (
          <table className="w-full text-left">
            <thead className="bg-primary text-on-primary">
              <tr>
                <th className="px-lg py-4">Date</th>
                <th className="px-lg py-4">Patient</th>
                <th className="px-lg py-4">Category</th>
                <th className="px-lg py-4">File</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant">
              {rows.map((row, i) => (
                <tr
                  key={i}
                  className="hover:bg-surface-container transition-colors cursor-pointer"
                  onClick={() => navigate(`/patients/${row.patient_id}`)}
                >
                  <td className="px-lg py-4 text-sm">
                    {new Date(row.date).toLocaleDateString('en-IN', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="px-lg py-4 text-sm">{row.patient_name}</td>
                  <td className="px-lg py-4 text-sm">{row.category}</td>
                  <td className="px-lg py-4 text-sm text-on-surface-variant truncate max-w-[180px]" title={row.filename}>
                    {row.filename}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </MainLayout>
  )
}
