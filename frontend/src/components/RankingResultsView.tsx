import { useState } from 'react'
import type { RankingResponse } from '../types/api'
import { GROUP_LABELS, RELEVANCE_LABELS } from '../types/api'
import { MetricTile } from './MetricTile'
import { GroupExposureBarChart } from './charts/GroupExposureBarChart'

interface RankingResultsViewProps {
  ranking: RankingResponse
  cutoffK: number
  lambdaVal: number
}

export function RankingResultsView({ ranking, cutoffK, lambdaVal }: RankingResultsViewProps) {
  const [showFormulas, setShowFormulas] = useState(false)

  const rawScores = ranking.ranked_candidates.map((r) => r.raw_score)
  const minRaw = Math.min(...rawScores)
  const maxRaw = Math.max(...rawScores)
  const rerankActive = lambdaVal > 0

  function exposureFormula(rank: number) {
    if (rank > cutoffK) return `rank ${rank} > K=${cutoffK} → e = 0`
    const value = 1 / Math.log2(rank + 1)
    return `1/log2(${rank}+1) = ${value.toFixed(4)}`
  }

  function normalizationFormula(raw: number, normalized: number) {
    if (rerankActive) {
      return 'Fair Reranker đang hoạt động → điểm đã là điểm chuẩn hoá dùng làm input tái xếp hạng'
    }
    if (Math.abs(maxRaw - minRaw) < 1e-9) {
      return 'Mọi điểm bằng nhau trong pool → chuẩn hoá = 0'
    }
    return `(${raw.toFixed(3)} − ${minRaw.toFixed(3)}) / (${maxRaw.toFixed(3)} − ${minRaw.toFixed(3)}) = ${normalized.toFixed(3)}`
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-base font-semibold text-gray-900">📊 Ranking Performance & Algorithmic Parity</h3>
        <div className="mt-3 flex flex-wrap gap-3">
          <MetricTile label="Utility (nDCG@10)" value={ranking.ndcg_at_k.toFixed(3)} />
          <MetricTile label="MRR" value={ranking.mrr.toFixed(3)} />
          <MetricTile label="B-W Exp Gap" value={ranking.black_white_exposure_gap.toFixed(4)} />
          <MetricTile label="F-M Exp Gap" value={ranking.female_male_exposure_gap.toFixed(4)} />
          <MetricTile label="Intersectional Excess (H5)" value={ranking.intersectional_excess.toFixed(4)} />
        </div>
      </div>

      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-base font-semibold text-gray-900">📋 Ranked Candidate Allocation</h3>
          <button
            type="button"
            className="text-sm font-medium text-brand-700 underline"
            onClick={() => setShowFormulas((v) => !v)}
          >
            {showFormulas ? 'Ẩn' : '🔬 Hiện'} chi tiết tính toán
          </button>
        </div>
        <div className="mt-3 overflow-x-auto rounded-xl border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Rank</th>
                <th className="px-4 py-2">Candidate Name</th>
                <th className="px-4 py-2">Group</th>
                <th className="px-4 py-2">Relevance Grade</th>
                <th className="px-4 py-2">Score</th>
                <th className="px-4 py-2">Exposure e(k)</th>
                {showFormulas && (
                  <>
                    <th className="px-4 py-2">Cách tính chuẩn hoá</th>
                    <th className="px-4 py-2">Cách tính Exposure</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {ranking.ranked_candidates.map((r) => (
                <tr key={r.candidate_id}>
                  <td className="px-4 py-2">{r.rank}</td>
                  <td className="px-4 py-2">{r.candidate_name}</td>
                  <td className="px-4 py-2">{GROUP_LABELS[r.group as keyof typeof GROUP_LABELS] ?? r.group}</td>
                  <td className="px-4 py-2">{RELEVANCE_LABELS[r.relevance_grade]}</td>
                  <td className="px-4 py-2">{r.raw_score.toFixed(3)}</td>
                  <td className="px-4 py-2">{r.exposure_at_k.toFixed(3)}</td>
                  {showFormulas && (
                    <>
                      <td className="px-4 py-2 font-mono text-xs text-gray-500">
                        {normalizationFormula(r.raw_score, r.normalized_score)}
                      </td>
                      <td className="px-4 py-2 font-mono text-xs text-gray-500">{exposureFormula(r.rank)}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="text-base font-semibold text-gray-900">📈 Group Allocation Breakdown</h3>
        <div className="mt-3 rounded-xl border border-gray-200 bg-white p-2">
          <GroupExposureBarChart summaries={ranking.group_summaries} />
        </div>
      </div>
    </div>
  )
}
