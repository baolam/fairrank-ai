import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createJob, listJobs } from '../lib/apiClient'
import { useAuthStore } from '../store/useAuthStore'
import { DEFAULT_JOB_DESCRIPTION, DEFAULT_JOB_TITLE } from '../data/sampleCandidates'
import type { JobPosting } from '../types/api'

export function RecruiterDashboard() {
  const logout = useAuthStore((s) => s.logout)
  const [jobs, setJobs] = useState<JobPosting[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [formOpen, setFormOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)

  function refresh() {
    setLoading(true)
    listJobs()
      .then(setJobs)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được danh sách job.'))
      .finally(() => setLoading(false))
  }

  useEffect(refresh, [])

  async function handleCreate() {
    if (!title.trim() || !description.trim()) return
    setCreating(true)
    try {
      await createJob(title.trim(), description.trim())
      setTitle('')
      setDescription('')
      setFormOpen(false)
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tạo job thất bại.')
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">🧑‍💼 Nhà tuyển dụng — Job Postings</h1>
          <div className="flex gap-3">
            <Link to="/" className="text-sm font-medium text-gray-500 hover:text-gray-800">
              ← Trang chủ
            </Link>
            <button type="button" className="text-sm font-medium text-red-600 hover:text-red-700" onClick={logout}>
              Đăng xuất
            </button>
          </div>
        </div>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <div className="mb-4 flex justify-end">
          <button
            type="button"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700"
            onClick={() => setFormOpen((v) => !v)}
          >
            {formOpen ? 'Đóng form' : '➕ Tạo job mới'}
          </button>
        </div>

        {formOpen && (
          <div className="mb-6 space-y-3 rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
            <label className="block text-sm font-medium text-gray-700">
              Tiêu đề job
              <input
                className="mt-1 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
            </label>
            <label className="block text-sm font-medium text-gray-700">
              Mô tả công việc (JD)
              <textarea
                className="mt-1 h-32 w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <div className="flex items-center justify-between">
              <button
                type="button"
                className="text-sm font-medium text-brand-700 underline"
                onClick={() => {
                  setTitle(DEFAULT_JOB_TITLE)
                  setDescription(DEFAULT_JOB_DESCRIPTION)
                }}
              >
                Dùng JD mẫu
              </button>
              <button
                type="button"
                disabled={creating || !title.trim() || !description.trim()}
                onClick={handleCreate}
                className="rounded-lg bg-brand-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {creating ? 'Đang tạo…' : 'Tạo job'}
              </button>
            </div>
          </div>
        )}

        {loading && <p className="text-sm text-gray-500">Đang tải danh sách job…</p>}

        {!loading && jobs.length === 0 && (
          <p className="rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-500">
            Chưa có job nào. Bấm "➕ Tạo job mới" để bắt đầu.
          </p>
        )}

        <div className="space-y-3">
          {jobs.map((job) => (
            <Link
              key={job.id}
              to={`/recruiter/${job.id}`}
              className="block rounded-xl border border-gray-200 bg-white p-4 shadow-sm transition-colors hover:border-brand-400"
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900">{job.title}</span>
                <span className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-700">
                  {job.application_count} hồ sơ
                </span>
              </div>
              <p className="mt-1 text-xs text-gray-400">
                Tạo lúc {new Date(job.created_at).toLocaleString()}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
