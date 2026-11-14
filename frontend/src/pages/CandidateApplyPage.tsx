import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { listJobs, parseResumeFile, submitApplication } from '../lib/apiClient'
import type { ParsedResume } from '../types/api'
import { GROUP_LABELS, INTERSECTIONAL_GROUPS } from '../types/api'
import type { JobPostingFull } from '../types/ats'
import { PipelineDiagram, type PipelineStageDef, type PipelineStageStatus } from '../components/PipelineDiagram'

type Phase = 'select' | 'processing' | 'review' | 'done'

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt', '.md']
const MAX_FILE_BYTES = 10 * 1024 * 1024

const PROCESSING_STAGES: PipelineStageDef[] = [
  {
    id: 'validate',
    icon: '📤',
    label: 'Kiểm tra file',
    detail: 'Xác thực định dạng & dung lượng',
    formula: 'Chấp nhận .pdf .docx .txt · tối đa 10MB',
  },
  {
    id: 'extract',
    icon: '📄',
    label: 'Trích xuất văn bản',
    detail: 'Đọc nội dung từ PDF/DOCX',
    formula: 'pypdf / python-docx → normalize_text()',
  },
  {
    id: 'detect',
    icon: '🧠',
    label: 'Nhận diện thông tin',
    detail: 'Tên, kỹ năng, số năm kinh nghiệm',
    formula: 'regex + tech-skills taxonomy',
  },
  {
    id: 'redact',
    icon: '🛡️',
    label: 'Rà soát thông tin nhạy cảm',
    detail: 'Phát hiện tên/email/SĐT/link cá nhân',
    formula: 'redact_sensitive_information()',
  },
]

const STAGE_STEP_MS = 350

