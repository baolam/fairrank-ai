import { useState } from 'react'
import { useRankingStore } from '../../store/useRankingStore'
import { RankingResultsView } from '../RankingResultsView'
import { ParetoFrontierTab } from '../tabs/ParetoFrontierTab'
import { CounterfactualTab } from '../tabs/CounterfactualTab'
import { ComplianceReportTab } from '../tabs/ComplianceReportTab'

const VIEWS = [
  { id: 'ranking', label: 'Kết quả Ranking' },
  { id: 'pareto', label: 'Pareto Frontier' },
  { id: 'counterfactual', label: 'Counterfactual Audit' },
  { id: 'report', label: 'Compliance Report' },
] as const

export function ResultsCompareStep() {
  const lastRun = useRankingStore((s) => s.lastRun)
  const setStep = useRankingStore((s) => s.setStep)
  const restartAtStep1 = useRankingStore((s) => s.restartAtStep1)
  const [view, setView] = useState<(typeof VIEWS)[number]['id']>('ranking')

  if (!lastRun) {
    return null
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-fr-ink">Bước 3 · Kết quả &amp; so sánh</h2>
          <p className="mt-1 text-sm text-fr-ink-soft">
            So sánh hiệu suất xếp hạng, đánh đổi công bằng/tiện ích, và kiểm chứng thiên lệch nhân khẩu học.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-md border border-fr-line px-3 py-1.5 text-sm font-medium text-fr-ink-soft hover:border-fr-teal hover:text-fr-teal transition-colors"
            onClick={() => setStep(2)}
          >
            ← Chạy cấu hình khác
          </button>
          <button
            type="button"
            className="rounded-md border border-fr-line px-3 py-1.5 text-sm font-medium text-fr-ink-soft hover:border-fr-teal hover:text-fr-teal transition-colors"
            onClick={restartAtStep1}
          >
            Chạy lại từ đầu
          </button>
        </div>
      </div>

      <nav className="flex flex-wrap gap-5 border-b border-fr-line">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            type="button"
            onClick={() => setView(v.id)}
            className={`-mb-px border-b-2 px-0.5 py-2.5 text-sm font-medium transition-colors ${
              view === v.id ? 'border-fr-teal text-fr-teal' : 'border-transparent text-fr-ink-soft hover:text-fr-ink'
            }`}
          >
            {v.label}
          </button>
        ))}
      </nav>

      <div>
        {view === 'ranking' && (
          <RankingResultsView ranking={lastRun.ranking} cutoffK={lastRun.cutoffK} lambdaVal={lastRun.lambdaVal} />
        )}
        {view === 'pareto' && <ParetoFrontierTab />}
        {view === 'counterfactual' && <CounterfactualTab />}
        {view === 'report' && <ComplianceReportTab />}
      </div>
    </div>
  )
}
