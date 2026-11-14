interface MetricTileProps {
  label: string
  value: string
  hint?: string
  axis?: 'teal' | 'amber' | 'alert'
}

const AXIS_RULE: Record<NonNullable<MetricTileProps['axis']>, string> = {
  teal: 'bg-fr-teal',
  amber: 'bg-fr-amber',
  alert: 'bg-fr-alert',
}

export function MetricTile({ label, value, hint, axis = 'teal' }: MetricTileProps) {
  return (
    <div className="min-w-[160px] flex-1 rounded-md border border-fr-line bg-white p-4">
      <div className={`h-[3px] w-8 rounded-full ${AXIS_RULE[axis]}`} aria-hidden />
      <div className="mt-2.5 text-[13px] text-fr-ink-soft">{label}</div>
      <div className="fr-mono mt-1 text-2xl font-medium text-fr-ink">{value}</div>
      {hint && <div className="mt-1 text-xs text-fr-ink-soft">{hint}</div>}
    </div>
  )
}