export function CandidateApplyPage() {
  const [jobs, setJobs] = useState<JobPostingFull[]>([])
  const [loadingJobs, setLoadingJobs] = useState(true)
  const [jobsError, setJobsError] = useState<string | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<string>('')
  const [declaredGroup, setDeclaredGroup] = useState<string>('')

  const [phase, setPhase] = useState<Phase>('select')
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [activeStageIndex, setActiveStageIndex] = useState(-1)
  const seqPosRef = useRef(0)

  const [parsed, setParsed] = useState<ParsedResume | null>(null)
  const [confirmedName, setConfirmedName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [currentTitle, setCurrentTitle] = useState('')
  const [candidateLocation, setCandidateLocation] = useState('')
  const [linkedinUrl, setLinkedinUrl] = useState('')
  const [showRedacted, setShowRedacted] = useState(false)
  const [processError, setProcessError] = useState<string | null>(null)

  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [confirmation, setConfirmation] = useState<{ id: string; jobTitle: string } | null>(null)

  useEffect(() => {
    listJobs()
      .then((data) => {
        setJobs(data)
        if (data.length > 0) setSelectedJobId(data[0].id)
      })
      .catch((err) => setJobsError(err instanceof Error ? err.message : 'Không tải được danh sách job.'))
      .finally(() => setLoadingJobs(false))
  }, [])

  const selectedJob = jobs.find((j) => j.id === selectedJobId) ?? null

  function handleFileChange(selected: File | null) {
    setFileError(null)
    if (!selected) {
      setFile(null)
      return
    }
    const ext = `.${selected.name.split('.').pop()?.toLowerCase() ?? ''}`
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setFileError(`Định dạng ${ext} không được hỗ trợ. Chỉ chấp nhận PDF, DOCX, hoặc TXT.`)
      setFile(null)
      return
    }
    if (selected.size > MAX_FILE_BYTES) {
      setFileError(`File quá lớn (${(selected.size / 1_048_576).toFixed(1)}MB). Giới hạn tối đa 10MB.`)
      setFile(null)
      return
    }
    setFile(selected)
  }

  async function handleProcess() {
    if (!file) return
    setPhase('processing')
    setProcessError(null)
    seqPosRef.current = 0
    setActiveStageIndex(0)
    const timer = window.setInterval(() => {
      seqPosRef.current += 1
      if (seqPosRef.current < PROCESSING_STAGES.length) {
        setActiveStageIndex(seqPosRef.current)
      }
    }, STAGE_STEP_MS)

    try {
      const result = await parseResumeFile(file)
      window.clearInterval(timer)
      setParsed(result)
      setConfirmedName(result.predicted_name || '')
      await new Promise((resolve) => setTimeout(resolve, 300))
      setPhase('review')
    } catch (err) {
      window.clearInterval(timer)
      setProcessError(err instanceof Error ? err.message : 'Xử lý CV thất bại, vui lòng thử file khác.')
      setPhase('select')
    }
  }

  function getStageStatus(idx: number): PipelineStageStatus {
    if (phase !== 'processing') return 'pending'
    if (idx < activeStageIndex) return 'done'
    if (idx === activeStageIndex) return 'active'
    return 'pending'
  }

  async function handleConfirmSubmit() {
    if (!selectedJob || !file || !confirmedName.trim()) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const result = await submitApplication(
        selectedJob.id,
        confirmedName.trim(),
        declaredGroup || null,
        file,
        {
          email: email.trim(),
          phone: phone.trim(),
          currentTitle: currentTitle.trim(),
          location: candidateLocation.trim(),
          linkedinUrl: linkedinUrl.trim(),
        },
      )
      setConfirmation({ id: result.id, jobTitle: selectedJob.title })
      setPhase('done')
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Nộp hồ sơ thất bại, vui lòng thử lại.')
    } finally {
      setSubmitting(false)
    }
  }

  function resetAll() {
    setPhase('select')
    setFile(null)
    setFileError(null)
    setParsed(null)
    setConfirmedName('')
    setEmail('')
    setPhone('')
    setCurrentTitle('')
    setCandidateLocation('')
    setLinkedinUrl('')
    setShowRedacted(false)
    setProcessError(null)
    setSubmitError(null)
    setConfirmation(null)
  }

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">📝 Cổng nộp hồ sơ ứng tuyển (Candidate Portal)</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Hệ thống ATS tự động bóc tách kỹ năng và hỗ trợ bảo mật danh tính công bằng (Blind Hiring).
            </p>
          </div>
          <Link to="/" className="text-sm font-medium text-brand-700 underline">
            ← Về trang chủ
          </Link>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          {phase === 'done' && confirmation ? (
            <div className="space-y-4 text-center py-6">
              <div className="text-5xl">🎉</div>
              <h2 className="text-xl font-bold text-gray-900">Nộp hồ sơ thành công!</h2>
              <p className="text-sm text-gray-600 max-w-md mx-auto">
                Hồ sơ của bạn đã được chuyển tới Hệ thống ATS của vị trí <strong>{confirmation.jobTitle}</strong>.
                Hệ thống AI đã tự động phân tích kỹ năng và chuyển tới Hội đồng tuyển dụng.
              </p>
              <div className="inline-block rounded-lg bg-gray-100 px-4 py-2 text-xs font-mono text-gray-700">
                Mã ứng tuyển (Application ID): {confirmation.id}
              </div>
              <div>
                <button
                  type="button"
                  className="mt-4 rounded-xl bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-brand-700"
                  onClick={resetAll}
                >
                  Nộp hồ sơ cho vị trí khác
                </button>
              </div>
            </div>
          ) : phase === 'processing' ? (
            <div className="space-y-6 py-4">
              <h2 className="text-lg font-bold text-gray-900 text-center">⏳ Đang xử lý bóc tách CV qua AI Pipeline…</h2>
              <PipelineDiagram
                stages={PROCESSING_STAGES}
                statuses={PROCESSING_STAGES.map((_, idx) => getStageStatus(idx))}
              />
            </div>
          ) : phase === 'review' && parsed ? (
            <div className="space-y-6">
              <div className="border-b border-gray-100 pb-3">
                <h2 className="text-lg font-bold text-gray-900">🔎 Xác nhận thông tin hồ sơ ứng viên</h2>
                <p className="text-xs text-gray-500">
                  Hệ thống đã tự động trích xuất thông tin từ CV. Bạn có thể kiểm tra và bổ sung thông tin liên hệ.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Họ và tên *</label>
                  <input
                    type="text"
                    required
                    className="w-full rounded-lg border border-gray-300 p-2 text-sm font-medium"
                    value={confirmedName}
                    onChange={(e) => setConfirmedName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Email liên hệ</label>
                  <input
                    type="email"
                    placeholder="candidate@example.com"
                    className="w-full rounded-lg border border-gray-300 p-2 text-sm"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 text-xs">
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Số điện thoại</label>
                  <input
                    type="tel"
                    placeholder="0912-xxx-xxx"
                    className="w-full rounded-lg border border-gray-300 p-2"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Vị trí hiện tại</label>
                  <input
                    type="text"
                    placeholder="VD: Software Developer"
                    className="w-full rounded-lg border border-gray-300 p-2"
                    value={currentTitle}
                    onChange={(e) => setCurrentTitle(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Địa điểm cư trú</label>
                  <input
                    type="text"
                    placeholder="Hà Nội / TP.HCM"
                    className="w-full rounded-lg border border-gray-300 p-2"
                    value={candidateLocation}
                    onChange={(e) => setCandidateLocation(e.target.value)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">LinkedIn / Portfolio URL</label>
                <input
                  type="url"
                  placeholder="https://linkedin.com/in/your-profile"
                  className="w-full rounded-lg border border-gray-300 p-2 text-xs"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                />
              </div>

              {/* Skills Extracted */}
              <div className="rounded-xl border border-gray-100 bg-gray-50 p-4">
                <span className="text-xs font-semibold text-gray-700 block mb-2">
                  Kỹ năng hệ thống tự động bóc tách ({parsed.skills.length}):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {parsed.skills.length > 0 ? (
                    parsed.skills.map((s) => (
                      <span key={s} className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400">Không nhận diện được kỹ năng cụ thể.</span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-3">
                  <strong>Số năm kinh nghiệm ước tính:</strong>{' '}
                  {parsed.years_of_experience != null ? `${parsed.years_of_experience} năm` : 'Không xác định'}
                </p>
              </div>

              <div>
                <button
                  type="button"
                  className="text-xs font-medium text-brand-700 underline"
                  onClick={() => setShowRedacted((v) => !v)}
                >
                  {showRedacted ? 'Ẩn' : 'Xem'} bản nội dung CV đã ẩn danh (Blind Screening Preview)
                </button>
                {showRedacted && (
                  <pre className="mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700 font-mono">
                    {parsed.redacted_text}
                  </pre>
                )}
              </div>

              {submitError && <p className="text-sm text-red-600">{submitError}</p>}

              <div className="flex items-center justify-between border-t border-gray-200 pt-4">
                <button
                  type="button"
                  className="text-sm font-medium text-gray-500 hover:text-gray-800"
                  onClick={() => setPhase('select')}
                >
                  ← Chọn file khác
                </button>
                <button
                  type="button"
                  disabled={submitting || !confirmedName.trim()}
                  onClick={handleConfirmSubmit}
                  className="rounded-xl bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting ? 'Đang nộp…' : '✅ Xác nhận & Nộp hồ sơ vào ATS'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {loadingJobs && <p className="text-sm text-gray-500">Đang tải danh sách vị trí tuyển dụng…</p>}
              {jobsError && <p className="text-sm text-red-600">{jobsError}</p>}

              {!loadingJobs && jobs.length === 0 && (
                <div className="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">
                  Hiện chưa có vị trí nào đang mở. Vui lòng quay lại sau!
                </div>
              )}

              {jobs.length > 0 && (
                <>
                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Chọn vị trí bạn muốn ứng tuyển *
                    </label>
                    <select
                      className="w-full rounded-xl border border-gray-300 p-2.5 text-sm font-medium"
                      value={selectedJobId}
                      onChange={(e) => setSelectedJobId(e.target.value)}
                    >
                      {jobs.map((j) => (
                        <option key={j.id} value={j.id}>
                          {j.title} ({j.department || 'Engineering'} · {j.location || 'Hanoi'})
                        </option>
                      ))}
                    </select>
                  </div>

                  {selectedJob && (
                    <div className="rounded-xl border border-gray-100 bg-gray-50 p-4 text-xs space-y-2">
                      <div className="flex flex-wrap gap-4 text-gray-600">
                        <span>📍 Địa điểm: {selectedJob.location || 'Hybrid / Hanoi'}</span>
                        <span>💼 Hình thức: {selectedJob.employment_type || 'Full-time'}</span>
                        {selectedJob.salary_max ? (
                          <span>
                            💰 Lương: {selectedJob.salary_min} - {selectedJob.salary_max} {selectedJob.salary_currency}
                          </span>
                        ) : null}
                      </div>
                      <p className="whitespace-pre-wrap text-gray-700 border-t border-gray-200/60 pt-2 leading-relaxed">
                        {selectedJob.description}
                      </p>
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Nhóm nhân khẩu học (Tùy chọn — phục vụ kiểm toán công bằng và chống thiên vị)
                    </label>
                    <select
                      className="w-full rounded-xl border border-gray-300 p-2 text-xs"
                      value={declaredGroup}
                      onChange={(e) => setDeclaredGroup(e.target.value)}
                    >
                      <option value="">Không khai báo (Giữ ẩn danh hoàn toàn)</option>
                      {INTERSECTIONAL_GROUPS.map((g) => (
                        <option key={g} value={g}>
                          {GROUP_LABELS[g]}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-700 mb-1">
                      Tải lên CV của bạn (.pdf, .docx, .txt — Tối đa 10MB) *
                    </label>
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt,.md"
                      onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
                      className="block w-full text-xs text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-50 file:text-brand-700 hover:file:bg-brand-100"
                    />
                  </div>

                  {fileError && <p className="text-xs text-red-600">{fileError}</p>}
                  {processError && <p className="text-xs text-red-600">{processError}</p>}

                  <button
                    type="button"
                    disabled={!file}
                    onClick={handleProcess}
                    className="w-full rounded-xl bg-brand-600 py-3 text-sm font-semibold text-white shadow-xs hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
                  >
                    🔬 Phân tích & Xử lý CV qua AI →
                  </button>
                </>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
