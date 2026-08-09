import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'
import PathologyScores from '../components/PathologyScores'
import { fetchPatients, fetchPatientDocuments, imageUrl } from '../api/client'

const DOC_TYPE_LABEL = {
  xray: 'Chest X-Ray',
  brain_mri: 'Brain MRI',
  ct: 'Abdominal CT',
  text_report: 'Text Report',
}

const DOC_TYPE_ICON = {
  xray: 'radiology',
  brain_mri: 'psychology',
  ct: 'biotech',
  text_report: 'description',
}

export default function Records() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(null)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    fetchPatients()
      .then(async (patients) => {
        const allDocs = await Promise.all(
          patients.map((p) =>
            fetchPatientDocuments(p.id).then((docs) =>
              docs.map((d) => ({ ...d, patient_name: p.name }))
            )
          )
        )
        const flat = allDocs
          .flat()
          .sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at))
        setDocuments(flat)
      })
      .catch(() => setLoadError('Failed to load records'))
      .finally(() => setLoading(false))
  }, [])

  const filtered =
    filter === 'all' ? documents : documents.filter((d) => d.document_type === filter)

  return (
    <MainLayout>
      <div className="flex justify-between mb-lg items-center">
        <div className="flex gap-2 flex-wrap">
          {['all', 'xray', 'brain_mri', 'ct', 'text_report'].map((t) => (
            <button
              key={t}
              onClick={() => setFilter(t)}
              className={`px-4 py-2 rounded-full text-xs transition-colors ${
                filter === t
                  ? 'bg-primary text-on-primary'
                  : 'bg-white border border-outline-variant hover:bg-surface-container'
              }`}
            >
              {t === 'all' ? 'All Records' : DOC_TYPE_LABEL[t] ?? t}
            </button>
          ))}
        </div>
      </div>

      {loadError && (
        <div className="w-full bg-error-container text-on-error-container text-sm px-md py-sm rounded-lg flex items-center gap-sm mb-lg">
          <span className="material-symbols-outlined text-[18px]">error</span>
          {loadError}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-on-surface-variant p-lg">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="text-sm text-on-surface-variant p-lg">
          {filter === 'all'
            ? 'No records yet. Upload a scan to get started.'
            : `No ${DOC_TYPE_LABEL[filter] ?? filter} records found.`}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-lg">
          {filtered.map((doc) => (
            <div
              key={doc.id}
              onClick={() => navigate(`/patients/${doc.patient_id}`)}
              className="bg-white border border-outline-variant rounded-xl p-md cursor-pointer hover:border-primary transition-all group"
            >
              <div className="h-40 rounded-lg bg-black mb-md overflow-hidden">
                <img
                  src={imageUrl(doc.id)}
                  alt={doc.filename}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none'
                    e.currentTarget.parentElement.classList.add('flex', 'items-center', 'justify-center', 'bg-surface-container-low')
                    e.currentTarget.parentElement.innerHTML =
                      `<span class="material-symbols-outlined text-outline text-6xl">${DOC_TYPE_ICON[doc.document_type] ?? 'image'}</span>`
                  }}
                />
              </div>
              <h4 className="font-semibold truncate" title={doc.filename}>{doc.filename}</h4>
              <p className="text-xs text-on-surface-variant mt-1">
                {DOC_TYPE_LABEL[doc.document_type] ?? doc.document_type}
              </p>
              <p className="text-xs text-on-surface-variant">
                {new Date(doc.uploaded_at).toLocaleDateString('en-IN', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric',
                })}
              </p>
              {doc.patient_name && (
                <p className="text-xs text-primary mt-1 truncate">{doc.patient_name}</p>
              )}
              {doc.scan_result && (
                <div className="mt-2">
                  <PathologyScores
                    scores={doc.scan_result.pathology_scores}
                    opThreshs={doc.scan_result.op_threshs}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </MainLayout>
  )
}
