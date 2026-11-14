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
        <h3 className="text-base font-semibold text-fr-ink">Ranking performance &amp; algorithmic parity</h3>
        <div className="mt-3 flex flex-wrap gap-3">
          <MetricTile label="Utility (nDCG@10)" value={ranking.ndcg_at_k.toFixed(3)} axis="teal" />
          <MetricTile label="MRR" value={ranking.mrr.toFixed(3)} axis="teal" />
          <MetricTile label="B-W exposure gap" value={ranking.black_white_exposure_gap.toFixed(4)} axis="amber" />
          <MetricTile label="F-M exposure gap" value={ranking.female_male_exposure_gap.toFixed(4)} axis="amber" />
          <MetricTile label="Intersectional excess (H5)" value={ranking.intersectional_excess.toFixed(4)} axis="amber" />
        </div>
      </div>

      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-base font-semibold text-fr-ink">Ranked candidate allocation</h3>
          <button
            type="button"
            className="text-sm font-medium text-fr-teal hover:text-fr-ink"
            onClick={() => setShowFormulas((v) => !v)}
          >
            {showFormulas ? 'Ẩn chi tiết tính toán' : 'Hiện chi tiết tính toán'}
          </button>
        </div>
        <div className="mt-3 overflow-x-auto rounded-md border border-fr-line">
          <table className="min-w-full text-sm">
            <thead className="border-b border-fr-line text-left text-[12px] font-medium text-fr-ink-soft">
              <tr>
                <th className="px-4 py-2">Rank</th>
                <th className="px-4 py-2">Candidate name</th>
                <th className="px-4 py-2">Group</th>
                <th className="px-4 py-2">Relevance grade</th>
                <th className="px-4 py-2 text-right">Score</th>
                <th className="px-4 py-2 text-right">Exposure e(k)</th>
                {showFormulas && (
                  <>
                    <th className="px-4 py-2">Cách tính chuẩn hoá</th>
                    <th className="px-4 py-2">Cách tính Exposure</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-fr-line/60">
              {ranking.ranked_candidates.map((r) => (
                <tr key={r.candidate_id}>
                  <td className="fr-mono px-4 py-2 text-fr-ink-soft">{r.rank}</td>
                  <td className="px-4 py-2 text-fr-ink">{r.candidate_name}</td>
                  <td className="px-4 py-2 text-fr-ink-soft">{GROUP_LABELS[r.group as keyof typeof GROUP_LABELS] ?? r.group}</td>
                  <td className="px-4 py-2 text-fr-ink-soft">{RELEVANCE_LABELS[r.relevance_grade]}</td>
                  <td className="fr-mono px-4 py-2 text-right text-fr-ink">{r.raw_score.toFixed(3)}</td>
                  <td className="fr-mono px-4 py-2 text-right text-fr-ink">{r.exposure_at_k.toFixed(3)}</td>
                  {showFormulas && (
                    <>
                      <td className="fr-mono px-4 py-2 text-xs text-fr-ink-soft">
                        {normalizationFormula(r.raw_score, r.normalized_score)}
                      </td>
                      <td className="fr-mono px-4 py-2 text-xs text-fr-ink-soft">{exposureFormula(r.rank)}</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h3 className="text-base font-semibold text-fr-ink">Group allocation breakdown</h3>
        <div className="mt-3 rounded-md border border-fr-line bg-white p-2">
          <GroupExposureBarChart summaries={ranking.group_summaries} />
        </div>
      </div>
    </div>
  )
}
