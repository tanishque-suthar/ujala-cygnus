import { useState } from 'react'

// These labels are not clinical pathologies and are suppressed from the findings list.
// 'support device' gets its own chip; 'lung opacity' is silently dropped (nonspecific).
const NON_PATHOLOGY_LABELS = new Set(['lung opacity', 'support device'])

function capitalize(str) {
  return str.replace(/(^\w|\s\w)/g, c => c.toUpperCase())
}

function getFlaggedFindings(scores, opThreshs) {
  if (!scores || !opThreshs) return { pathologyFindings: [], supportDeviceDetected: false }

  const flagged = Object.entries(scores).filter(
    ([name, score]) => opThreshs[name] != null && score >= opThreshs[name]
  )

  const supportDeviceDetected = flagged.some(([name]) => name.toLowerCase() === 'support device')
  const pathologyFindings = flagged
    .filter(([name]) => !NON_PATHOLOGY_LABELS.has(name.toLowerCase()))
    .sort(([, a], [, b]) => b - a)

  return { pathologyFindings, supportDeviceDetected }
}

function FlaggedFindings({ pathologyFindings, supportDeviceDetected }) {
  const hasAny = pathologyFindings.length > 0 || supportDeviceDetected

  return (
    <div className="space-y-sm">
      {supportDeviceDetected && (
        <div className="flex flex-wrap gap-sm">
          <span className="text-xs font-medium px-sm py-0.5 rounded-full bg-tertiary-container text-on-tertiary-container border border-tertiary/30 flex items-center gap-xs">
            <span className="material-symbols-outlined text-[14px]">devices</span>
            Support Device Detected
          </span>
        </div>
      )}

      {pathologyFindings.length > 0 && (
        <div className="space-y-sm">
          <span className="text-xs text-secondary uppercase tracking-widest">Flagged Findings</span>
          <div className="flex flex-wrap gap-sm">
            {pathologyFindings.map(([name]) => (
              <span
                key={name}
                className="text-xs font-medium px-sm py-0.5 rounded-full bg-error-container text-on-error-container border border-error/30"
              >
                {capitalize(name)}
              </span>
            ))}
          </div>
        </div>
      )}

      {!hasAny && (
        <div className="flex items-center gap-sm text-on-surface-variant">
          <span className="material-symbols-outlined text-[18px]">check_circle</span>
          <span className="text-sm font-medium">No findings above threshold</span>
        </div>
      )}
    </div>
  )
}

function PathologyBar({ name, score }) {
  const pct = (score * 100).toFixed(1)
  return (
    <div className="flex items-center gap-md">
      <span className="text-xs text-on-surface-variant w-[200px] shrink-0 truncate" title={capitalize(name)}>
        {capitalize(name)}
      </span>
      <div className="flex-1 h-[6px] bg-surface-container-high rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-secondary transition-all duration-500"
          style={{ width: `${Math.max(score * 100, 1)}%` }}
        />
      </div>
      <span className="text-xs font-medium text-on-surface-variant w-[48px] text-right">{pct}%</span>
    </div>
  )
}

export default function PathologyScores({ scores, opThreshs }) {
  const [expanded, setExpanded] = useState(false)
  if (!scores) return null

  const { pathologyFindings, supportDeviceDetected } = getFlaggedFindings(scores, opThreshs)
  const allSorted = Object.entries(scores).sort(([, a], [, b]) => b - a)

  return (
    <div className="space-y-md">
      <FlaggedFindings
        pathologyFindings={pathologyFindings}
        supportDeviceDetected={supportDeviceDetected}
      />

      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-primary hover:text-primary-container flex items-center gap-xs transition-colors"
      >
        <span
          className="material-symbols-outlined text-[16px]"
          style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}
        >
          expand_more
        </span>
        {expanded ? 'Hide' : 'View'} detailed pathology scores
      </button>

      {expanded && (
        <div className="space-y-xs p-md bg-surface-container-low rounded-lg border border-outline-variant animate-[fadeIn_0.2s_ease-out]">
          <p className="text-[11px] text-on-surface-variant italic mb-sm">These are raw model scores, not calibrated probabilities.</p>
          {allSorted.map(([name, score]) => (
            <PathologyBar key={name} name={name} score={score} />
          ))}
        </div>
      )}
    </div>
  )
}
