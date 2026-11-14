import { useState } from 'react'
import type { JobPostingFull } from '../../types/ats'
import { updateJob } from '../../lib/apiClient'

interface JobSettingsModalProps {
  job: JobPostingFull
  isOpen: boolean
  onClose: () => void
  onUpdated: () => void
}

export function JobSettingsModal({ job, isOpen, onClose, onUpdated }: JobSettingsModalProps) {
  const [title, setTitle] = useState(job.title)
  const [department, setDepartment] = useState(job.department || 'Engineering')
  const [location, setLocation] = useState(job.location || 'Hà Nội (Hybrid)')
  const [employmentType, setEmploymentType] = useState(job.employment_type || 'Full-time')
  const [experienceLevel, setExperienceLevel] = useState(job.experience_level || 'Mid-Level')
  const [status, setStatus] = useState<JobPostingFull['status']>(job.status || 'published')
  const [salaryMin, setSalaryMin] = useState<number>(job.salary_min || 0)
  const [salaryMax, setSalaryMax] = useState<number>(job.salary_max || 0)
  const [salaryCurrency, setSalaryCurrency] = useState(job.salary_currency || 'USD')
  const [deadline, setDeadline] = useState(job.deadline || '')
  const [description, setDescription] = useState(job.description || '')

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!isOpen) return null

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      await updateJob(job.id, {
        title: title.trim(),
        department: department.trim(),
        location: location.trim(),
        employment_type: employmentType,
        experience_level: experienceLevel,
        status,
        salary_min: Number(salaryMin) || 0,
        salary_max: Number(salaryMax) || 0,
        salary_currency: salaryCurrency,
        deadline: deadline || null,
        description: description.trim(),
      })
      onUpdated()
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Lỗi khi cập nhật cấu hình vị trí tuyển dụng')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs">
      <div className="w-full max-w-2xl rounded-2xl bg-white shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between bg-gray-50/70 rounded-t-2xl">
          <div className="flex items-center gap-2">
            <span className="text-xl">⚙️</span>
            <div>
              <h3 className="text-base font-bold text-gray-900">Cấu hình Thông tin Vị trí Tuyển dụng</h3>
              <p className="text-xs text-gray-500">Chỉnh sửa thông tin đăng tuyển, chế độ đãi ngộ và trạng thái tuyển dụng</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-700 cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Body Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-4 text-xs">
          {error && <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-red-700 font-medium">{error}</div>}

          {/* Title */}
          <div>
            <label className="block font-semibold text-gray-700 mb-1">Tiêu đề vị trí tuyển dụng *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs font-medium focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
              required
            />
          </div>

          {/* Department & Status */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Phòng ban / Bộ phận</label>
              <input
                type="text"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Trạng thái tuyển dụng</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as any)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs bg-white"
              >
                <option value="published">🟢 Đang mở tuyển (Published)</option>
                <option value="draft">📝 Bản nháp (Draft)</option>
                <option value="paused">⏸️ Tạm dừng nhận hồ sơ (Paused)</option>
                <option value="closed">🔒 Đã đóng tuyển dụng (Closed)</option>
              </select>
            </div>
          </div>

          {/* Location & Employment Type & Level */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Địa điểm</label>
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs"
              />
            </div>
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Hình thức làm việc</label>
              <select
                value={employmentType}
                onChange={(e) => setEmploymentType(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs bg-white"
              >
                <option value="Full-time">Toàn thời gian (Full-time)</option>
                <option value="Part-time">Bán thời gian (Part-time)</option>
                <option value="Hybrid">Linh hoạt (Hybrid)</option>
                <option value="Remote">Từ xa (Remote)</option>
                <option value="Contract">Hợp đồng (Contract)</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Cấp bậc yêu cầu</label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs bg-white"
              >
                <option value="Junior">Junior (0 - 2 năm)</option>
                <option value="Mid-Level">Mid-Level (2 - 4 năm)</option>
                <option value="Senior">Senior (5+ năm)</option>
                <option value="Lead / Principal">Lead / Principal</option>
              </select>
            </div>
          </div>

          {/* Salary & Deadline */}
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Lương tối thiểu</label>
              <input
                type="number"
                min="0"
                value={salaryMin}
                onChange={(e) => setSalaryMin(Number(e.target.value) || 0)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Lương tối đa</label>
              <input
                type="number"
                min="0"
                value={salaryMax}
                onChange={(e) => setSalaryMax(Number(e.target.value) || 0)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Tiền tệ</label>
              <select
                value={salaryCurrency}
                onChange={(e) => setSalaryCurrency(e.target.value)}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs bg-white"
              >
                <option value="USD">USD ($)</option>
                <option value="VND">VND (₫)</option>
                <option value="EUR">EUR (€)</option>
              </select>
            </div>
            <div>
              <label className="block font-semibold text-gray-700 mb-1">Hạn chót nộp hồ sơ</label>
              <input
                type="date"
                value={deadline ? deadline.split('T')[0] : ''}
                onChange={(e) => setDeadline(e.target.value ? `${e.target.value}T23:59:59` : '')}
                className="w-full rounded-xl border border-gray-300 px-3 py-2 text-xs"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block font-semibold text-gray-700 mb-1">Mô tả công việc (Job Description)</label>
            <textarea
              rows={5}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-xl border border-gray-300 p-3 text-xs leading-relaxed focus:border-brand-500 focus:outline-none"
              required
            />
          </div>

          {/* Footer Actions */}
          <div className="border-t border-gray-200 pt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-gray-300 bg-white px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-xl bg-brand-600 px-5 py-2 text-xs font-bold text-white shadow-xs hover:bg-brand-700 disabled:opacity-50 cursor-pointer"
            >
              {saving ? '⏳ Đang lưu cấu hình…' : '💾 Lưu cấu hình tin tuyển dụng'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
