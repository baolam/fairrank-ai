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
        <h2 className="text-lg font-semibold text-gray-900">📁 Bước 1 · Upload dữ liệu</h2>
        <p className="text-sm text-gray-500">
          Nhập mô tả công việc (JD) và nạp hồ sơ ứng viên — dùng bộ mẫu kiểm định sẵn hoặc upload file CV thật.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-700">
            Target Job Title
            <input
              className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              value={jobTitle}
              onChange={(e) => setJobInputs(e.target.value, jobDescription)}
            />
          </label>
          <label className="block text-sm font-medium text-gray-700">
            Job Description Requirements
            <textarea
              className="mt-1 h-44 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
              value={jobDescription}
              onChange={(e) => setJobInputs(jobTitle, e.target.value)}
            />
          </label>
        </div>

        <div className="space-y-3">
          <div className="flex gap-2 text-sm font-medium text-gray-700">
            <button
              type="button"
              className={`rounded-full border px-3 py-1.5 ${source === 'sample' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-300 text-gray-600'}`}
              onClick={() => handleSourceChange('sample')}
            >
              Balanced Audit Pool (12 Synthetic Profiles)
            </button>
            <button
              type="button"
              className={`rounded-full border px-3 py-1.5 ${source === 'upload' ? 'border-brand-600 bg-brand-50 text-brand-700' : 'border-gray-300 text-gray-600'}`}
              onClick={() => handleSourceChange('upload')}
            >
              Upload Custom Files
            </button>
          </div>

          {source === 'sample' ? (
            <p className="rounded-lg bg-green-50 px-3 py-2 text-sm text-green-800">
              Đã nạp {SAMPLE_CANDIDATES.length} hồ sơ kiểm định trên 4 nhóm nhân khẩu học giao nhau.
            </p>
          ) : (
            <div className="space-y-2">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,.txt"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="block w-full text-sm text-gray-600"
              />
              {uploading && <p className="text-sm text-gray-500">Đang phân tích CV đã upload…</p>}
              {uploadError && <p className="text-sm text-red-600">{uploadError}</p>}
              {candidatesPool.length > 0 && !uploading && (
                <p className="rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-800">
                  Đã phân tích thành công {candidatesPool.length} file CV.
                </p>
              )}
              {candidatesPool.length === 0 && !uploading && (
                <p className="rounded-lg bg-yellow-50 px-3 py-2 text-sm text-yellow-800">
                  Vui lòng upload một hoặc nhiều file CV, hoặc chuyển sang Balanced Audit Pool.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="flex justify-end border-t border-gray-200 pt-4">
        <button
          type="button"
          disabled={!canContinue}
          onClick={() => setStep(2)}
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Tiếp tục: Cấu hình &amp; Chạy →
        </button>
      </div>
    </div>
  )
}
