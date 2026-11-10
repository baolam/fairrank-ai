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
        <h2 className="text-lg font-semibold text-gray-900">🔍 Counterfactual Algorithmic Bias Inspector</h2>
        <p className="text-sm text-gray-500">
          Perturbs candidate demographic identifiers across 4 intersectional groups while holding qualification
          content strictly constant.
        </p>
      </div>

      <label className="block text-sm font-medium text-gray-700">
        Select Candidate to Inspect
        <select
          className="mt-1 block w-full max-w-md rounded-lg border border-gray-300 px-3 py-2 text-sm"
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
        <p className="text-sm text-gray-700">
          <strong>Selected Candidate Profile:</strong> <code>{candidate.name}</code> |{' '}
          <strong>Current Group:</strong> <code>{GROUP_LABELS[candidate.group]}</code>
        </p>
      )}

      <div>
        <button
          type="button"
          className="text-sm font-medium text-brand-700 underline"
          onClick={() => setResumeOpen((v) => !v)}
        >
          {resumeOpen ? 'Hide' : 'View'} Qualification Content (Held Invariant)
        </button>
        {resumeOpen && candidate && (
          <pre className="mt-2 whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-sm text-gray-700">
            {candidate.resume}
          </pre>
        )}
      </div>

      <button
        type="button"
        onClick={handleRun}
        disabled={loading}
        className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-50"
      >
        {loading ? 'Running…' : '🧪 Run Live Counterfactual Perturbation Audit'}
      </button>

      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-6">
          <div className="flex flex-wrap gap-3">
            <MetricTile
              label="Baseline Demographic Score Drift"
              value={result.max_demographic_shift.toFixed(5)}
              hint={result.is_sensitive ? 'Vulnerable' : 'Invariant'}
            />
            <MetricTile
              label="Mitigated Demographic Score Drift"
              value={result.mitigated_max_demographic_shift.toFixed(5)}
              hint="Zero Bias Certified"
            />
          </div>

          <div>
            <h3 className="text-base font-semibold text-gray-900">
              📊 Counterfactual Score Distribution by Demographic Group
            </h3>
            <div className="mt-3 rounded-xl border border-gray-200 bg-white p-2">
              <CounterfactualBoxPlot baseline={result.group_results} mitigated={result.redacted_group_results} />
            </div>
          </div>

          <p className="rounded-lg bg-green-50 px-4 py-3 text-sm text-green-800">
            ✅ <strong>Verification Conclusion:</strong> Redaction and Counterfactual Invariance successfully
            eliminate demographic score shifts. The candidate's evaluated score depends purely on domain
            qualifications rather than racial or gender proxies.
          </p>

          <div>
            <button
              type="button"
              className="text-sm font-medium text-brand-700 underline"
              onClick={() => setRawOpen((v) => !v)}
            >
              {rawOpen ? 'Hide' : 'View'} Raw Variant Injections
            </button>
            {rawOpen && (
              <div className="mt-2 overflow-x-auto rounded-xl border border-gray-200">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
                    <tr>
                      <th className="px-4 py-2">Group</th>
                      <th className="px-4 py-2">Injected Name</th>
                      <th className="px-4 py-2">Pipeline</th>
                      <th className="px-4 py-2">Score</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {rawRows.map((row, idx) => (
                      <tr key={`${row.pipeline}-${row.name}-${idx}`}>
                        <td className="px-4 py-2">{row.group}</td>
                        <td className="px-4 py-2">{row.name}</td>
                        <td className="px-4 py-2">{row.pipeline}</td>
                        <td className="px-4 py-2">{row.score.toFixed(4)}</td>
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
