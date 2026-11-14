export type PipelineStageStatus = 'pending' | 'active' | 'done' | 'skipped'

export interface PipelineStageDef {
  id: string
  icon: string
  label: string
  detail: string
  formula: string
}

interface PipelineDiagramProps {
  stages: PipelineStageDef[]
  statuses: PipelineStageStatus[]
}

const STATUS_STYLES: Record<PipelineStageStatus, string> = {
  pending: 'border-fr-line bg-white',
  active: 'border-fr-teal bg-fr-teal-soft',
  done: 'border-fr-teal bg-white',
  skipped: 'border-fr-line bg-fr-paper opacity-50',
}

const LABEL_STYLES: Record<PipelineStageStatus, string> = {
  pending: 'text-fr-ink-soft',
  active: 'text-fr-teal',
  done: 'text-fr-ink',
  skipped: 'text-fr-ink-soft',
}

export function PipelineDiagram({ stages, statuses }: PipelineDiagramProps) {
  return (
    <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-stretch sm:gap-0">
      {stages.map((stage, idx) => {
        const status = statuses[idx] ?? 'pending'
        return (
          <div key={stage.id} className="flex min-w-0 flex-1 items-center">
            <div
              className={`min-w-0 flex-1 rounded-md border p-3 transition-colors duration-300 ${STATUS_STYLES[status]}`}
            >
              <div className="flex min-w-0 items-center gap-2">
                <span className="fr-mono shrink-0 text-[11px] text-fr-ink-soft">{String(idx + 1).padStart(2, '0')}</span>
                <span
                  className={`min-w-0 truncate text-sm font-medium ${LABEL_STYLES[status]}`}
                  title={stage.label}
                >
                  {stage.label}
                </span>
                {status === 'active' && (
                  <span className="ml-auto h-2 w-2 shrink-0 animate-pulse rounded-full bg-fr-teal" aria-hidden />
                )}
                {status === 'done' && <span className="ml-auto shrink-0 text-fr-teal">✓</span>}
                {status === 'skipped' && <span className="ml-auto shrink-0 text-[11px] text-fr-ink-soft">bỏ qua</span>}
              </div>
              <p className="mt-1.5 truncate text-xs text-fr-ink-soft" title={stage.detail}>
                {stage.detail}
              </p>
              <p className="fr-mono mt-1 truncate text-[11px] text-fr-ink-soft/70" title={stage.formula}>
                {stage.formula}
              </p>
            </div>
            {idx < stages.length - 1 && (
              <span className="mx-1 hidden h-px w-3 shrink-0 bg-fr-line sm:block" aria-hidden />
            )}
          </div>
        )
      })}
    </div>
  )
}
