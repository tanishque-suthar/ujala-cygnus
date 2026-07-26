import { useState } from 'react'

const LUNG_OPACITY_SUPPRESS_ON = new Set(['Consolidation', 'Infiltration', 'Effusion'])

function getFlaggedFindings(scores, opThreshs) {
  if (!scores || !opThreshs) return []

  let flagged = Object.entries(scores).filter(
    ([name, score]) => opThreshs[name] != null && score >= opThreshs[name]
  )

  const loEntry = flagged.find(([name]) => name === 'Lung Opacity')
  if (loEntry) {
    const hasMoreSpecific = flagged.some(
      ([name]) => LUNG_OPACITY_SUPPRESS_ON.has(name)
    )
    if (hasMoreSpecific) {
      flagged = flagged.filter(([name]) => name !== 'Lung Opacity')
    } else {
      flagged = flagged.map(([name, score]) =>
        name === 'Lung Opacity' ? ['General Opacity (nonspecific)', score] : [name, score]
      )
    }
  }

  return flagged.sort(([, a], [, b]) => b - a)
}

function FlaggedFindings({ findings }) {
  if (findings.length === 0) {
    return (
      <div className="flex items-center gap-sm text-on-surface-variant">
        <span className="material-symbols-outlined text-[18px]">check_circle</span>
        <span className="text-sm font-medium">No findings above threshold</span>
      </div>
    )
  }

  return (
    <div className="space-y-sm">
      <span className="text-xs text-secondary uppercase tracking-widest">Flagged Findings</span>
      <div className="flex flex-wrap gap-sm">
        {findings.map(([name]) => (
          <span
            key={name}
            className="text-xs font-medium px-sm py-0.5 rounded-full bg-error-container text-on-error-container border border-error/30"
          >
            {name}
          </span>
        ))}
      </div>
    </div>
  )
}

function PathologyBar({ name, score }) {
  const pct = (score * 100).toFixed(1)
  return (
    <div className="flex items-center gap-md">
      <span className="text-xs text-on-surface-variant w-[180px] shrink-0 truncate" title={name}>{name}</span>
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

  const flagged = getFlaggedFindings(scores, opThreshs)
  const allSorted = Object.entries(scores).sort(([, a], [, b]) => b - a)

  return (
    <div className="space-y-md">
      <FlaggedFindings findings={flagged} />

      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-primary hover:text-primary-container flex items-center gap-xs transition-colors"
      >
        <span className="material-symbols-outlined text-[16px]" style={{ transform: expanded ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }}>expand_more</span>
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
