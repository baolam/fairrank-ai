import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { listJobs, parseResumeFile, submitApplication } from '../lib/apiClient'
import type { JobPosting, ParsedResume } from '../types/api'
import { GROUP_LABELS, INTERSECTIONAL_GROUPS } from '../types/api'
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

const STAGE_STEP_MS = 400

export function CandidateApplyPage() {
  const [jobs, setJobs] = useState<JobPosting[]>([])
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
      const result = await submitApplication(selectedJob.id, confirmedName.trim(), declaredGroup || null, file)
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
    setShowRedacted(false)
    setProcessError(null)
    setSubmitError(null)
    setConfirmation(null)
  }

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-10">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">📝 Nộp hồ sơ ứng tuyển</h1>
          <Link to="/" className="text-sm font-medium text-brand-700 underline">
            ← Về trang chủ
          </Link>
        </div>

        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          {phase === 'done' && confirmation ? (
            <div className="space-y-3 text-center">
              <div className="text-4xl">✅</div>
              <h2 className="text-lg font-semibold text-gray-900">Nộp hồ sơ thành công!</h2>
              <p className="text-sm text-gray-600">
                Bạn đã ứng tuyển vào <strong>{confirmation.jobTitle}</strong>.
              </p>
              <p className="text-xs text-gray-400">Mã ứng tuyển: {confirmation.id}</p>
              <button
                type="button"
                className="mt-4 rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
                onClick={resetAll}
              >
                Nộp hồ sơ khác
              </button>
            </div>
          ) : phase === 'processing' ? (
            <div className="space-y-5">
              <h2 className="text-lg font-semibold text-gray-900">⏳ Đang xử lý CV…</h2>
              <PipelineDiagram
                stages={PROCESSING_STAGES}
                statuses={PROCESSING_STAGES.map((_, idx) => getStageStatus(idx))}
              />
            </div>
          ) : phase === 'review' && parsed ? (
            <div className="space-y-5">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">🔎 Xác nhận thông tin trích xuất</h2>
                <p className="text-sm text-gray-500">
                  Kiểm tra lại thông tin hệ thống nhận diện được từ CV trước khi nộp chính thức.
                </p>
              </div>

              <label className="block text-sm font-medium text-gray-700">
                Họ và tên (có thể sửa nếu nhận diện sai)
                <input
                  className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                  value={confirmedName}
                  onChange={(e) => setConfirmedName(e.target.value)}
                />
              </label>

              <div className="text-sm text-gray-700">
                <strong>Kỹ năng nhận diện được:</strong>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {parsed.skills.length > 0 ? (
                    parsed.skills.map((s) => (
                      <span key={s} className="rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-gray-400">Không nhận diện được kỹ năng cụ thể.</span>
                  )}
                </div>
              </div>

              <p className="text-sm text-gray-700">
                <strong>Số năm kinh nghiệm:</strong>{' '}
                {parsed.years_of_experience != null ? `${parsed.years_of_experience} năm` : 'Không xác định'}
              </p>

              {parsed.detected_sensitive_entities.length > 0 && (
                <p className="rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-800">
                  🛡️ Các mục sau sẽ được ẩn danh khi chấm điểm công bằng:{' '}
                  {parsed.detected_sensitive_entities.join(', ')}
                </p>
              )}

              <div>
                <button
                  type="button"
                  className="text-sm font-medium text-brand-700 underline"
                  onClick={() => setShowRedacted((v) => !v)}
                >
                  {showRedacted ? 'Ẩn' : 'Xem'} bản đã ẩn danh (redacted)
                </button>
                {showRedacted && (
                  <pre className="mt-2 max-h-48 overflow-y-auto whitespace-pre-wrap rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-700">
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
                  className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting ? 'Đang nộp…' : '✅ Xác nhận & Nộp hồ sơ'}
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-5">
              {loadingJobs && <p className="text-sm text-gray-500">Đang tải danh sách job…</p>}
              {jobsError && <p className="text-sm text-red-600">{jobsError}</p>}

              {!loadingJobs && jobs.length === 0 && (
                <p className="rounded-lg bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
                  Hiện chưa có job nào đang mở. Vui lòng đợi Nhà tuyển dụng tạo job posting.
                </p>
              )}

              {jobs.length > 0 && (
                <>
                  <label className="block text-sm font-medium text-gray-700">
                    Chọn job muốn ứng tuyển
                    <select
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      value={selectedJobId}
                      onChange={(e) => setSelectedJobId(e.target.value)}
                    >
                      {jobs.map((j) => (
                        <option key={j.id} value={j.id}>
                          {j.title}
                        </option>
                      ))}
                    </select>
                  </label>

                  {selectedJob && (
                    <div className="rounded-lg bg-gray-50 p-3 text-sm text-gray-600">
                      <p className="whitespace-pre-wrap">{selectedJob.description}</p>
                    </div>
                  )}

                  <label className="block text-sm font-medium text-gray-700">
                    Nhóm nhân khẩu học (phục vụ audit công bằng — tuỳ chọn, tách biệt khỏi CV)
                    <select
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                      value={declaredGroup}
                      onChange={(e) => setDeclaredGroup(e.target.value)}
                    >
                      <option value="">Không khai báo</option>
                      {INTERSECTIONAL_GROUPS.map((g) => (
                        <option key={g} value={g}>
                          {GROUP_LABELS[g]}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="block text-sm font-medium text-gray-700">
                    Upload CV (.pdf, .docx, .txt — tối đa 10MB)
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt,.md"
                      onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
                      className="mt-1 block w-full text-sm text-gray-600"
                    />
                  </label>

                  {fileError && <p className="text-sm text-red-600">{fileError}</p>}
                  {processError && <p className="text-sm text-red-600">{processError}</p>}

                  <button
                    type="button"
                    disabled={!file}
                    onClick={handleProcess}
                    className="w-full rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    🔬 Xử lý CV →
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
