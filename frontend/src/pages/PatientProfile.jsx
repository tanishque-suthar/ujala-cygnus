import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import MainLayout from '../components/MainLayout'
import PathologyScores from '../components/PathologyScores'
import { fetchPatient, imageUrl, heatmapUrl } from '../api/client'

const DOC_TYPE_LABEL = {
  xray: 'Chest X-Ray',
  brain_mri: 'Brain MRI',
  ct: 'Abdominal CT',
  text_report: 'Text Report',
}

function initials(name) {
  return name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function ImageModal({ doc, onClose }) {
  const hasScan = !!doc.scan_result
  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-lg"
      onClick={onClose}
    >
      <div
        className="bg-surface-container-lowest rounded-2xl overflow-hidden max-w-4xl w-full shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-xl py-lg border-b border-outline-variant flex justify-between items-center">
          <div>
            <p className="font-semibold text-on-surface">{doc.filename}</p>
            <p className="text-xs text-on-surface-variant">{DOC_TYPE_LABEL[doc.document_type] ?? doc.document_type}</p>
          </div>
          <button onClick={onClose} className="text-on-surface-variant hover:text-on-surface transition-colors">
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>
        <div className={`p-xl grid gap-xl ${hasScan ? 'grid-cols-1 md:grid-cols-2' : 'grid-cols-1'}`}>
          <div className="space-y-sm">
            <p className="text-xs text-secondary uppercase tracking-widest">Original Image</p>
            <div className="bg-black rounded-lg overflow-hidden aspect-square">
              <img
                src={imageUrl(doc.id)}
                alt={doc.filename}
                className="w-full h-full object-contain"
              />
            </div>
          </div>
          {hasScan && (
            <div className="space-y-sm">
              <p className="text-xs text-secondary uppercase tracking-widest">Heatmap Overlay</p>
              <div className="bg-black rounded-lg overflow-hidden aspect-square">
                <img
                  src={heatmapUrl(doc.scan_result.id)}
                  alt="Heatmap"
                  className="w-full h-full object-contain"
                />
              </div>
            </div>
          )}
        </div>
        {hasScan && (
          <div className="px-xl pb-xl space-y-md">
            <p className="text-xs text-on-surface-variant">
              Model: <span className="font-semibold text-on-surface">{doc.scan_result.model_used}</span>
            </p>
            <PathologyScores
              scores={doc.scan_result.pathology_scores}
              opThreshs={doc.scan_result.op_threshs}
            />
          </div>
        )}
      </div>
    </div>
  )
}

export default function PatientProfile() {
  const { patientId } = useParams()
  const navigate = useNavigate()
  const [patient, setPatient] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeDoc, setActiveDoc] = useState(null)

  useEffect(() => {
    fetchPatient(patientId)
      .then(setPatient)
      .catch(() => setError('Patient not found.'))
      .finally(() => setLoading(false))
  }, [patientId])

  if (loading) {
    return (
      <MainLayout>
        <div className="p-lg text-sm text-on-surface-variant">Loading…</div>
      </MainLayout>
    )
  }

  if (error || !patient) {
    return (
      <MainLayout>
        <div className="p-lg text-sm text-error">{error ?? 'Unknown error'}</div>
      </MainLayout>
    )
  }

  const sortedDocs = patient.documents
    .slice()
    .sort((a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at))

  return (
    <MainLayout>
      {activeDoc && <ImageModal doc={activeDoc} onClose={() => setActiveDoc(null)} />}

      <div className="max-w-container-max mx-auto space-y-lg">
        <div className="flex items-center gap-md">
          <button
            onClick={() => navigate(-1)}
            className="text-on-surface-variant hover:text-on-surface transition-colors"
          >
            <span className="material-symbols-outlined">arrow_back</span>
          </button>
          <div className="flex items-center gap-md">
            <div className="w-14 h-14 rounded-full bg-secondary-container flex items-center justify-center font-bold text-on-secondary-container text-lg">
              {initials(patient.name)}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-on-background">{patient.name}</h2>
              <p className="text-sm text-on-surface-variant">
                Registered{' '}
                {new Date(patient.created_at).toLocaleDateString('en-IN', {
                  month: 'long',
                  day: 'numeric',
                  year: 'numeric',
                })}
                {' · '}
                {patient.documents.length} document{patient.documents.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>
        </div>

        {sortedDocs.length === 0 ? (
          <div className="bg-white border border-outline-variant rounded-xl p-lg text-sm text-on-surface-variant">
            No documents uploaded for this patient yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-lg">
            {sortedDocs.map((doc) => (
              <div
                key={doc.id}
                onClick={() => setActiveDoc(doc)}
                className="bg-white border border-outline-variant rounded-xl p-md cursor-pointer hover:border-primary transition-all group"
              >
                <div className="h-36 rounded-lg bg-black mb-md overflow-hidden">
                  <img
                    src={imageUrl(doc.id)}
                    alt={doc.filename}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                      e.currentTarget.parentElement.classList.add('flex', 'items-center', 'justify-center')
                      e.currentTarget.parentElement.innerHTML =
                        '<span class="material-symbols-outlined text-outline text-5xl">description</span>'
                    }}
                  />
                </div>
                <h4 className="font-semibold truncate text-sm" title={doc.filename}>
                  {doc.filename}
                </h4>
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
                {doc.scan_result && (
                  <div className="mt-2">
                    <span className="text-xs text-on-surface-variant">
                      Model: {doc.scan_result.model_used}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  )
}
