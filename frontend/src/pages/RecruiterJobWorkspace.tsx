import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getJob, listApplications, updateApplicationStage, getJobAnalytics, exportHtmlReport, runFairScreening, advanceTopCandidates } from '../lib/apiClient'
import { useAuthStore } from '../store/useAuthStore'
import { useRankingStore } from '../store/useRankingStore'
import { ConfigureRunStep } from '../components/steps/ConfigureRunStep'
import { ResultsCompareStep } from '../components/steps/ResultsCompareStep'
import { CandidateDetailDrawer } from '../components/ats/CandidateDetailDrawer'
import { JobAICriteriaEditor } from '../components/ats/JobAICriteriaEditor'
import { JobSettingsModal } from '../components/ats/JobSettingsModal'
import type { ApplicationStage, CandidateApplicationFull, JobFunnelAnalytics, JobPostingFull } from '../types/ats'
import { ATS_STAGES } from '../types/ats'
import { SAMPLE_CANDIDATES } from '../data/sampleCandidates'
import type { CandidateRecord, RelevanceGrade } from '../types/api'

type WorkspaceTab = 'kanban' | 'criteria' | 'audit' | 'analytics'

export function RecruiterJobWorkspace() {
  const { jobId } = useParams<{ jobId: string }>()
  const logout = useAuthStore((s) => s.logout)

  const [job, setJob] = useState<JobPostingFull | null>(null)
  const [applications, setApplications] = useState<CandidateApplicationFull[]>([])
  const [analytics, setAnalytics] = useState<JobFunnelAnalytics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [jobSettingsOpen, setJobSettingsOpen] = useState(false)

  // Tab state
  const [activeTab, setActiveTab] = useState<WorkspaceTab>('kanban')

  // Selected candidate for drawer
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateApplicationFull | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [selectedAppIds, setSelectedAppIds] = useState<Set<string>>(new Set())
  const [expandedAdverseGroup, setExpandedAdverseGroup] = useState<string | null>(null)

  const PASSED_STAGES = new Set(['shortlisted', 'interviewing', 'offered', 'hired'])

  const autoThreshold = job?.ai_criteria?.auto_advance_threshold ?? 70.0
  function isProfileSatisfied(app: CandidateApplicationFull): boolean {
    const scoreOk = (app.ai_score ?? 0) >= autoThreshold
    const noMissing = !app.missing_skills || app.missing_skills.length === 0
    return scoreOk && noMissing
  }

  // Ranking Store bindings for Tab 2 (AI Screening & Audit)
  const setCandidatesPool = useRankingStore((s) => s.setCandidatesPool)
  const startJobWorkflow = useRankingStore((s) => s.startJobWorkflow)
  const step = useRankingStore((s) => s.step)
  const setStep = useRankingStore((s) => s.setStep)
  const lastRun = useRankingStore((s) => s.lastRun)

  function syncCandidatesPool(apps: CandidateApplicationFull[]) {
    if (!apps || apps.length === 0) {
      setCandidatesPool(SAMPLE_CANDIDATES)
    } else {
      const mapped: CandidateRecord[] = apps.map((app) => ({
        id: app.id,
        name: app.candidate_name,
        group: (app.declared_group || 'White_male') as any,
        relevance_grade: (app.ai_score && app.ai_score > 75 ? 2 : app.ai_score && app.ai_score > 40 ? 1 : 0) as RelevanceGrade,
        resume: app.resume_raw_text,
        redacted_text: app.resume_redacted_text,
        skills: app.skills,
        years_of_experience: app.years_of_experience,
      }))
      setCandidatesPool(mapped)
    }
  }

  function refreshAnalytics() {
    if (!jobId) return
    getJobAnalytics(jobId)
      .then(setAnalytics)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được báo cáo phễu tuyển dụng.'))
  }

  function refresh() {
    if (!jobId) return
    setLoading(true)
    setError(null)
    Promise.allSettled([getJob(jobId), listApplications(jobId), getJobAnalytics(jobId)])
      .then(([jobResult, appsResult, analyticsResult]) => {
        const failures: string[] = []

        if (jobResult.status === 'fulfilled') {
          setJob(jobResult.value)
          startJobWorkflow(jobResult.value.title, jobResult.value.description)
        } else {
          failures.push('thông tin job')
        }

        if (appsResult.status === 'fulfilled') {
          setApplications(appsResult.value)
          syncCandidatesPool(appsResult.value)
        } else {
          failures.push('danh sách ứng viên')
        }

        if (analyticsResult.status === 'fulfilled') {
          setAnalytics(analyticsResult.value)
        } else {
          failures.push('báo cáo phễu tuyển dụng & 4/5ths Rule')
        }

        if (failures.length > 0) {
          setError(`Không tải được: ${failures.join(', ')}. Các phần dữ liệu khác đã được cập nhật — bấm "Làm mới" để thử lại.`)
        }

        if (step <= 1) setStep(2)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId])

  async function handleQuickStageMove(appId: string, newStage: ApplicationStage, e: React.MouseEvent) {
    e.stopPropagation()
    if (!jobId) return
    try {
      await updateApplicationStage(jobId, appId, newStage)
      refresh()
    } catch (err) {
      alert('Không thể chuyển giai đoạn: ' + err)
    }
  }

  function handleOpenCandidate(app: CandidateApplicationFull) {
    setSelectedCandidate(app)
    setDrawerOpen(true)
  }

  const [screeningLoading, setScreeningLoading] = useState(false)
  const [screeningMessage, setScreeningMessage] = useState<string | null>(null)

  async function handleRunFairScreening() {
    if (!jobId) return
    setScreeningLoading(true)
    setScreeningMessage(null)
    try {
      const res = await runFairScreening(jobId, {
        lambda_penalty: 1.0,
        target_stage: 'screening',
        from_stage: 'new',
      })
      setScreeningMessage(res.message)
      refresh()
    } catch (err) {
      alert('Lỗi sàng lọc AI: ' + err)
    } finally {
      setScreeningLoading(false)
    }
  }

  function loadIntoAuditPipeline() {
    if (applications.length === 0) {
      // If no applications, load sample pool
      setCandidatesPool(SAMPLE_CANDIDATES)
    } else {
      const mapped: CandidateRecord[] = applications.map((app) => ({
        id: app.id,
        name: app.candidate_name,
        group: app.declared_group || 'White_male',
        relevance_grade: (app.ai_score && app.ai_score > 75 ? 2 : app.ai_score && app.ai_score > 40 ? 1 : 0) as RelevanceGrade,
        resume: app.resume_raw_text,
        redacted_text: app.resume_redacted_text,
        skills: app.skills,
        years_of_experience: app.years_of_experience,
      }))
      setCandidatesPool(mapped)
    }
    setStep(2)
    setActiveTab('audit')
  }

  async function handleExportReport() {
    if (!job || !lastRun) return
    try {
      const mitigationParts: string[] = []
      if (lastRun.redactionEnabled) mitigationParts.push('Sensitive Redaction')
      if (lastRun.lambdaVal > 0) mitigationParts.push('Fair Reranking (Greedy Exposure)')

      const html = await exportHtmlReport({
        job_title: job.title,
        job_description: job.description,
        model_name: lastRun.modelLabel,
        mitigation_strategy: mitigationParts.length > 0 ? mitigationParts.join(' & ') : 'Baseline Unmitigated',
        lambda_val: lastRun.lambdaVal,
        ranking_summary: lastRun.ranking,
      })
      const blob = new Blob([html], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `FairRank_ATS_Report_${job.id}.html`
      a.click()
    } catch (e) {
      alert('Lỗi xuất báo cáo: ' + e)
    }
  }

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-7xl">
        {/* Workspace Header */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-brand-700">
              <Link to="/recruiter" className="underline hover:text-brand-800">
                ← Bảng điều khiển ATS
              </Link>
              <span>/</span>
              <span className="text-gray-500">{job?.department || 'Engineering'}</span>
            </div>
            <h1 className="mt-1 text-2xl font-bold text-gray-900">{job?.title ?? 'Đang tải…'}</h1>
            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-gray-500">
              <span>📍 {job?.location}</span>
              <span>💼 {job?.employment_type}</span>
              {job?.salary_max ? (
                <span>
                  💰 {job?.salary_min} - {job?.salary_max} {job?.salary_currency}
                </span>
              ) : null}
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 font-semibold text-emerald-800">
                {applications.length} ứng viên đã nộp
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setJobSettingsOpen(true)}
              className="rounded-lg border border-purple-200 bg-purple-50 px-3 py-1.5 text-xs font-semibold text-purple-700 shadow-xs hover:bg-purple-100 flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <span>⚙️</span> Cấu hình Job
            </button>
            <Link
              to={`/apply`}
              target="_blank"
              className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-xs hover:bg-gray-50"
            >
              🔗 Link Cổng Ứng viên (/apply)
            </Link>
            <button
              type="button"
              className="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-600 shadow-xs hover:bg-red-50"
              onClick={logout}
            >
              Đăng xuất
            </button>
          </div>
        </header>

        {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

        {/* Tab Navigation */}
        <div className="mb-6 border-b border-gray-200 bg-white rounded-t-2xl px-6 flex gap-6 text-sm font-medium overflow-x-auto">
          {[
            { id: 'kanban', label: `📋 Quy trình tuyển dụng (Kanban - ${applications.length})` },
            { id: 'criteria', label: '🎯 Tiêu chí AI & Từ khóa' },
            { id: 'audit', label: '🛡️ AI Auto-Screening & Tái xếp hạng công bằng' },
            { id: 'analytics', label: '📊 Phễu tuyển dụng & Giám sát 4/5ths Rule' },
          ].map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => {
                if (t.id === 'audit') {
                  syncCandidatesPool(applications)
                  if (step <= 1) setStep(2)
                }
                setActiveTab(t.id as WorkspaceTab)
              }}
              className={`py-4 border-b-2 transition-colors cursor-pointer ${
                activeTab === t.id
                  ? 'border-brand-600 text-brand-600 font-bold'
                  : 'border-transparent text-gray-500 hover:text-gray-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* =========================================================================
            TAB 1: KANBAN BOARD
        ========================================================================= */}
        {activeTab === 'kanban' && (
          <div className="space-y-4">
            {screeningMessage && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs font-semibold text-emerald-800 flex items-center justify-between shadow-xs">
                <span>{screeningMessage}</span>
                <button
                  type="button"
                  onClick={() => setScreeningMessage(null)}
                  className="text-emerald-600 hover:text-emerald-900 font-bold"
                >
                  ✕
                </button>
              </div>
            )}

            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-gray-500">
                Kéo hoặc bấm vào thẻ ứng viên để mở chi tiết, xem CV, chấm Scorecard, hoặc lên lịch phỏng vấn.
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={screeningLoading}
                  onClick={handleRunFairScreening}
                  className="rounded-lg bg-purple-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-purple-700 transition-colors flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                >
                  {screeningLoading ? '⏳ Đang chạy Sàng lọc AI…' : '⚡ Chạy Fair AI Ranking (Chuyển vào Sàng lọc AI)'}
                </button>
                <button
                  type="button"
                  onClick={loadIntoAuditPipeline}
                  className="rounded-lg border border-purple-300 bg-white px-3 py-2 text-xs font-semibold text-purple-700 hover:bg-purple-50 transition-colors"
                  title="Mở bảng điều khiển tinh chỉnh tham số mô hình"
                >
                  ⚙️ Tinh chỉnh mô hình
                </button>
              </div>
            </div>

            {loading && <p className="text-center py-10 text-sm text-gray-500">Đang tải hồ sơ…</p>}

            {!loading && (
              <div className="flex gap-4 overflow-x-auto pb-6">
                {ATS_STAGES.map((col) => {
                  let columnApps = applications.filter((a) => (a.stage || 'new') === col.id)
                  if (col.id === 'screening') {
                    // Prioritize satisfied profiles (score >= threshold and no missing must-haves) first!
                    columnApps = [...columnApps].sort((a, b) => {
                      const aSat = isProfileSatisfied(a)
                      const bSat = isProfileSatisfied(b)
                      if (aSat && !bSat) return -1
                      if (!aSat && bSat) return 1
                      return (b.ai_score || 0) - (a.ai_score || 0)
                    })
                  }
                  const satisfiedApps = columnApps.filter(isProfileSatisfied)

                  return (
                    <div
                      key={col.id}
                      className={`w-72 shrink-0 rounded-2xl border ${col.color} p-3.5 flex flex-col justify-between min-h-[500px]`}
                    >
                      <div>
                        {/* Column Header */}
                        <div className="flex items-center justify-between mb-2 px-1">
                          <span className="text-xs font-bold text-gray-800 uppercase tracking-wider">{col.label}</span>
                          <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${col.badge}`}>
                            {columnApps.length}
                          </span>
                        </div>

                        {col.id === 'screening' && columnApps.length > 0 && (
                          <div className="mb-3 space-y-1.5">
                            {selectedAppIds.size > 0 ? (
                              <button
                                type="button"
                                onClick={async () => {
                                  if (!jobId) return
                                  await advanceTopCandidates(jobId, {
                                    candidateIds: Array.from(selectedAppIds),
                                    targetStage: 'shortlisted',
                                  })
                                  setSelectedAppIds(new Set())
                                  refresh()
                                }}
                                className="w-full rounded-lg bg-purple-600 py-1.5 px-2 text-xs font-bold text-white shadow-xs hover:bg-purple-700 transition-colors flex items-center justify-center gap-1 cursor-pointer"
                              >
                                <span>⭐</span>
                                <span>Chuyển {selectedAppIds.size} hồ sơ đã chọn sang Chọn lọc</span>
                              </button>
                            ) : satisfiedApps.length > 0 ? (
                              <button
                                type="button"
                                onClick={async () => {
                                  if (!jobId) return
                                  await advanceTopCandidates(jobId, {
                                    candidateIds: satisfiedApps.map((a) => a.id),
                                    targetStage: 'shortlisted',
                                  })
                                  refresh()
                                }}
                                className="w-full rounded-lg bg-amber-500 py-1.5 px-2 text-xs font-bold text-white shadow-xs hover:bg-amber-600 transition-colors flex items-center justify-center gap-1 cursor-pointer"
                                title={`Chuyển ${satisfiedApps.length} hồ sơ đạt chuẩn (≥ ${autoThreshold}%)`}
                              >
                                <span>⭐</span>
                                <span>Chuyển {satisfiedApps.length} hồ sơ đạt chuẩn (≥ {autoThreshold}%)</span>
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={async () => {
                                  if (!jobId) return
                                  await advanceTopCandidates(jobId, 10, 'shortlisted')
                                  refresh()
                                }}
                                className="w-full rounded-lg bg-amber-100 py-1.5 text-xs font-bold text-amber-800 hover:bg-amber-200 transition-colors shadow-2xs"
                              >
                                ⭐ Đưa Top 10 vào Chọn lọc
                              </button>
                            )}
                          </div>
                        )}

                        {/* Cards List */}
                        <div className="space-y-2.5">
                          {columnApps.map((app) => (
                            <div
                              key={app.id}
                              onClick={() => handleOpenCandidate(app)}
                              className={`group cursor-pointer rounded-xl border bg-white p-3.5 shadow-xs transition-all hover:shadow-md ${
                                selectedAppIds.has(app.id)
                                  ? 'border-purple-500 ring-1 ring-purple-500'
                                  : isProfileSatisfied(app)
                                  ? 'border-emerald-300 hover:border-emerald-500'
                                  : 'border-gray-200 hover:border-brand-500'
                              }`}
                            >
                              <div className="flex items-start gap-2.5">
                                <input
                                  type="checkbox"
                                  checked={selectedAppIds.has(app.id)}
                                  onClick={(e) => e.stopPropagation()}
                                  onChange={(e) => {
                                    setSelectedAppIds((prev) => {
                                      const next = new Set(prev)
                                      if (e.target.checked) next.add(app.id)
                                      else next.delete(app.id)
                                      return next
                                    })
                                  }}
                                  className="mt-1 h-3.5 w-3.5 rounded border-gray-300 text-brand-600 focus:ring-brand-500 cursor-pointer"
                                  title="Chọn hồ sơ này để chuyển giai đoạn hàng loạt"
                                />

                                <div className="flex-1">
                                  <div className="flex items-start justify-between gap-1.5">
                                    <div>
                                      <h4 className="text-sm font-bold text-gray-900 group-hover:text-brand-600 transition-colors">
                                        {app.candidate_name}
                                      </h4>
                                      <p className="text-[11px] text-gray-500 mt-0.5">
                                        {app.current_title || 'Ứng viên'} ·{' '}
                                        {app.years_of_experience ? `${app.years_of_experience} năm kn` : 'N/A'}
                                      </p>
                                    </div>

                                    <div className="flex flex-col items-end gap-1">
                                      {app.ai_score !== undefined && app.ai_score > 0 && (
                                        <span className="rounded-md bg-purple-50 border border-purple-200 px-1.5 py-0.5 text-[11px] font-bold text-purple-700">
                                          {app.ai_score}%
                                        </span>
                                      )}
                                      {isProfileSatisfied(app) && (
                                        <span className="rounded bg-emerald-100 px-1.5 py-0.2 text-[9px] font-bold text-emerald-800">
                                          ✓ Đạt chuẩn
                                        </span>
                                      )}
                                    </div>
                                  </div>

                                  {/* Skills & Must-Have Matching */}
                                  {app.skills && app.skills.length > 0 && (
                                    <div className="mt-2.5 flex flex-wrap gap-1">
                                      {app.skills.slice(0, 3).map((s, idx) => (
                                        <span key={idx} className="rounded bg-gray-100 px-1.5 py-0.5 text-[10px] text-gray-600">
                                          {s}
                                        </span>
                                      ))}
                                      {app.skills.length > 3 && (
                                        <span className="text-[10px] text-gray-400">+{app.skills.length - 3}</span>
                                      )}
                                    </div>
                                  )}

                                  {/* Missing Must-Have Warning Badge */}
                                  {app.missing_skills && app.missing_skills.length > 0 ? (
                                    <div className="mt-2 flex items-center gap-1 text-[10px] text-red-600 bg-red-50 border border-red-100 rounded px-1.5 py-0.5 font-semibold">
                                      <span>⚠️ Thiếu:</span>
                                      <span className="truncate max-w-[130px]">{app.missing_skills.slice(0, 2).join(', ')}</span>
                                      {app.missing_skills.length > 2 && <span>+{app.missing_skills.length - 2}</span>}
                                    </div>
                                  ) : app.matched_skills && app.matched_skills.length > 0 ? (
                                    <div className="mt-2 flex items-center gap-1 text-[10px] text-emerald-600 bg-emerald-50 border border-emerald-100 rounded px-1.5 py-0.5 font-semibold">
                                      <span>✓ Đủ kỹ năng bắt buộc</span>
                                    </div>
                                  ) : null}

                                  {/* Rating, View CV & Quick Action */}
                                  <div className="mt-3 pt-2.5 border-t border-gray-100 flex items-center justify-between text-[11px]">
                                    <div className="flex items-center gap-1.5">
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handleOpenCandidate(app)
                                        }}
                                        className="rounded border border-gray-200 bg-gray-50 px-2 py-0.5 text-[10px] font-bold text-gray-700 hover:bg-gray-100 hover:text-brand-600 transition-colors flex items-center gap-1 shadow-2xs cursor-pointer"
                                        title="Bấm để mở chi tiết & xem bản PDF CV ứng viên"
                                      >
                                        <span>📄</span> Xem CV
                                      </button>
                                      {(() => {
                                        const code = typeof window !== 'undefined' ? (sessionStorage.getItem('fairrank_recruiter_code') || 'fairrank-demo') : 'fairrank-demo'
                                        return (
                                          <a
                                            href={`/api/v1/jobs/${jobId}/applications/${app.id}/cv.pdf?code=${encodeURIComponent(code)}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={(e) => e.stopPropagation()}
                                            className="rounded border border-red-200 bg-red-50 px-1.5 py-0.5 text-[10px] font-bold text-red-700 hover:bg-red-100 hover:border-red-300 transition-colors flex items-center gap-0.5 shadow-2xs"
                                            title="Mở trực tiếp file PDF CV trong tab mới"
                                          >
                                            <span>PDF</span> ↗
                                          </a>
                                        )
                                      })()}
                                      <span className="text-amber-500 font-semibold text-[10px]">
                                        {app.overall_rating && app.overall_rating > 0 ? `★ ${app.overall_rating}` : ''}
                                      </span>
                                    </div>

                                    {/* Stage Movers */}
                                    <div className="flex items-center gap-1">
                                      {col.id === 'new' && (
                                        <button
                                          type="button"
                                          title="Chuyển sang Sàng lọc AI"
                                          onClick={(e) => handleQuickStageMove(app.id, 'screening', e)}
                                          className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-purple-600 font-bold"
                                        >
                                          🔍
                                        </button>
                                      )}
                                      {col.id === 'screening' && (
                                        <button
                                          type="button"
                                          title="Chuyển sang Lọt chọn lọc"
                                          onClick={(e) => handleQuickStageMove(app.id, 'shortlisted', e)}
                                          className="rounded bg-amber-50 border border-amber-200 px-1.5 py-0.5 text-[10px] font-bold text-amber-700 hover:bg-amber-100 flex items-center gap-0.5"
                                        >
                                          <span>⭐</span> Chọn lọc
                                        </button>
                                      )}
                                      {(col.id === 'new' || col.id === 'screening') && !isProfileSatisfied(app) && (
                                        <button
                                          type="button"
                                          title="Hồ sơ không phù hợp - Loại ứng viên"
                                          onClick={(e) => handleQuickStageMove(app.id, 'rejected', e)}
                                          className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
                                        >
                                          ❌
                                        </button>
                                      )}
                                      {col.id === 'shortlisted' && (
                                        <button
                                          type="button"
                                          title="Chuyển sang Phỏng vấn"
                                          onClick={(e) => handleQuickStageMove(app.id, 'interviewing', e)}
                                          className="rounded bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 text-[10px] font-bold text-indigo-700 hover:bg-indigo-100 flex items-center gap-0.5"
                                        >
                                          <span>🗓️</span> Phỏng vấn
                                        </button>
                                      )}
                                      {(col.id === 'interviewing' || col.id === 'offered') && (
                                        <>
                                          {col.id === 'interviewing' && (
                                            <button
                                              type="button"
                                              title="Chuyển sang Đã gửi Offer"
                                              onClick={(e) => handleQuickStageMove(app.id, 'offered', e)}
                                              className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-emerald-600"
                                            >
                                              📨
                                            </button>
                                          )}
                                          <button
                                            type="button"
                                            title="Đã tuyển dụng"
                                            onClick={(e) => handleQuickStageMove(app.id, 'hired', e)}
                                            className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-teal-600"
                                          >
                                            🎉
                                          </button>
                                          <button
                                            type="button"
                                            title="Loại ứng viên"
                                            onClick={(e) => handleQuickStageMove(app.id, 'rejected', e)}
                                            className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-600"
                                          >
                                            ❌
                                          </button>
                                        </>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}

                          {columnApps.length === 0 && (
                            col.id === 'screening' ? (
                              <div className="rounded-xl border border-dashed border-purple-300 bg-purple-50/60 p-4 text-center space-y-2">
                                <p className="text-xs font-semibold text-purple-900">
                                  Chưa có ứng viên trong cột Sàng lọc AI
                                </p>
                                <p className="text-[11px] text-purple-700 leading-relaxed">
                                  Bấm nút dưới đây để chạy thuật toán Fair AI Ranking và tự động chuyển các ứng viên Mới nộp sang giai đoạn này.
                                </p>
                                <button
                                  type="button"
                                  disabled={screeningLoading}
                                  onClick={handleRunFairScreening}
                                  className="w-full rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-purple-700 transition-colors disabled:opacity-50"
                                >
                                  {screeningLoading ? '⏳ Đang sàng lọc…' : '⚡ Chạy Fair AI Sàng lọc ngay'}
                                </button>
                              </div>
                            ) : (
                              <div className="rounded-xl border border-dashed border-gray-300 p-6 text-center text-xs text-gray-400">
                                Chưa có hồ sơ
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            TAB: AI CRITERIA & KEYWORDS SETUP
        ========================================================================= */}
        {activeTab === 'criteria' && job && (
          <JobAICriteriaEditor job={job} onCriteriaUpdated={refresh} />
        )}

        {/* =========================================================================
            TAB 2: AI AUTO-SCREENING & FAIR RERANKING
        ========================================================================= */}
        {activeTab === 'audit' && (
          <div className="space-y-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-gray-100">
              <div>
                <h3 className="text-lg font-bold text-gray-900">🛡️ FairRank-AI Scoring & Mitigation Engine</h3>
                <p className="text-xs text-gray-500">
                  Tái xếp hạng công bằng và kiểm toán thiên vị tự động trên tập ứng viên của vị trí {job?.title}.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold cursor-pointer ${
                    step <= 2 ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  ⚙️ Cấu hình mô hình (BM25/SBERT & λ)
                </button>
                <button
                  type="button"
                  disabled={!lastRun}
                  onClick={() => setStep(3)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50 cursor-pointer ${
                    step === 3 ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📊 So sánh kết quả xếp hạng
                </button>
              </div>
            </div>

            {step <= 2 && <ConfigureRunStep />}
            {step === 3 && (
              <div className="space-y-4">
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleExportReport}
                    className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 transition-colors"
                  >
                    📥 Tải Báo cáo Kiểm toán Đạo đức AI (HTML Certificate)
                  </button>
                </div>
                <ResultsCompareStep />
              </div>
            )}
          </div>
        )}

        {/* =========================================================================
            TAB 3: FUNNEL & ADVERSE IMPACT ANALYTICS
        ========================================================================= */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <div className="flex justify-end">
              <button
                type="button"
                onClick={refreshAnalytics}
                className="rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-semibold text-gray-700 shadow-xs hover:bg-gray-50 transition-colors"
              >
                🔄 Làm mới báo cáo
              </button>
            </div>
            {analytics && (
              <>
                {/* Funnel Stage Breakdown */}
                <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                  <h3 className="text-base font-bold text-gray-900 mb-4">📈 Phễu tuyển dụng qua các giai đoạn</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-7 gap-3">
                    {ATS_STAGES.map((s) => {
                      const count = analytics.stage_counts[s.id] || 0
                      const pct = analytics.total_applications > 0
                        ? Math.round((count / analytics.total_applications) * 100)
                        : 0
                      return (
                        <div key={s.id} className="rounded-xl border border-gray-100 bg-gray-50 p-3 text-center">
                          <p className="text-xs font-medium text-gray-500">{s.label}</p>
                          <p className="mt-1 text-xl font-bold text-gray-900">{count}</p>
                          <span className="text-[11px] text-gray-400">{pct}% tổng số</span>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Adverse Impact 4/5ths Rule Monitoring */}
                <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-base font-bold text-gray-900">
                        ⚖️ Báo cáo Giám sát Công bằng: Quy tắc 4/5ths Rule (EEOC Adverse Impact)
                      </h3>
                      <p className="text-xs text-gray-500">
                        Đo lường tỷ lệ trúng tuyển qua vòng Shortlist giữa các nhóm nhân khẩu học. Nếu tỷ lệ &lt; 80% (0.8), hệ thống sẽ kích hoạt cảnh báo Disparate Impact.
                      </p>
                    </div>
                  </div>

                  {analytics.adverse_impact.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead className="bg-gray-50 text-gray-600 font-semibold uppercase tracking-wider">
                          <tr>
                            <th className="p-3">Nhóm nhân khẩu học</th>
                            <th className="p-3 text-center">Tổng nộp</th>
                            <th className="p-3 text-center">Lọt Shortlist+</th>
                            <th className="p-3 text-center">Tỷ lệ chọn lọc (Selection Rate)</th>
                            <th className="p-3 text-center">Adverse Impact Ratio</th>
                            <th className="p-3 text-center">Đánh giá EEOC</th>
                            <th className="p-3 text-center">Hồ sơ</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                          {analytics.adverse_impact.map((row, idx) => (
                            <tr key={idx} className="hover:bg-gray-50/50">
                              <td className="p-3 font-semibold text-gray-800">{row.group}</td>
                              <td className="p-3 text-center text-gray-600">{row.total}</td>
                              <td className="p-3 text-center text-gray-600">{row.passed}</td>
                              <td className="p-3 text-center font-mono font-medium">
                                {(row.selection_rate * 100).toFixed(1)}%
                              </td>
                              <td className="p-3 text-center font-mono font-bold">
                                {row.adverse_impact_ratio.toFixed(2)}
                              </td>
                              <td className="p-3 text-center">
                                {row.is_adverse ? (
                                  <span className="rounded-full bg-red-100 px-2.5 py-1 text-[11px] font-bold text-red-700">
                                    ⚠️ Có dấu hiệu thiên vị (&lt; 0.8)
                                  </span>
                                ) : (
                                  <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-[11px] font-bold text-emerald-700">
                                    ✅ Đạt chuẩn công bằng (≥ 0.8)
                                  </span>
                                )}
                              </td>
                              <td className="p-3 text-center">
                                {row.is_adverse && (
                                  <button
                                    type="button"
                                    onClick={() =>
                                      setExpandedAdverseGroup((prev) => (prev === row.group ? null : row.group))
                                    }
                                    className="rounded-lg border border-red-200 bg-white px-2.5 py-1 text-[11px] font-bold text-red-700 hover:bg-red-50 transition-colors"
                                  >
                                    {expandedAdverseGroup === row.group ? '▲ Ẩn hồ sơ' : '👁️ Xem hồ sơ'}
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">Chưa có đủ dữ liệu nhân khẩu học để tính 4/5ths Rule.</p>
                  )}

                  {/* Flagged Group: Candidate Profiles for Review */}
                  {expandedAdverseGroup && (() => {
                    const flaggedApps = applications.filter(
                      (a) => (a.declared_group || 'Unknown') === expandedAdverseGroup
                    )
                    const notPassed = flaggedApps.filter((a) => !PASSED_STAGES.has(a.stage || 'new'))
                    const passed = flaggedApps.filter((a) => PASSED_STAGES.has(a.stage || 'new'))

                    return (
                      <div className="mt-4 rounded-xl border border-red-200 bg-red-50/40 p-4 space-y-3">
                        <div>
                          <h4 className="text-sm font-bold text-red-900">
                            ⚠️ Hồ sơ thuộc nhóm "{expandedAdverseGroup}" — rà soát dấu hiệu thiên vị
                          </h4>
                          <p className="text-[11px] text-red-700 mt-0.5">
                            {notPassed.length} hồ sơ chưa qua Shortlist (có thể bị bỏ sót) · {passed.length} hồ sơ đã qua Shortlist.
                          </p>
                        </div>

                        {notPassed.length > 0 ? (
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
                            {notPassed.map((app) => {
                              const stageDef = ATS_STAGES.find((s) => s.id === app.stage) || ATS_STAGES[0]
                              return (
                                <div
                                  key={app.id}
                                  onClick={() => handleOpenCandidate(app)}
                                  className="cursor-pointer rounded-xl border border-gray-200 bg-white p-3 shadow-xs hover:border-red-400 hover:shadow-md transition-all"
                                >
                                  <div className="flex items-start justify-between gap-2">
                                    <div>
                                      <p className="text-sm font-bold text-gray-900">{app.candidate_name}</p>
                                      <p className="text-[11px] text-gray-500 mt-0.5">
                                        {app.current_title || 'Ứng viên'} ·{' '}
                                        {app.years_of_experience ? `${app.years_of_experience} năm kn` : 'N/A'}
                                      </p>
                                    </div>
                                    <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold shrink-0 ${stageDef.badge}`}>
                                      {stageDef.label}
                                    </span>
                                  </div>
                                  {app.ai_score !== undefined && app.ai_score > 0 && (
                                    <p className="mt-1.5 text-[11px] text-purple-700 font-semibold">🎯 AI Match: {app.ai_score}%</p>
                                  )}
                                  {app.missing_skills && app.missing_skills.length > 0 && (
                                    <p className="mt-1 text-[10px] text-red-600 truncate">
                                      ⚠️ Thiếu: {app.missing_skills.slice(0, 2).join(', ')}
                                    </p>
                                  )}
                                </div>
                              )
                            })}
                          </div>
                        ) : (
                          <p className="text-xs text-red-700">Mọi hồ sơ của nhóm này đều đã qua Shortlist.</p>
                        )}
                      </div>
                    )
                  })()}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Candidate Detail Slide-Over Drawer */}
      <CandidateDetailDrawer
        candidate={selectedCandidate}
        jobTitle={job?.title || 'Vị trí tuyển dụng'}
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onUpdated={refresh}
      />

      {/* Job Settings Configuration Modal */}
      {job && (
        <JobSettingsModal
          job={job}
          isOpen={jobSettingsOpen}
          onClose={() => setJobSettingsOpen(false)}
          onUpdated={refresh}
        />
      )}
    </div>
  )
}
