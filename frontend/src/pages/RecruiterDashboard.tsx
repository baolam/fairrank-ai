import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createJobFull, listJobs } from '../lib/apiClient'
import { useAuthStore } from '../store/useAuthStore'
import { DEFAULT_JOB_DESCRIPTION, DEFAULT_JOB_TITLE } from '../data/sampleCandidates'
import type { JobPostingFull } from '../types/ats'

export function RecruiterDashboard() {
  const logout = useAuthStore((s) => s.logout)
  const [jobs, setJobs] = useState<JobPostingFull[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [deptFilter, setDeptFilter] = useState<string>('all')
  const [searchQuery, setSearchQuery] = useState('')

  // Form modal state
  const [formOpen, setFormOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [department, setDepartment] = useState('Engineering')
  const [location, setLocation] = useState('Hybrid / Hanoi')
  const [employmentType, setEmploymentType] = useState('Full-time')
  const [experienceLevel, setExperienceLevel] = useState('Mid-Level')
  const [salaryMin, setSalaryMin] = useState(1500)
  const [salaryMax, setSalaryMax] = useState(3000)
  const [currency, setCurrency] = useState('USD')
  const [status, setStatus] = useState<'published' | 'draft'>('published')
  const [reqInput, setReqInput] = useState('Python, FastAPI, Docker, CI/CD, Problem Solving')
  const [creating, setCreating] = useState(false)

  function refresh() {
    setLoading(true)
    listJobs()
      .then(setJobs)
      .catch((err) => setError(err instanceof Error ? err.message : 'Không tải được danh sách job.'))
      .finally(() => setLoading(false))
  }

  useEffect(refresh, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim() || !description.trim()) return
    setCreating(true)
    try {
      const requirements = reqInput
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      await createJobFull({
        title: title.trim(),
        description: description.trim(),
        department,
        location,
        employment_type: employmentType,
        experience_level: experienceLevel,
        salary_min: Number(salaryMin),
        salary_max: Number(salaryMax),
        salary_currency: currency,
        status,
        requirements,
      })
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

  // Filtered jobs
  const filteredJobs = jobs.filter((j) => {
    if (statusFilter !== 'all' && j.status !== statusFilter) return false
    if (deptFilter !== 'all' && j.department !== deptFilter) return false
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      return j.title.toLowerCase().includes(q) || j.description.toLowerCase().includes(q)
    }
    return true
  })

  // Summary Metrics
  const totalApps = jobs.reduce((acc, j) => acc + (j.application_count || 0), 0)
  const activeJobs = jobs.filter((j) => j.status === 'published').length
  const departments = Array.from(new Set(jobs.map((j) => j.department || 'Engineering')))

  return (
    <div className="min-h-screen bg-[#f6f5fb] px-4 py-8 sm:px-8">
      <div className="mx-auto max-w-6xl">
        {/* Header */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">🧑‍💼</span>
              <h1 className="text-2xl font-bold text-gray-900">FairRank-AI · ATS Enterprise Cockpit</h1>
            </div>
            <p className="text-sm text-gray-600 mt-0.5">
              Hệ thống Quản lý Tuyển dụng Toàn diện tích hợp Tự động hóa Sàng lọc & Giám sát Đạo đức AI.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/talent-pool"
              className="rounded-lg border border-brand-300 bg-white px-3 py-1.5 text-xs font-semibold text-brand-700 shadow-xs hover:bg-brand-50"
            >
              👥 Kho Tài năng (Talent Pool)
            </Link>
            <Link
              to="/quick-demo"
              className="rounded-lg border border-purple-300 bg-white px-3 py-1.5 text-xs font-semibold text-purple-700 shadow-xs hover:bg-purple-50"
            >
              🛡️ AI Audit Simulator
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

        {/* ATS Top Metrics Dashboard */}
        <div className="mb-8 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-blue-200 bg-white p-4 shadow-xs">
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider">Tin đang mở</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{activeJobs}</p>
            <span className="text-xs text-gray-400">Trên tổng số {jobs.length} tin</span>
          </div>
          <div className="rounded-2xl border border-purple-200 bg-white p-4 shadow-xs">
            <p className="text-xs font-semibold text-purple-600 uppercase tracking-wider">Tổng hồ sơ ứng tuyển</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{totalApps}</p>
            <span className="text-xs text-gray-400">Toàn bộ các chiến dịch</span>
          </div>
          <div className="rounded-2xl border border-emerald-200 bg-white p-4 shadow-xs">
            <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">AI Auto-Screening</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">100%</p>
            <span className="text-xs text-emerald-600 font-medium">BM25 + SBERT Active</span>
          </div>
          <div className="rounded-2xl border border-amber-200 bg-white p-4 shadow-xs">
            <p className="text-xs font-semibold text-amber-600 uppercase tracking-wider">Fairness Guard</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">EEOC / EU AI</p>
            <span className="text-xs text-amber-600 font-medium">4/5ths Rule & Blind Mode</span>
          </div>
        </div>

        {error && <div className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

        {/* Action & Filter Toolbar */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-xs">
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <input
              type="text"
              placeholder="🔍 Tìm kiếm vị trí..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-1.5 focus:border-brand-500 focus:outline-none"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-1.5 focus:border-brand-500 focus:outline-none"
            >
              <option value="all">Tất cả trạng thái</option>
              <option value="published">Đang tuyển (Published)</option>
              <option value="draft">Bản nháp (Draft)</option>
              <option value="closed">Đã đóng (Closed)</option>
            </select>
            <select
              value={deptFilter}
              onChange={(e) => setDeptFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-3 py-1.5 focus:border-brand-500 focus:outline-none"
            >
              <option value="all">Tất cả phòng ban</option>
              {departments.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            className="rounded-xl bg-brand-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-brand-700 transition-colors"
            onClick={() => setFormOpen(true)}
          >
            ➕ Đăng tin tuyển dụng mới
          </button>
        </div>

        {/* Create Job Modal */}
        {formOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
            <div className="w-full max-w-2xl rounded-2xl border border-gray-200 bg-white p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-3">
                <h3 className="text-lg font-bold text-gray-900">📝 Tạo tin tuyển dụng doanh nghiệp (Job Requisition)</h3>
                <button
                  type="button"
                  onClick={() => setFormOpen(false)}
                  className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleCreate} className="space-y-4 text-xs">
                <div>
                  <label className="block font-medium text-gray-700 mb-1">Tiêu đề vị trí tuyển dụng *</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="VD: Senior Full-Stack Engineer (React & FastAPI)"
                    className="w-full rounded-lg border border-gray-300 p-2.5 text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Phòng ban</label>
                    <input
                      type="text"
                      value={department}
                      onChange={(e) => setDepartment(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Địa điểm làm việc</label>
                    <input
                      type="text"
                      value={location}
                      onChange={(e) => setLocation(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Hình thức</label>
                    <select
                      value={employmentType}
                      onChange={(e) => setEmploymentType(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    >
                      <option value="Full-time">Full-time</option>
                      <option value="Part-time">Part-time</option>
                      <option value="Contract">Hợp đồng (Contract)</option>
                      <option value="Internship">Thực tập sinh</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Cấp bậc</label>
                    <select
                      value={experienceLevel}
                      onChange={(e) => setExperienceLevel(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    >
                      <option value="Junior">Junior (0 - 2 năm)</option>
                      <option value="Mid-Level">Mid-Level (2 - 5 năm)</option>
                      <option value="Senior">Senior (5+ năm)</option>
                      <option value="Lead / Manager">Lead / Quản lý</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Trạng thái tin</label>
                    <select
                      value={status}
                      onChange={(e) => setStatus(e.target.value as any)}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    >
                      <option value="published">Đăng ngay (Published)</option>
                      <option value="draft">Bản nháp (Draft)</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Lương tối thiểu</label>
                    <input
                      type="number"
                      value={salaryMin}
                      onChange={(e) => setSalaryMin(Number(e.target.value))}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Lương tối đa</label>
                    <input
                      type="number"
                      value={salaryMax}
                      onChange={(e) => setSalaryMax(Number(e.target.value))}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-gray-700 mb-1">Đơn vị tiền tệ</label>
                    <select
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 p-2"
                    >
                      <option value="USD">USD ($)</option>
                      <option value="VND">VNĐ (đ)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-gray-700 mb-1">Kỹ năng cốt lõi (cách nhau bởi dấu phẩy)</label>
                  <input
                    type="text"
                    value={reqInput}
                    onChange={(e) => setReqInput(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 p-2"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="font-medium text-gray-700">Mô tả công việc (JD) *</label>
                    <button
                      type="button"
                      className="text-xs text-brand-600 underline font-medium"
                      onClick={() => {
                        setTitle(DEFAULT_JOB_TITLE)
                        setDescription(DEFAULT_JOB_DESCRIPTION)
                      }}
                    >
                      🧪 Điền mẫu JD Senior Engineer
                    </button>
                  </div>
                  <textarea
                    rows={6}
                    required
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Nhập trách nhiệm công việc, yêu cầu kỹ năng..."
                    className="w-full rounded-lg border border-gray-300 p-2.5 font-mono text-xs leading-relaxed"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-100">
                  <button
                    type="button"
                    onClick={() => setFormOpen(false)}
                    className="rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Hủy bỏ
                  </button>
                  <button
                    type="submit"
                    disabled={creating || !title.trim() || !description.trim()}
                    className="rounded-lg bg-brand-600 px-5 py-2 font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
                  >
                    {creating ? 'Đang tạo…' : 'Xác nhận tạo tin'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Job Listings Grid */}
        {loading && <p className="text-center py-10 text-sm text-gray-500">Đang tải danh sách vị trí tuyển dụng…</p>}

        {!loading && filteredJobs.length === 0 && (
          <div className="rounded-2xl border border-gray-200 bg-white p-10 text-center">
            <span className="text-4xl">📂</span>
            <h3 className="mt-2 text-base font-bold text-gray-900">Không tìm thấy vị trí tuyển dụng nào</h3>
            <p className="mt-1 text-sm text-gray-500">Hãy thử thay đổi bộ lọc hoặc bấm "Đăng tin tuyển dụng mới".</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredJobs.map((job) => (
            <Link
              key={job.id}
              to={`/recruiter/${job.id}`}
              className="group rounded-2xl border border-gray-200 bg-white p-5 shadow-xs transition-all hover:border-brand-500 hover:shadow-md flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                        {job.department || 'Engineering'}
                      </span>
                      <span
                        className={`rounded-md px-2 py-0.5 text-xs font-semibold ${
                          job.status === 'published' ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {job.status === 'published' ? 'Active' : 'Draft'}
                      </span>
                    </div>
                    <h3 className="mt-2 text-base font-bold text-gray-900 group-hover:text-brand-700 transition-colors">
                      {job.title}
                    </h3>
                  </div>

                  <span className="rounded-full bg-brand-100 px-3 py-1 text-xs font-bold text-brand-800 shrink-0">
                    {job.application_count} ứng viên
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                  <span>📍 {job.location || 'Hybrid / Hanoi'}</span>
                  <span>💼 {job.employment_type || 'Full-time'}</span>
                  {job.salary_max ? (
                    <span>
                      💰 {job.salary_min} - {job.salary_max} {job.salary_currency}
                    </span>
                  ) : null}
                </div>

                {job.requirements && job.requirements.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {job.requirements.slice(0, 4).map((r, idx) => (
                      <span key={idx} className="rounded-md bg-gray-100 px-2 py-0.5 text-[11px] text-gray-600">
                        {r}
                      </span>
                    ))}
                    {job.requirements.length > 4 && (
                      <span className="text-[11px] text-gray-400 self-center">+{job.requirements.length - 4} kỹ năng</span>
                    )}
                  </div>
                )}
              </div>

              <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between text-xs text-gray-400">
                <span>Mở lúc: {new Date(job.created_at).toLocaleDateString('vi-VN')}</span>
                <span className="font-semibold text-brand-600 group-hover:translate-x-0.5 transition-transform">
                  Mở ATS Workspace →
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
