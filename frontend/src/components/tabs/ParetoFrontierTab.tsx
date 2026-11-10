import { useEffect, useMemo, useState } from 'react'
import { computeParetoSweep } from '../../lib/apiClient'
import { useRankingStore } from '../../store/useRankingStore'
import { EmptyState } from '../EmptyState'
import { ParetoScatterChart, type ParetoRow } from '../charts/ParetoScatterChart'

export function ParetoFrontierTab() {
  const lastRun = useRankingStore((s) => s.lastRun)
  const paretoCache = useRankingStore((s) => s.paretoCache)
  const setParetoCache = useRankingStore((s) => s.setParetoCache)

  const [lambdaMax, setLambdaMax] = useState(4)
  const [steps, setSteps] = useState(15)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [tableOpen, setTableOpen] = useState(false)

  async function runSweep() {
    if (!lastRun) return
    setLoading(true)
    setError(null)
    try {
      const points = await computeParetoSweep({
        job_description: lastRun.jobDescription,
        candidates: lastRun.candidatesPool.map((c) => ({
          id: c.id,
          name: c.name,
          text: c.resume,
          group: c.group,
          relevance_grade: c.relevance_grade,
        })),
        lambda_min: 0,
        lambda_max: lambdaMax,
        steps,
        cutoff_k: lastRun.cutoffK,
      })
      setParetoCache(points)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pareto sweep failed.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (lastRun && !paretoCache) {
      void runSweep()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lastRun])

  const rows: ParetoRow[] = useMemo(() => {
    if (!paretoCache || paretoCache.length === 0) return []
    const baseline = paretoCache[0].ndcg_at_k
    return paretoCache.map((p) => ({
      ...p,
      utility_retention: baseline > 0 ? (p.ndcg_at_k / baseline) * 100 : 100,
    }))
  }, [paretoCache])

  const optimal = useMemo(() => {
    if (rows.length === 0) return null
    const safe = rows.filter((r) => r.utility_retention >= 98)
    const pool = safe.length > 0 ? safe : rows
    return [...pool].sort((a, b) => a.black_white_exposure_gap - b.black_white_exposure_gap)[0]
  }, [rows])

  if (!lastRun) {
    return <EmptyState message="Please execute a ranking run on Tab 1 first to initialize the candidate pool and job description." />
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">⚖️ Utility vs. Fairness Pareto Frontier</h2>
        <p className="text-sm text-gray-500">
          Empirical simulation exploring the optimal balance between ranking accuracy (nDCG@10) and demographic parity
          across penalty weights (λ).
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-4">
        <label className="text-sm font-medium text-gray-700">
          Maximum Penalty λ ({lambdaMax.toFixed(1)})
          <input
            type="range"
            min={1}
            max={8}
            step={0.5}
            value={lambdaMax}
            onChange={(e) => setLambdaMax(Number(e.target.value))}
            className="mt-1 block w-40"
          />
        </label>
        <label className="text-sm font-medium text-gray-700">
          Grid Resolution (Steps: {steps})
          <input
            type="range"
            min={5}
            max={25}
            step={5}
            value={steps}
            onChange={(e) => setSteps(Number(e.target.value))}
            className="mt-1 block w-40"
          />
        </label>
        <button
          type="button"
          onClick={runSweep}
          disabled={loading}
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
        >
          {loading ? 'Computing…' : '🔄 Compute Pareto Frontier'}
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {rows.length > 0 && optimal && (
        <>
          <div>
            <h3 className="text-base font-semibold text-gray-900">📈 Interactive Pareto Trade-off Curve</h3>
            <div className="mt-3 rounded-xl border border-gray-200 bg-white p-2">
              <ParetoScatterChart rows={rows} optimal={optimal} />
            </div>
          </div>

          <p className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">
            <strong>Algorithm Recommendation:</strong> Optimal operating parameter is{' '}
            <strong>λ = {optimal.lambda_penalty}</strong>. It preserves{' '}
            <strong>{optimal.utility_retention.toFixed(2)}%</strong> of baseline utility (nDCG@10:{' '}
            {optimal.ndcg_at_k.toFixed(4)}) while reducing the Black-White exposure gap to{' '}
            <strong>{optimal.black_white_exposure_gap.toFixed(4)}</strong>.
          </p>

          <div>
            <button
              type="button"
              className="text-sm font-medium text-brand-700 underline"
              onClick={() => setTableOpen((v) => !v)}
            >
              {tableOpen ? 'Hide' : 'View'} Complete Pareto Evaluation Table
            </button>
            {tableOpen && (
              <div className="mt-2 overflow-x-auto rounded-xl border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-2">λ</th>
                      <th className="px-4 py-2">nDCG@10</th>
                      <th className="px-4 py-2">Utility Retention</th>
                      <th className="px-4 py-2">B-W Gap</th>
                      <th className="px-4 py-2">F-M Gap</th>
                      <th className="px-4 py-2">Intersectional Excess</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rows.map((r) => (
                      <tr key={r.lambda_penalty}>
                        <td className="px-4 py-2">{r.lambda_penalty}</td>
                        <td className="px-4 py-2">{r.ndcg_at_k.toFixed(4)}</td>
                        <td className="px-4 py-2">{r.utility_retention.toFixed(2)}%</td>
                        <td className="px-4 py-2">{r.black_white_exposure_gap.toFixed(4)}</td>
                        <td className="px-4 py-2">{r.female_male_exposure_gap.toFixed(4)}</td>
                        <td className="px-4 py-2">{r.intersectional_excess.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
