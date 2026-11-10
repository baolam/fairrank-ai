interface MetricTileProps {
  label: string
  value: string
  hint?: string
}

export function MetricTile({ label, value, hint }: MetricTileProps) {
  return (
    <div className="flex-1 min-w-[160px] rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
        {label}
      </div>
      <div className="mt-1 text-2xl font-semibold text-gray-900">{value}</div>
      {hint && <div className="mt-1 text-xs text-gray-400">{hint}</div>}
    </div>
  )
}
