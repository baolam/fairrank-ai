import { useEffect, useState } from 'react'
import type { AICriteria, JobPostingFull } from '../../types/ats'
import { getJobAICriteria, updateJobAICriteria, reScoreJobApplications } from '../../lib/apiClient'

interface JobAICriteriaEditorProps {
  job: JobPostingFull
  onCriteriaUpdated?: () => void
}

const COMMON_SKILL_SUGGESTIONS = [
  'React',
  'TypeScript',
  'Tailwind CSS',
  'JavaScript',
  'Node.js',
  'Next.js',
  'Vue.js',
  'FastAPI',
  'Python',
  'Docker',
  'PostgreSQL',
  'Git',
  'AWS',
  'CI/CD',
  'REST API',
  'GraphQL',
  'Microservices',
  'Kubernetes',
]

export function JobAICriteriaEditor({ job, onCriteriaUpdated }: JobAICriteriaEditorProps) {
  const [criteria, setCriteria] = useState<AICriteria>(() => {
    return (
      job.ai_criteria || {
        must_have_skills: ['React', 'TypeScript', 'Tailwind CSS'],
        nice_to_have_skills: ['Docker', 'FastAPI'],
        min_experience_years: 2.0,
        weight_keyword: 0.45,
        weight_semantic: 0.35,
        weight_experience: 0.20,
        auto_advance_threshold: 70.0,
      }
    )
  })

  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [rescoring, setRescoring] = useState(false)
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const [newMustHave, setNewMustHave] = useState('')
  const [newNiceToHave, setNewNiceToHave] = useState('')

  useEffect(() => {
    let mounted = true
    setLoading(true)
    getJobAICriteria(job.id)
      .then((c) => {
        if (mounted && c && c.must_have_skills) {
          setCriteria(c)
        }
      })
      .catch((err) => {
        console.warn('Could not fetch custom criteria, using default:', err)
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => {
      mounted = false
    }
  }, [job.id])

  // Helpers for Must-Have tags (supports comma or newline separation)
  function addMustHave(skillInput: string) {
    const skills = skillInput
      .split(/[,;\n]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (skills.length === 0) return
    setCriteria((prev) => {
      const existingLower = new Set(prev.must_have_skills.map((s) => s.toLowerCase()))
      const toAdd = skills.filter((s) => !existingLower.has(s.toLowerCase()))
      return {
        ...prev,
        must_have_skills: [...prev.must_have_skills, ...toAdd],
      }
    })
    setNewMustHave('')
  }

  function removeMustHave(index: number) {
    setCriteria((prev) => ({
      ...prev,
      must_have_skills: prev.must_have_skills.filter((_, i) => i !== index),
    }))
  }

  function moveMustToNice(index: number) {
    const skill = criteria.must_have_skills[index]
    if (!skill) return
    removeMustHave(index)
    addNiceToHave(skill)
  }

  // Helpers for Nice-to-Have tags (supports comma or newline separation)
  function addNiceToHave(skillInput: string) {
    const skills = skillInput
      .split(/[,;\n]+/)
      .map((s) => s.trim())
      .filter(Boolean)
    if (skills.length === 0) return
    setCriteria((prev) => {
      const existingLower = new Set(prev.nice_to_have_skills.map((s) => s.toLowerCase()))
      const toAdd = skills.filter((s) => !existingLower.has(s.toLowerCase()))
      return {
        ...prev,
        nice_to_have_skills: [...prev.nice_to_have_skills, ...toAdd],
      }
    })
    setNewNiceToHave('')
  }

  function removeNiceToHave(index: number) {
    setCriteria((prev) => ({
      ...prev,
      nice_to_have_skills: prev.nice_to_have_skills.filter((_, i) => i !== index),
    }))
  }

  function moveNiceToMust(index: number) {
    const skill = criteria.nice_to_have_skills[index]
    if (!skill) return
    removeNiceToHave(index)
    addMustHave(skill)
  }

  // Weight auto-balancing
  const sumWeights = Math.round((criteria.weight_keyword + criteria.weight_semantic + criteria.weight_experience) * 100)
  const isWeightsBalanced = sumWeights === 100

  function handleAutoBalanceWeights() {
    const total = criteria.weight_keyword + criteria.weight_semantic + criteria.weight_experience
    if (total <= 0) {
      setCriteria((prev) => ({
        ...prev,
        weight_keyword: 0.45,
        weight_semantic: 0.35,
        weight_experience: 0.20,
      }))
      return
    }
    const kw = Math.round((criteria.weight_keyword / total) * 100) / 100
    const sem = Math.round((criteria.weight_semantic / total) * 100) / 100
    const exp = Math.round((1 - kw - sem) * 100) / 100
    setCriteria((prev) => ({
      ...prev,
      weight_keyword: kw,
      weight_semantic: sem,
      weight_experience: Math.max(0, exp),
    }))
  }

  // Save criteria
  async function handleSaveCriteria(reScoreNow: boolean) {
    setSaving(true)
    setStatusMessage(null)
    try {
      await updateJobAICriteria(job.id, criteria, reScoreNow)
      setStatusMessage({
        type: 'success',
        text: reScoreNow
          ? 'Đã lưu thiết lập AI và tự động tính toán lại điểm phù hợp cho tất cả ứng viên thành công!'
          : 'Đã lưu cấu hình tiêu chí AI thành công!',
      })
      if (onCriteriaUpdated) onCriteriaUpdated()
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: 'Không thể lưu tiêu chí: ' + (err.response?.data?.detail || err.message || err),
      })
    } finally {
      setSaving(false)
    }
  }

  // Manual re-score
  async function handleManualRescore() {
    setRescoring(true)
    setStatusMessage(null)
    try {
      const res = await reScoreJobApplications(job.id)
      setStatusMessage({
        type: 'success',
        text: res.message || `Đã tính toán lại điểm AI cho ${res.rescored_count} hồ sơ!`,
      })
      if (onCriteriaUpdated) onCriteriaUpdated()
    } catch (err: any) {
      setStatusMessage({
        type: 'error',
        text: 'Lỗi tính toán lại điểm: ' + (err.response?.data?.detail || err.message || err),
      })
    } finally {
      setRescoring(false)
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-sm text-gray-500">Đang tải thiết lập AI & Từ khóa…</div>
  }

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="rounded-2xl border border-purple-200 bg-gradient-to-r from-purple-50 via-indigo-50 to-white p-6 shadow-xs">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-purple-600 text-lg text-white shadow-xs">
                🎯
              </span>
              <h2 className="text-xl font-bold text-gray-900">Thiết lập Tiêu chí AI & Từ khóa (AI & Keywords Setup)</h2>
            </div>
            <p className="mt-1 text-xs text-gray-600 max-w-3xl leading-relaxed">
              Tùy biến bộ tiêu chí sàng lọc thông minh riêng cho vị trí <strong>{job.title}</strong>. Hệ thống AI kết hợp
              chặt chẽ giữa: <strong>Từ khóa bắt buộc & ưu tiên</strong>, <strong>Phân tích ngữ nghĩa học máy</strong>, và{' '}
              <strong>Số năm kinh nghiệm</strong> nhằm đưa ra điểm số minh bạch, có thể giải trình.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={rescoring || saving}
              onClick={handleManualRescore}
              className="rounded-xl border border-purple-300 bg-white px-3.5 py-2 text-xs font-semibold text-purple-700 shadow-xs hover:bg-purple-50 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {rescoring ? '⏳ Đang tính lại…' : '🔄 Tính lại điểm toàn bộ hồ sơ'}
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => handleSaveCriteria(true)}
              className="rounded-xl bg-purple-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-purple-700 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {saving ? '⏳ Đang lưu…' : '⚡ Lưu & Áp dụng ngay'}
            </button>
          </div>
        </div>
      </div>

      {statusMessage && (
        <div
          className={`rounded-xl border p-4 text-xs font-semibold flex items-center justify-between shadow-xs ${
            statusMessage.type === 'success'
              ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
              : 'border-red-200 bg-red-50 text-red-800'
          }`}
        >
          <span>{statusMessage.text}</span>
          <button
            type="button"
            onClick={() => setStatusMessage(null)}
            className="hover:opacity-75 font-bold cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Form Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* =========================================================================
            SECTION 1: MUST-HAVE & NICE-TO-HAVE SKILLS
        ========================================================================= */}
        <div className="space-y-6">
          {/* Must-Have Skills */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                <span className="text-red-500 font-bold">🔴</span> Kỹ năng bắt buộc (Must-Have Skills)
              </h3>
              <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-[11px] font-bold text-red-700">
                {criteria.must_have_skills.length} kỹ năng
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Ứng viên thiếu bất kỳ kỹ năng nào trong nhóm này sẽ bị gắn cờ cảnh báo đỏ và bị trừ điểm từ khóa đáng kể.
            </p>

            {/* Tag List */}
            <div className="flex flex-wrap gap-1.5 mb-3 min-h-[38px] p-2 bg-gray-50 rounded-xl border border-gray-200">
              {criteria.must_have_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 rounded-lg bg-red-50 border border-red-200 px-2.5 py-1 text-xs font-semibold text-red-700 shadow-2xs group"
                >
                  <span>✓ {skill}</span>
                  <button
                    type="button"
                    onClick={() => moveMustToNice(idx)}
                    className="hover:text-blue-700 font-bold text-gray-400 ml-1 text-[10px]"
                    title="Chuyển sang nhóm Kỹ năng ưu tiên"
                  >
                    ⇄
                  </button>
                  <button
                    type="button"
                    onClick={() => removeMustHave(idx)}
                    className="hover:text-red-900 font-bold text-red-400 ml-0.5 cursor-pointer"
                    title="Xóa kỹ năng này"
                  >
                    ×
                  </button>
                </span>
              ))}
              {criteria.must_have_skills.length === 0 && (
                <span className="text-xs text-gray-400 italic py-1">Chưa thiết lập kỹ năng bắt buộc nào</span>
              )}
            </div>

            {/* Add Input */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Nhập kỹ năng (hỗ trợ dấu phẩy: React, TypeScript, Python)…"
                value={newMustHave}
                onChange={(e) => setNewMustHave(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addMustHave(newMustHave)
                  }
                }}
                className="flex-1 rounded-xl border border-gray-300 bg-white px-3 py-1.5 text-xs focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              />
              <button
                type="button"
                onClick={() => addMustHave(newMustHave)}
                className="rounded-xl bg-red-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-red-700 transition-colors cursor-pointer"
              >
                + Thêm
              </button>
            </div>
          </div>

          {/* Nice-to-Have Skills */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
                <span className="text-blue-500 font-bold">🔵</span> Kỹ năng ưu tiên / Cộng điểm (Nice-to-Have)
              </h3>
              <span className="rounded-full bg-blue-100 px-2.5 py-0.5 text-[11px] font-bold text-blue-700">
                {criteria.nice_to_have_skills.length} kỹ năng
              </span>
            </div>
            <p className="text-xs text-gray-500 mb-3">
              Kỹ năng bổ trợ giúp tăng điểm xếp hạng và ưu tiên hồ sơ khi hai ứng viên có cùng trình độ.
            </p>

            {/* Tag List */}
            <div className="flex flex-wrap gap-1.5 mb-3 min-h-[38px] p-2 bg-gray-50 rounded-xl border border-gray-200">
              {criteria.nice_to_have_skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 rounded-lg bg-blue-50 border border-blue-200 px-2.5 py-1 text-xs font-semibold text-blue-700 shadow-2xs group"
                >
                  <span>+ {skill}</span>
                  <button
                    type="button"
                    onClick={() => moveNiceToMust(idx)}
                    className="hover:text-red-700 font-bold text-gray-400 ml-1 text-[10px]"
                    title="Chuyển sang nhóm Kỹ năng bắt buộc"
                  >
                    ⇄
                  </button>
                  <button
                    type="button"
                    onClick={() => removeNiceToHave(idx)}
                    className="hover:text-blue-900 font-bold text-blue-400 ml-0.5 cursor-pointer"
                    title="Xóa kỹ năng này"
                  >
                    ×
                  </button>
                </span>
              ))}
              {criteria.nice_to_have_skills.length === 0 && (
                <span className="text-xs text-gray-400 italic py-1">Chưa thiết lập kỹ năng ưu tiên nào</span>
              )}
            </div>

            {/* Add Input */}
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Nhập kỹ năng bổ trợ (hỗ trợ dấu phẩy: Docker, AWS, GraphQL)…"
                value={newNiceToHave}
                onChange={(e) => setNewNiceToHave(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addNiceToHave(newNiceToHave)
                  }
                }}
                className="flex-1 rounded-xl border border-gray-300 bg-white px-3 py-1.5 text-xs focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={() => addNiceToHave(newNiceToHave)}
                className="rounded-xl bg-blue-600 px-3.5 py-1.5 text-xs font-bold text-white hover:bg-blue-700 transition-colors cursor-pointer"
              >
                + Thêm
              </button>
            </div>
          </div>

          {/* Quick Suggestions */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs">
            <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
              💡 Gợi ý nhanh các kỹ năng phổ biến
            </h4>
            <div className="flex flex-wrap gap-2">
              {COMMON_SKILL_SUGGESTIONS.map((skill) => {
                const isMust = criteria.must_have_skills.some((s) => s.toLowerCase() === skill.toLowerCase())
                const isNice = criteria.nice_to_have_skills.some((s) => s.toLowerCase() === skill.toLowerCase())
                return (
                  <div
                    key={skill}
                    className={`inline-flex items-center gap-1 rounded-lg border px-2 py-1 text-xs font-medium ${
                      isMust
                        ? 'border-red-200 bg-red-50 text-red-700'
                        : isNice
                        ? 'border-blue-200 bg-blue-50 text-blue-700'
                        : 'border-gray-200 bg-gray-50 text-gray-700'
                    }`}
                  >
                    <span>{skill}</span>
                    {!isMust && !isNice ? (
                      <div className="flex items-center gap-1 ml-1 border-l border-gray-200 pl-1">
                        <button
                          type="button"
                          onClick={() => addMustHave(skill)}
                          className="hover:text-red-700 font-bold text-[10px] text-red-600 cursor-pointer"
                          title="Thêm vào Bắt buộc"
                        >
                          +Bắt buộc
                        </button>
                        <span className="text-gray-300">|</span>
                        <button
                          type="button"
                          onClick={() => addNiceToHave(skill)}
                          className="hover:text-blue-700 font-bold text-[10px] text-blue-600 cursor-pointer"
                          title="Thêm vào Ưu tiên"
                        >
                          +Ưu tiên
                        </button>
                      </div>
                    ) : isMust ? (
                      <span className="text-[10px] font-bold text-red-500 ml-1">✓ Bắt buộc</span>
                    ) : (
                      <span className="text-[10px] font-bold text-blue-500 ml-1">+ Ưu tiên</span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* =========================================================================
            SECTION 2: SCORING WEIGHTS & THRESHOLDS
        ========================================================================= */}
        <div className="space-y-6">
          {/* Weight Distribution */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-gray-900">⚖️ Phân bổ Trọng số Tính điểm AI</h3>
                <p className="text-xs text-gray-500">
                  Điều chỉnh tỷ trọng giữa Từ khóa, Ngữ nghĩa học máy và Số năm kinh nghiệm.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${
                    isWeightsBalanced ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                  }`}
                >
                  Tổng: {sumWeights}%
                </span>
                {!isWeightsBalanced && (
                  <button
                    type="button"
                    onClick={handleAutoBalanceWeights}
                    className="rounded-lg border border-gray-300 bg-white px-2 py-0.5 text-[11px] font-semibold text-gray-700 hover:bg-gray-50 cursor-pointer"
                  >
                    Cân bằng 100%
                  </button>
                )}
              </div>
            </div>

            {/* Slider 1: Keyword Weight */}
            <div className="rounded-xl bg-gray-50 p-3.5 border border-gray-100 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-gray-800">
                  1. Trọng số Khớp Từ khóa & Kỹ năng (Keyword Match):
                </span>
                <span className="font-mono font-bold text-brand-600">
                  {Math.round(criteria.weight_keyword * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={criteria.weight_keyword}
                onChange={(e) =>
                  setCriteria((prev) => ({ ...prev, weight_keyword: parseFloat(e.target.value) || 0 }))
                }
                className="w-full accent-brand-600 cursor-pointer"
              />
              <p className="text-[11px] text-gray-500">
                Tính dựa trên tỷ lệ khớp các kỹ năng Must-Have (70%) và Nice-to-Have (30%).
              </p>
            </div>

            {/* Slider 2: Semantic Weight */}
            <div className="rounded-xl bg-gray-50 p-3.5 border border-gray-100 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-gray-800">
                  2. Trọng số Tương đồng Ngữ nghĩa (Semantic Relevance):
                </span>
                <span className="font-mono font-bold text-purple-600">
                  {Math.round(criteria.weight_semantic * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={criteria.weight_semantic}
                onChange={(e) =>
                  setCriteria((prev) => ({ ...prev, weight_semantic: parseFloat(e.target.value) || 0 }))
                }
                className="w-full accent-purple-600 cursor-pointer"
              />
              <p className="text-[11px] text-gray-500">
                Mô hình BM25 / SBERT đo độ khớp tổng thể giữa mô tả công việc và kinh nghiệm trong CV.
              </p>
            </div>

            {/* Slider 3: Experience Weight */}
            <div className="rounded-xl bg-gray-50 p-3.5 border border-gray-100 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-gray-800">
                  3. Trọng số Năm kinh nghiệm (Experience Match):
                </span>
                <span className="font-mono font-bold text-emerald-600">
                  {Math.round(criteria.weight_experience * 100)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={criteria.weight_experience}
                onChange={(e) =>
                  setCriteria((prev) => ({ ...prev, weight_experience: parseFloat(e.target.value) || 0 }))
                }
                className="w-full accent-emerald-600 cursor-pointer"
              />
              <p className="text-[11px] text-gray-500">
                Đánh giá số năm kinh nghiệm thực tế bóc tách được so với ngưỡng tối thiểu yêu cầu.
              </p>
            </div>
          </div>

          {/* Thresholds & Years */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-gray-900">⚙️ Ngưỡng Kinh nghiệm & Tự động Sàng lọc</h3>

            {/* Min Experience */}
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-gray-700">Số năm kinh nghiệm tối thiểu yêu cầu:</label>
                <span className="font-bold text-indigo-700">{criteria.min_experience_years} năm</span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="0.5"
                  value={criteria.min_experience_years}
                  onChange={(e) =>
                    setCriteria((prev) => ({ ...prev, min_experience_years: parseFloat(e.target.value) || 0 }))
                  }
                  className="flex-1 accent-indigo-600 cursor-pointer"
                />
                <input
                  type="number"
                  min="0"
                  max="20"
                  step="0.5"
                  value={criteria.min_experience_years}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value)
                    setCriteria((prev) => ({
                      ...prev,
                      min_experience_years: isNaN(val) ? 0 : Math.max(0, val),
                    }))
                  }}
                  className="w-20 rounded-lg border border-gray-300 px-2 py-1 text-center font-bold"
                />
              </div>
            </div>

            {/* Auto-Advance Threshold */}
            <div className="space-y-1.5 text-xs pt-2 border-t border-gray-100">
              <div className="flex items-center justify-between">
                <label className="font-semibold text-gray-700">
                  Ngưỡng điểm AI tối thiểu để Đề xuất phỏng vấn (Auto-Advance Threshold):
                </label>
                <span className="font-bold text-emerald-700">{criteria.auto_advance_threshold}%</span>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="range"
                  min="40"
                  max="95"
                  step="1"
                  value={criteria.auto_advance_threshold}
                  onChange={(e) =>
                    setCriteria((prev) => ({
                      ...prev,
                      auto_advance_threshold: parseFloat(e.target.value) || 70,
                    }))
                  }
                  className="flex-1 accent-emerald-600 cursor-pointer"
                />
                <input
                  type="number"
                  min="40"
                  max="100"
                  value={criteria.auto_advance_threshold}
                  onChange={(e) => {
                    const val = parseFloat(e.target.value)
                    setCriteria((prev) => ({
                      ...prev,
                      auto_advance_threshold: isNaN(val) ? 40 : Math.min(100, Math.max(40, val)),
                    }))
                  }}
                  className="w-20 rounded-lg border border-gray-300 px-2 py-1 text-center font-bold"
                />
              </div>
              <p className="text-[11px] text-gray-500">
                Ứng viên đạt từ {criteria.auto_advance_threshold}% trở lên và đủ kỹ năng bắt buộc sẽ được tự động xếp ưu tiên lên đầu và đề xuất chuyển sang &quot;Lọt chọn lọc&quot;.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              disabled={saving}
              onClick={() => handleSaveCriteria(false)}
              className="rounded-xl border border-gray-300 bg-white px-4 py-2 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50 cursor-pointer"
            >
              Lưu cấu hình tiêu chí (Không tính lại điểm)
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => handleSaveCriteria(true)}
              className="rounded-xl bg-purple-600 px-5 py-2 text-xs font-bold text-white shadow-xs hover:bg-purple-700 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {saving ? '⏳ Đang lưu & tính toán lại…' : '⚡ Lưu & Tính toán lại điểm toàn bộ ứng viên'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
