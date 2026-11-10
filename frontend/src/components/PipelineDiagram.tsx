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
  pending: 'border-gray-200 bg-white',
  active: 'border-brand-600 bg-brand-50 shadow-md scale-[1.02]',
  done: 'border-emerald-300 bg-emerald-50',
  skipped: 'border-gray-200 bg-gray-50 opacity-50',
}

const LABEL_STYLES: Record<PipelineStageStatus, string> = {
  pending: 'text-gray-700',
  active: 'text-brand-700',
  done: 'text-emerald-800',
  skipped: 'text-gray-500',
}

export function PipelineDiagram({ stages, statuses }: PipelineDiagramProps) {
  return (
    <div className="flex min-w-0 flex-col gap-2 sm:flex-row sm:items-stretch sm:gap-0">
      {stages.map((stage, idx) => {
        const status = statuses[idx] ?? 'pending'
        return (
          <div key={stage.id} className="flex min-w-0 flex-1 items-center">
            <div
              className={`min-w-0 flex-1 rounded-xl border p-3 transition-all duration-300 ${STATUS_STYLES[status]}`}
            >
              <div className="flex min-w-0 items-center gap-2">
                <span className="shrink-0 text-lg">{stage.icon}</span>
                <span
                  className={`min-w-0 truncate text-sm font-semibold ${LABEL_STYLES[status]}`}
                  title={stage.label}
                >
                  {stage.label}
                </span>
                {status === 'active' && (
                  <span className="ml-auto h-2 w-2 shrink-0 animate-pulse rounded-full bg-brand-600" aria-hidden />
                )}
                {status === 'done' && <span className="ml-auto shrink-0 text-emerald-600">✓</span>}
                {status === 'skipped' && <span className="ml-auto shrink-0 text-xs text-gray-400">Bỏ qua</span>}
              </div>
              <p className="mt-1 truncate text-xs text-gray-500" title={stage.detail}>
                {stage.detail}
              </p>
              <p className="mt-1 truncate font-mono text-[11px] text-gray-400" title={stage.formula}>
                {stage.formula}
              </p>
            </div>
            {idx < stages.length - 1 && (
              <span className="mx-1 hidden shrink-0 text-gray-300 sm:block" aria-hidden>
                →
              </span>
            )}
          </div>
        )
      })}
    </div>
  )
}
