import { useState } from 'react'
import { parseResumeFiles } from '../../lib/apiClient'
import { useRankingStore } from '../../store/useRankingStore'
import { SAMPLE_CANDIDATES } from '../../data/sampleCandidates'
import type { CandidateRecord } from '../../types/api'
import { INTERSECTIONAL_GROUPS } from '../../types/api'

type CandidateSource = 'sample' | 'upload'

export function UploadDataStep() {
  const jobTitle = useRankingStore((s) => s.jobTitle)
  const jobDescription = useRankingStore((s) => s.jobDescription)
  const candidatesPool = useRankingStore((s) => s.candidatesPool)
  const setJobInputs = useRankingStore((s) => s.setJobInputs)
  const setCandidatesPool = useRankingStore((s) => s.setCandidatesPool)
  const setStep = useRankingStore((s) => s.setStep)

  const [source, setSource] = useState<CandidateSource>('sample')
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  function handleSourceChange(next: CandidateSource) {
    setSource(next)
    if (next === 'sample') {
      setCandidatesPool(SAMPLE_CANDIDATES)
    } else {
      setCandidatesPool([])
    }
  }

  async function handleFileUpload(files: FileList | null) {
    if (!files || files.length === 0) return
    setUploading(true)
    setUploadError(null)
    try {
      const parsed = await parseResumeFiles(Array.from(files))
      const mapped: CandidateRecord[] = parsed.map((p, idx) => ({
        id: `upload_${idx + 1}`,
        name: p.predicted_name || `Candidate ${idx + 1}`,
        group: INTERSECTIONAL_GROUPS[idx % INTERSECTIONAL_GROUPS.length],
        relevance_grade: 1,
        resume: p.raw_text,
        redacted_text: p.redacted_text,
        skills: p.skills,
        years_of_experience: p.years_of_experience,
      }))
      setCandidatesPool(mapped)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to parse uploaded files.')
    } finally {
      setUploading(false)
    }
  }

  const canContinue = candidatesPool.length > 0

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-base font-semibold text-fr-ink">Bước 1 · Upload dữ liệu</h2>
        <p className="mt-1 text-sm text-fr-ink-soft">
          Nhập mô tả công việc (JD) và nạp hồ sơ ứng viên — dùng bộ mẫu kiểm định sẵn hoặc upload file CV thật.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-3">
          <label className="block text-sm font-medium text-fr-ink-soft">
            Target job title
            <input
              className="mt-1 w-full rounded-md border border-fr-line bg-white px-3 py-2 text-sm text-fr-ink focus:border-fr-teal focus:outline-none"
              value={jobTitle}
              onChange={(e) => setJobInputs(e.target.value, jobDescription)}
            />
          </label>
          <label className="block text-sm font-medium text-fr-ink-soft">
            Job description requirements
            <textarea
              className="mt-1 h-44 w-full rounded-md border border-fr-line bg-white px-3 py-2 text-sm text-fr-ink focus:border-fr-teal focus:outline-none"
              value={jobDescription}
              onChange={(e) => setJobInputs(jobTitle, e.target.value)}
            />
          </label>
        </div>

        <div className="space-y-3">
          <div className="flex gap-2 text-sm font-medium">
            <button
              type="button"
              className={`rounded-md border px-3 py-1.5 transition-colors ${source === 'sample' ? 'border-fr-teal bg-fr-teal-soft text-fr-teal' : 'border-fr-line text-fr-ink-soft'}`}
              onClick={() => handleSourceChange('sample')}
            >
              Balanced audit pool (12 synthetic profiles)
            </button>
            <button
              type="button"
              className={`rounded-md border px-3 py-1.5 transition-colors ${source === 'upload' ? 'border-fr-teal bg-fr-teal-soft text-fr-teal' : 'border-fr-line text-fr-ink-soft'}`}
              onClick={() => handleSourceChange('upload')}
            >
              Upload custom files
            </button>
          </div>

          {source === 'sample' ? (
            <p className="rounded-md border border-fr-line bg-white px-3 py-2 text-sm text-fr-ink-soft">
              Đã nạp <span className="fr-mono text-fr-ink">{SAMPLE_CANDIDATES.length}</span> hồ sơ kiểm định trên 4
              nhóm nhân khẩu học giao nhau.
            </p>
          ) : (
            <div className="space-y-2">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="block w-full text-sm text-fr-ink-soft"
              />
              {uploading && <p className="text-sm text-fr-ink-soft">Đang phân tích CV đã upload…</p>}
              {uploadError && <p className="text-sm text-fr-alert">{uploadError}</p>}
              {candidatesPool.length > 0 && !uploading && (
                <p className="rounded-md border border-fr-line bg-white px-3 py-2 text-sm text-fr-ink-soft">
                  Đã phân tích thành công <span className="fr-mono text-fr-ink">{candidatesPool.length}</span> file CV.
                </p>
              )}
              {candidatesPool.length === 0 && !uploading && (
                <p className="rounded-md border border-fr-amber bg-fr-amber-soft px-3 py-2 text-sm text-fr-ink">
                  Vui lòng upload một hoặc nhiều file CV, hoặc chuyển sang Balanced Audit Pool.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end border-t border-fr-line pt-4">
        <button
          type="button"
          disabled={!canContinue}
          onClick={() => setStep(2)}
          className="rounded-md bg-fr-teal px-5 py-2.5 text-sm font-medium text-white hover:bg-fr-ink transition-colors disabled:cursor-not-allowed disabled:opacity-40"
        >
          Tiếp tục: Cấu hình &amp; Chạy
        </button>
      </div>
    </div>
  )
}
