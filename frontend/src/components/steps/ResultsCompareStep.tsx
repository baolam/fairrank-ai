import { useState } from 'react'
import { useRankingStore } from '../../store/useRankingStore'
import { RankingResultsView } from '../RankingResultsView'
import { ParetoFrontierTab } from '../tabs/ParetoFrontierTab'
import { CounterfactualTab } from '../tabs/CounterfactualTab'
import { ComplianceReportTab } from '../tabs/ComplianceReportTab'

const VIEWS = [
  { id: 'ranking', label: '📊 Kết quả Ranking' },
  { id: 'pareto', label: '⚖️ Pareto Frontier' },
  { id: 'counterfactual', label: '🔍 Counterfactual Audit' },
  { id: 'report', label: '📑 Compliance Report' },
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
          <h2 className="text-lg font-semibold text-gray-900">📈 Bước 3 · Kết quả &amp; So sánh</h2>
          <p className="text-sm text-gray-500">
            So sánh hiệu suất xếp hạng, đánh đổi công bằng/tiện ích, và kiểm chứng thiên lệch nhân khẩu học.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            onClick={() => setStep(2)}
          >
            ← Chạy cấu hình khác
          </button>
          <button
            type="button"
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            onClick={restartAtStep1}
          >
            🔄 Chạy lại từ đầu
          </button>
        </div>
      </div>

      <nav className="flex flex-wrap gap-2 border-b border-gray-200">
        {VIEWS.map((v) => (
          <button
            key={v.id}
            type="button"
            onClick={() => setView(v.id)}
            className={`rounded-t-lg px-4 py-2.5 text-sm font-medium transition-colors ${
              view === v.id ? 'border-b-2 border-brand-600 text-brand-700' : 'text-gray-500 hover:text-gray-800'
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
