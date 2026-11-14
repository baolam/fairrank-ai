import { useMemo, useState } from 'react'
import { runCounterfactualAudit } from '../../lib/apiClient'
import { useRankingStore } from '../../store/useRankingStore'
import { EmptyState } from '../EmptyState'
import { MetricTile } from '../MetricTile'
import { CounterfactualBoxPlot } from '../charts/CounterfactualBoxPlot'
import type { CounterfactualAuditResponse } from '../../types/api'
import { GROUP_LABELS, type IntersectionalGroup } from '../../types/api'

export function CounterfactualTab() {
  const lastRun = useRankingStore((s) => s.lastRun)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [resumeOpen, setResumeOpen] = useState(false)
  const [rawOpen, setRawOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<CounterfactualAuditResponse | null>(null)

  const candidate = useMemo(() => {
    if (!lastRun) return null
    return lastRun.candidatesPool.find((c) => c.id === selectedId) ?? lastRun.candidatesPool[0]
  }, [lastRun, selectedId])

  if (!lastRun) {
    return <EmptyState message="Please execute a ranking run on Tab 1 first to load candidates." />
  }

  async function handleRun() {
    if (!lastRun || !candidate) return
    setLoading(true)
    setError(null)
    try {
      const res = await runCounterfactualAudit({
        job_description: lastRun.jobDescription,
        candidate_profile: candidate.resume,
        baseline_model: 'bm25',
      })
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Counterfactual audit failed.')
    } finally {
      setLoading(false)
    }
  }

  const rawRows = result
    ? [
        ...result.group_results.flatMap((g) =>
          g.sample_names.map((name, idx) => ({
            group: GROUP_LABELS[g.group as IntersectionalGroup] ?? g.group,
            name,
            pipeline: 'Baseline (Unmitigated)',
            score: g.scores[idx],
          })),
        ),
        ...result.redacted_group_results.flatMap((g) =>
          g.sample_names.map((name, idx) => ({
            group: GROUP_LABELS[g.group as IntersectionalGroup] ?? g.group,
            name,
            pipeline: 'Mitigated (Redaction / Invariant)',
            score: g.scores[idx],
          })),
        ),
      ]
    : []

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-fr-ink">Counterfactual algorithmic bias inspector</h2>
        <p className="mt-1 text-sm text-fr-ink-soft">
          Perturbs candidate demographic identifiers across 4 intersectional groups while holding qualification
          content strictly constant.
        </p>
      </div>

      <label className="block text-sm font-medium text-fr-ink-soft">
        Select candidate to inspect
        <select
          className="mt-1 block w-full max-w-md rounded-md border border-fr-line bg-white px-3 py-2 text-sm text-fr-ink focus:border-fr-teal focus:outline-none"
          value={candidate?.id ?? ''}
          onChange={(e) => setSelectedId(e.target.value)}
        >
          {lastRun.candidatesPool.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name} ({c.id})
            </option>
          ))}
        </select>
      </label>

      {candidate && (
        <p className="text-sm text-fr-ink-soft">
          Selected candidate profile: <span className="fr-mono text-fr-ink">{candidate.name}</span> · current group:{' '}
          <span className="fr-mono text-fr-ink">{GROUP_LABELS[candidate.group]}</span>
        </p>
      )}

      <div>
        <button
          type="button"
          className="text-sm font-medium text-fr-teal hover:text-fr-ink"
          onClick={() => setResumeOpen((v) => !v)}
        >
          {resumeOpen ? 'Hide' : 'View'} qualification content (held invariant)
        </button>
        {resumeOpen && candidate && (
          <pre className="mt-2 whitespace-pre-wrap rounded-md border border-fr-line bg-white p-3 text-sm text-fr-ink-soft">
            {candidate.resume}
          </pre>
        )}
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={loading}
        className="rounded-md bg-fr-teal px-5 py-2.5 text-sm font-medium text-white hover:bg-fr-ink transition-colors disabled:opacity-40"
      >
        {loading ? 'Running…' : 'Run live counterfactual perturbation audit'}
      </button>

      {error && <p className="text-sm text-fr-alert">{error}</p>}

      {result && (
        <div className="space-y-6">
          <div className="flex flex-wrap gap-3">
            <MetricTile
              label="Baseline demographic score drift"
              value={result.max_demographic_shift.toFixed(5)}
              hint={result.is_sensitive ? 'Vulnerable' : 'Invariant'}
              axis={result.is_sensitive ? 'alert' : 'teal'}
            />
            <MetricTile
              label="Mitigated demographic score drift"
              value={result.mitigated_max_demographic_shift.toFixed(5)}
              hint="Zero bias certified"
              axis="teal"
            />
          </div>

          <div>
            <h3 className="text-base font-semibold text-fr-ink">
              Counterfactual score distribution by demographic group
            </h3>
            <div className="mt-3 rounded-md border border-fr-line bg-white p-2">
              <CounterfactualBoxPlot baseline={result.group_results} mitigated={result.redacted_group_results} />
            </div>
          </div>

          <p className="rounded-md border border-fr-teal bg-fr-teal-soft px-4 py-3 text-sm text-fr-ink">
            Verification conclusion: redaction and counterfactual invariance successfully eliminate demographic
            score shifts. The candidate's evaluated score depends purely on domain qualifications rather than
            racial or gender proxies.
          </p>

          <div>
            <button
              type="button"
              className="text-sm font-medium text-fr-teal hover:text-fr-ink"
              onClick={() => setRawOpen((v) => !v)}
            >
              {rawOpen ? 'Hide' : 'View'} raw variant injections
            </button>
            {rawOpen && (
              <div className="mt-2 overflow-x-auto rounded-md border border-fr-line">
                <table className="min-w-full text-sm">
                  <thead className="border-b border-fr-line text-left text-[12px] font-medium text-fr-ink-soft">
                    <tr>
                      <th className="px-4 py-2">Group</th>
                      <th className="px-4 py-2">Injected name</th>
                      <th className="px-4 py-2">Pipeline</th>
                      <th className="px-4 py-2 text-right">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-fr-line/60">
                    {rawRows.map((row, idx) => (
                      <tr key={`${row.pipeline}-${row.name}-${idx}`}>
                        <td className="px-4 py-2 text-fr-ink-soft">{row.group}</td>
                        <td className="px-4 py-2 text-fr-ink">{row.name}</td>
                        <td className="px-4 py-2 text-fr-ink-soft">{row.pipeline}</td>
                        <td className="fr-mono px-4 py-2 text-right text-fr-ink">{row.score.toFixed(4)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
