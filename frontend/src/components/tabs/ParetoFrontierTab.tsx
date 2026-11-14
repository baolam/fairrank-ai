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
        <h2 className="text-lg font-semibold text-fr-ink">Utility vs. fairness Pareto frontier</h2>
        <p className="mt-1 text-sm text-fr-ink-soft">
          Empirical simulation exploring the optimal balance between ranking accuracy (nDCG@10) and demographic parity
          across penalty weights (λ).
        </p>
      </div>

      <div className="flex flex-wrap items-end gap-5">
        <label className="text-sm font-medium text-fr-ink-soft">
          Maximum penalty λ (<span className="fr-mono text-fr-amber">{lambdaMax.toFixed(1)}</span>)
          <input
            type="range"
            min={1}
            max={8}
            step={0.5}
            value={lambdaMax}
            onChange={(e) => setLambdaMax(Number(e.target.value))}
            className="mt-1.5 block w-40 accent-fr-amber"
          />
        </label>
        <label className="text-sm font-medium text-fr-ink-soft">
          Grid resolution (steps: <span className="fr-mono text-fr-ink">{steps}</span>)
          <input
            type="range"
            min={5}
            max={25}
            step={5}
            value={steps}
            onChange={(e) => setSteps(Number(e.target.value))}
            className="mt-1.5 block w-40 accent-fr-teal"
          />
        </label>
        <button
          type="button"
          onClick={runSweep}
          disabled={loading}
          className="rounded-md bg-fr-teal px-5 py-2.5 text-sm font-medium text-white hover:bg-fr-ink transition-colors disabled:opacity-40"
        >
          {loading ? 'Computing…' : 'Compute Pareto frontier'}
        </button>
      </div>

      {error && <p className="text-sm text-fr-alert">{error}</p>}

      {rows.length > 0 && optimal && (
        <>
          <div>
            <h3 className="text-base font-semibold text-fr-ink">Interactive Pareto trade-off curve</h3>
            <div className="mt-3 rounded-md border border-fr-line bg-white p-2">
              <ParetoScatterChart rows={rows} optimal={optimal} />
            </div>
          </div>

          <p className="rounded-md border border-fr-teal bg-fr-teal-soft px-4 py-3 text-sm text-fr-ink">
            Algorithm recommendation: optimal operating parameter is{' '}
            <span className="fr-mono text-fr-teal">λ = {optimal.lambda_penalty}</span>. It preserves{' '}
            <span className="fr-mono text-fr-teal">{optimal.utility_retention.toFixed(2)}%</span> of baseline utility
            (nDCG@10: {optimal.ndcg_at_k.toFixed(4)}) while reducing the Black-White exposure gap to{' '}
            <span className="fr-mono text-fr-teal">{optimal.black_white_exposure_gap.toFixed(4)}</span>.
          </p>

          <div>
            <button
              type="button"
              className="text-sm font-medium text-fr-teal hover:text-fr-ink"
              onClick={() => setTableOpen((v) => !v)}
            >
              {tableOpen ? 'Hide' : 'View'} complete Pareto evaluation table
            </button>
            {tableOpen && (
              <div className="mt-2 overflow-x-auto rounded-md border border-fr-line">
                <table className="min-w-full text-sm">
                  <thead className="border-b border-fr-line text-left text-[12px] font-medium text-fr-ink-soft">
                    <tr>
                      <th className="px-4 py-2">λ</th>
                      <th className="px-4 py-2 text-right">nDCG@10</th>
                      <th className="px-4 py-2 text-right">Utility retention</th>
                      <th className="px-4 py-2 text-right">B-W gap</th>
                      <th className="px-4 py-2 text-right">F-M gap</th>
                      <th className="px-4 py-2 text-right">Intersectional excess</th>
                    </tr>
                  </thead>
                  <tbody className="fr-mono divide-y divide-fr-line/60 text-fr-ink">
                    {rows.map((r) => (
                      <tr key={r.lambda_penalty}>
                        <td className="px-4 py-2">{r.lambda_penalty}</td>
                        <td className="px-4 py-2 text-right">{r.ndcg_at_k.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right">{r.utility_retention.toFixed(2)}%</td>
                        <td className="px-4 py-2 text-right">{r.black_white_exposure_gap.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right">{r.female_male_exposure_gap.toFixed(4)}</td>
                        <td className="px-4 py-2 text-right">{r.intersectional_excess.toFixed(4)}</td>
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
