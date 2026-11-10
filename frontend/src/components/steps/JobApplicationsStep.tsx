import { Fragment, useEffect, useState } from 'react'
import { listApplications } from '../../lib/apiClient'
import { useRankingStore } from '../../store/useRankingStore'
import { SAMPLE_CANDIDATES } from '../../data/sampleCandidates'
import type { ApplicationRecord, CandidateRecord, RelevanceGrade } from '../../types/api'
import { GROUP_LABELS, INTERSECTIONAL_GROUPS } from '../../types/api'

const RELEVANCE_OPTIONS: { value: RelevanceGrade; label: string }[] = [
  { value: 0, label: 'Không phù hợp (No Fit)' },
  { value: 1, label: 'Có thể phù hợp (Potential Fit)' },
  { value: 2, label: 'Rất phù hợp (Good Fit)' },
]

export function JobApplicationsStep({ jobId }: { jobId: string }) {
  const candidatesPool = useRankingStore((s) => s.candidatesPool)
  const setCandidatesPool = useRankingStore((s) => s.setCandidatesPool)
  const setStep = useRankingStore((s) => s.setStep)

  const [applications, setApplications] = useState<ApplicationRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [grades, setGrades] = useState<Record<string, RelevanceGrade>>({})
  const [expandedId, setExpandedId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    listApplications(jobId)
      .then((apps) => {
        if (cancelled) return
        setApplications(apps)
        setGrades((prev) => {
          const next = { ...prev }
          apps.forEach((a) => {
            if (!(a.id in next)) next[a.id] = 1
          })
          return next
        })
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Không tải được danh sách hồ sơ.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [jobId])

  function loadReviewedPool() {
    const mapped: CandidateRecord[] = applications.map((app, idx) => ({
      id: app.id,
      name: app.candidate_name,
      group: app.declared_group ?? INTERSECTIONAL_GROUPS[idx % INTERSECTIONAL_GROUPS.length],
      relevance_grade: grades[app.id] ?? 1,
      resume: app.resume_raw_text,
      redacted_text: app.resume_redacted_text,
      skills: app.skills,
      years_of_experience: app.years_of_experience,
    }))
    setCandidatesPool(mapped)
    setStep(2)
  }

  function loadSamplePool() {
    setCandidatesPool(SAMPLE_CANDIDATES)
    setStep(2)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">📂 Bước 1 · Hồ sơ ứng viên đã nộp</h2>
        <p className="text-sm text-gray-500">
          Xem lại từng hồ sơ thật đã nộp vào job này, gán mức độ phù hợp (nếu muốn), rồi nạp vào pipeline xếp hạng.
        </p>
      </div>

      {loading && <p className="text-sm text-gray-500">Đang tải danh sách hồ sơ…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {!loading && !error && applications.length === 0 && (
        <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 text-sm text-yellow-800">
          💡 Chưa có ứng viên nào nộp hồ sơ vào job này. Hãy chia sẻ link <code>/apply</code> cho người đóng vai Ứng
          viên, hoặc dùng bộ dữ liệu mẫu để demo ngay.
          <div className="mt-3">
            <button
              type="button"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
              onClick={loadSamplePool}
            >
              🧪 Dùng bộ dữ liệu mẫu (12 hồ sơ)
            </button>
          </div>
        </div>
      )}

      {!loading && applications.length > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50 text-left text-xs font-medium uppercase text-gray-500">
                <tr>
                  <th className="px-4 py-2">Ứng viên</th>
                  <th className="px-4 py-2">Nhóm đã khai báo</th>
                  <th className="px-4 py-2">Nộp lúc</th>
                  <th className="px-4 py-2">Đánh giá mức phù hợp</th>
                  <th className="px-4 py-2">CV</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {applications.map((app) => (
                  <Fragment key={app.id}>
                    <tr>
                      <td className="px-4 py-2 font-medium text-gray-900">{app.candidate_name}</td>
                      <td className="px-4 py-2">
                        {app.declared_group ? GROUP_LABELS[app.declared_group] : 'Không khai báo'}
                      </td>
                      <td className="px-4 py-2 text-gray-500">{new Date(app.submitted_at).toLocaleString()}</td>
                      <td className="px-4 py-2">
                        <select
                          className="rounded-lg border border-gray-300 px-2 py-1 text-sm"
                          value={grades[app.id] ?? 1}
                          onChange={(e) =>
                            setGrades((prev) => ({ ...prev, [app.id]: Number(e.target.value) as RelevanceGrade }))
                          }
                        >
                          {RELEVANCE_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {opt.label}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-2">
                        <button
                          type="button"
                          className="text-sm font-medium text-brand-700 underline"
                          onClick={() => setExpandedId((cur) => (cur === app.id ? null : app.id))}
                        >
                          {expandedId === app.id ? 'Ẩn' : 'Xem'}
                        </button>
                      </td>
                    </tr>
                    {expandedId === app.id && (
                      <tr>
                        <td colSpan={5} className="bg-gray-50 px-4 py-3">
                          <pre className="whitespace-pre-wrap text-xs text-gray-700">{app.resume_raw_text}</pre>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between border-t border-gray-200 pt-4">
            <button
              type="button"
              className="text-sm font-medium text-gray-500 hover:text-gray-800"
              onClick={loadSamplePool}
            >
              🧪 Dùng bộ dữ liệu mẫu thay thế
            </button>
            <button
              type="button"
              className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
              onClick={loadReviewedPool}
            >
              Nạp {applications.length} hồ sơ &amp; Tiếp tục →
            </button>
          </div>
        </>
      )}

      {candidatesPool.length > 0 && (
        <p className="text-xs text-gray-400">Pool hiện tại đang có {candidatesPool.length} hồ sơ đã nạp.</p>
      )}
    </div>
  )
}
