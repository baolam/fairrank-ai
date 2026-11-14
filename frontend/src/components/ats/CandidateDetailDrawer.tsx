import { useEffect, useState } from 'react'
import type { ApplicationStage, CandidateApplicationFull, EmailLogRecord, InterviewRecord, RecruiterNoteRecord, ScorecardRecord } from '../../types/ats'
import { ATS_STAGES } from '../../types/ats'
import {
  createNote,
  createScorecard,
  listCandidateInterviews,
  listEmailLogs,
  listNotes,
  listScorecards,
  scheduleInterview,
  sendCandidateEmail,
  updateApplicationStage,
} from '../../lib/apiClient'

interface Props {
  candidate: CandidateApplicationFull | null
  jobTitle: string
  isOpen: boolean
  onClose: () => void
  onUpdated: () => void
}

type DrawerTab = 'cv' | 'scorecard' | 'notes' | 'interview' | 'email'

export function CandidateDetailDrawer({ candidate, jobTitle, isOpen, onClose, onUpdated }: Props) {
  const [activeTab, setActiveTab] = useState<DrawerTab>('cv')
  const [blindMode, setBlindMode] = useState(false)
  const [cvViewMode, setCvViewMode] = useState<'pdf' | 'visual' | 'raw'>('pdf')
  const [copiedCv, setCopiedCv] = useState(false)
  const [currentStage, setCurrentStage] = useState<ApplicationStage>(candidate?.stage ?? 'new')

  const recruiterCode = typeof window !== 'undefined' ? (sessionStorage.getItem('fairrank_recruiter_code') || 'fairrank-demo') : 'fairrank-demo'
  const pdfUrl = candidate
    ? `/api/v1/jobs/${candidate.job_id}/applications/${candidate.id}/cv.pdf?code=${encodeURIComponent(recruiterCode)}${blindMode ? '&blind=true' : ''}`
    : ''

  // Scorecards state
  const [scorecards, setScorecards] = useState<ScorecardRecord[]>([])
  const [evaluatorName, setEvaluatorName] = useState('Recruiter')
  const [recommendation, setRecommendation] = useState<ScorecardRecord['overall_recommendation']>('hire')
  const [techScore, setTechScore] = useState(4)
  const [commScore, setCommScore] = useState(4)
  const [expScore, setExpScore] = useState(4)
  const [scoreNotes, setScoreNotes] = useState('')

  // Notes state
  const [notes, setNotes] = useState<RecruiterNoteRecord[]>([])
  const [noteAuthor, setNoteAuthor] = useState('Recruiter')
  const [noteContent, setNoteContent] = useState('')

  // Interviews state
  const [interviews, setInterviews] = useState<InterviewRecord[]>([])
  const [roundType, setRoundType] = useState('Technical Interview')
  const [scheduledAt, setScheduledAt] = useState('')
  const [interviewer, setInterviewer] = useState('Tech Lead')
  const [meetLink, setMeetLink] = useState('https://meet.google.com/abc-defg-hij')

  // Email state
  const [emailLogs, setEmailLogs] = useState<EmailLogRecord[]>([])
  const [emailTemplate, setEmailTemplate] = useState('interview_invite')
  const [emailSubject, setEmailSubject] = useState('')
  const [emailBody, setEmailBody] = useState('')
  const [emailSending, setEmailSending] = useState(false)

  useEffect(() => {
    if (!candidate) return
    setCurrentStage(candidate.stage)
    loadTabData(candidate.job_id, candidate.id)
    updateEmailTemplate('interview_invite', candidate)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [candidate])

  async function loadTabData(jobId: string, appId: string) {
    try {
      const [sc, nt, iv, em] = await Promise.all([
        listScorecards(jobId, appId),
        listNotes(jobId, appId),
        listCandidateInterviews(jobId, appId),
        listEmailLogs(jobId, appId),
      ])
      setScorecards(sc)
      setNotes(nt)
      setInterviews(iv)
      setEmailLogs(em)
    } catch (e) {
      console.error('Failed loading drawer data', e)
    }
  }

  function updateEmailTemplate(tmpl: string, cand: CandidateApplicationFull) {
    setEmailTemplate(tmpl)
    const name = cand.candidate_name
    if (tmpl === 'interview_invite') {
      setEmailSubject(`Thư mời tham gia phỏng vấn vị trí ${jobTitle}`)
      setEmailBody(`Xin chào ${name},\n\nChúc mừng bạn đã vượt qua vòng sàng lọc hồ sơ cho vị trí ${jobTitle}!\nChúng tôi trân trọng mời bạn tham gia buổi phỏng vấn trực tuyến.\n\n- Vòng phỏng vấn: ${roundType}\n- Link phỏng vấn: ${meetLink}\n\nVui lòng phản hồi để xác nhận thời gian phù hợp.\n\nTrân trọng,\nĐội ngũ Tuyển dụng`)
    } else if (tmpl === 'application_received') {
      setEmailSubject(`Xác nhận đã nhận hồ sơ ứng tuyển - ${jobTitle}`)
      setEmailBody(`Xin chào ${name},\n\nCảm ơn bạn đã nộp hồ sơ ứng tuyển vị trí ${jobTitle}. Đội ngũ tuyển dụng đang tiến hành đánh giá hồ sơ và sẽ phản hồi trong thời gian sớm nhất.\n\nTrân trọng,\nPhòng Tuyển dụng`)
    } else if (tmpl === 'job_offer') {
      setEmailSubject(`Thư mời nhận việc (Job Offer) - Vị trí ${jobTitle}`)
      setEmailBody(`Xin chào ${name},\n\nSau các vòng phỏng vấn xuất sắc, chúng tôi rất vui mừng gửi tới bạn Thư mời nhận việc cho vị trí ${jobTitle}.\n\nChúng tôi hy vọng sớm được hợp tác cùng bạn!\n\nTrân trọng,\nPhòng Nhân sự`)
    } else if (tmpl === 'rejection') {
      setEmailSubject(`Thông báo kết quả ứng tuyển vị trí ${jobTitle}`)
      setEmailBody(`Xin chào ${name},\n\nCảm ơn bạn đã dành thời gian ứng tuyển vị trí ${jobTitle}.\nHiện tại hồ sơ của bạn chưa phù hợp nhất với tiêu chí đợt này. Chúng tôi đã lưu hồ sơ của bạn vào Kho Tài năng để liên hệ trong các cơ hội tiếp theo.\n\nChúc bạn luôn thành công!\n\nTrân trọng,\nĐội ngũ Tuyển dụng`)
    }
  }

  async function handleStageChange(newStage: ApplicationStage) {
    if (!candidate) return
    try {
      await updateApplicationStage(candidate.job_id, candidate.id, newStage)
      setCurrentStage(newStage)
      onUpdated()
    } catch (e) {
      alert('Không thể đổi trạng thái: ' + e)
    }
  }

  async function handleAddScorecard(e: React.FormEvent) {
    e.preventDefault()
    if (!candidate) return
    try {
      await createScorecard(candidate.job_id, candidate.id, {
        evaluator_name: evaluatorName,
        overall_recommendation: recommendation,
        technical_score: techScore,
        communication_score: commScore,
        experience_score: expScore,
        notes: scoreNotes,
      })
      setScoreNotes('')
      const sc = await listScorecards(candidate.job_id, candidate.id)
      setScorecards(sc)
      onUpdated()
    } catch (e) {
      alert('Lỗi lưu đánh giá: ' + e)
    }
  }

  async function handleAddNote(e: React.FormEvent) {
    e.preventDefault()
    if (!candidate || !noteContent.trim()) return
    try {
      await createNote(candidate.job_id, candidate.id, noteAuthor, noteContent.trim())
      setNoteContent('')
      const nt = await listNotes(candidate.job_id, candidate.id)
      setNotes(nt)
    } catch (e) {
      alert('Lỗi thêm ghi chú: ' + e)
    }
  }

  async function handleScheduleInterview(e: React.FormEvent) {
    e.preventDefault()
    if (!candidate || !scheduledAt) return
    try {
      await scheduleInterview(candidate.job_id, candidate.id, {
        round_type: roundType,
        scheduled_at: scheduledAt,
        interviewer_name: interviewer,
        meeting_link: meetLink,
        location: 'Online',
        notes: '',
      })
      const iv = await listCandidateInterviews(candidate.job_id, candidate.id)
      setInterviews(iv)
      setCurrentStage('interviewing')
      onUpdated()
      alert('Đã lên lịch phỏng vấn thành công!')
    } catch (e) {
      alert('Lỗi lên lịch: ' + e)
    }
  }

  async function handleSendEmail(e: React.FormEvent) {
    e.preventDefault()
    if (!candidate) return
    setEmailSending(true)
    try {
      await sendCandidateEmail(candidate.job_id, candidate.id, {
        template_type: emailTemplate,
        recipient_email: candidate.email || 'candidate@example.com',
        subject: emailSubject,
        body: emailBody,
      })
      const em = await listEmailLogs(candidate.job_id, candidate.id)
      setEmailLogs(em)
      alert('Đã gửi email thành công!')
    } catch (e) {
      alert('Lỗi gửi email: ' + e)
    } finally {
      setEmailSending(false)
    }
  }

  if (!isOpen || !candidate) return null

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs">
      <div className="absolute inset-y-0 right-0 flex max-w-full pl-10">
        <div className="w-screen max-w-3xl bg-white shadow-2xl flex flex-col">
          {/* Header */}
          <div className="border-b border-gray-200 px-6 py-4 bg-gray-50/70 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold text-gray-900">
                  {blindMode ? '🎭 [Hồ sơ Ẩn danh]' : candidate.candidate_name}
                </h2>
                {candidate.ai_score !== undefined && candidate.ai_score > 0 && (
                  <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                    AI Match: {candidate.ai_score}%
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                Ứng tuyển: <span className="font-medium text-gray-700">{jobTitle}</span> · Nộp lúc:{' '}
                {new Date(candidate.submitted_at).toLocaleDateString('vi-VN')}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-lg px-2.5 py-1.5 shadow-xs hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={blindMode}
                  onChange={(e) => setBlindMode(e.target.checked)}
                  className="rounded text-brand-600 focus:ring-brand-500"
                />
                Blind Mode (Ẩn danh)
              </label>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Quick Stage Progression Bar */}
          <div className="border-b border-gray-200 bg-white px-6 py-3 flex items-center justify-between gap-4">
            <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Giai đoạn hiện tại:</span>
            <div className="flex flex-wrap items-center gap-1.5">
              {ATS_STAGES.map((st) => (
                <button
                  key={st.id}
                  type="button"
                  onClick={() => handleStageChange(st.id)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                    currentStage === st.id
                      ? `${st.badge} ring-1 ring-inset ring-current font-bold`
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {st.label}
                </button>
              ))}
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="border-b border-gray-200 bg-gray-50 px-6 flex gap-6 text-sm font-medium text-gray-600">
            {[
              { id: 'cv', label: '📄 Hồ sơ CV' },
              { id: 'scorecard', label: `⭐ Đánh giá (${scorecards.length})` },
              { id: 'notes', label: `📝 Ghi chú (${notes.length})` },
              { id: 'interview', label: `🗓️ Phỏng vấn (${interviews.length})` },
              { id: 'email', label: `✉️ Gửi Email (${emailLogs.length})` },
            ].map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setActiveTab(t.id as DrawerTab)}
                className={`py-3 border-b-2 transition-colors ${
                  activeTab === t.id
                    ? 'border-brand-600 text-brand-600 font-semibold'
                    : 'border-transparent text-gray-500 hover:text-gray-800'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* TAB 1: CV & Profile */}
            {activeTab === 'cv' && (
              <div className="space-y-6">
                {!blindMode && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 rounded-xl border border-gray-200 bg-gray-50 p-4 text-xs">
                    <div>
                      <span className="text-gray-500">Email:</span>
                      <p className="font-medium text-gray-900 mt-0.5">{candidate.email || 'Chưa cung cấp'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Số điện thoại:</span>
                      <p className="font-medium text-gray-900 mt-0.5">{candidate.phone || 'Chưa cung cấp'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Kinh nghiệm:</span>
                      <p className="font-medium text-gray-900 mt-0.5">
                        {candidate.years_of_experience ? `${candidate.years_of_experience} năm` : 'N/A'}
                      </p>
                    </div>
                    <div>
                      <span className="text-gray-500">Vị trí hiện tại:</span>
                      <p className="font-medium text-gray-900 mt-0.5">{candidate.current_title || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Địa điểm:</span>
                      <p className="font-medium text-gray-900 mt-0.5">{candidate.location || 'N/A'}</p>
                    </div>
                    <div>
                      <span className="text-gray-500">Nhóm nhân khẩu học:</span>
                      <p className="font-medium text-gray-900 mt-0.5">{candidate.declared_group || 'Chưa khai báo'}</p>
                    </div>
                  </div>
                )}

                {/* AI & Keyword Match Breakdown */}
                <div className="rounded-xl border border-purple-200 bg-purple-50/60 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-xs font-bold text-purple-900 uppercase tracking-wider flex items-center gap-1.5">
                      <span>🎯</span> Đánh giá độ phù hợp AI & Từ khóa (AI & Keyword Breakdown)
                    </h3>
                    {candidate.ai_score !== undefined && candidate.ai_score > 0 && (
                      <span className="rounded-full bg-purple-600 px-2.5 py-0.5 text-xs font-bold text-white shadow-xs">
                        {candidate.ai_score}% Match
                      </span>
                    )}
                  </div>

                  {candidate.ai_rationale && (
                    <p className="text-xs text-purple-800 bg-white/80 rounded-lg p-2.5 border border-purple-100 leading-relaxed">
                      💡 {candidate.ai_rationale}
                    </p>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    {/* Matched Skills */}
                    <div className="rounded-lg bg-white p-3 border border-emerald-200">
                      <div className="flex items-center gap-1.5 mb-2 text-xs font-bold text-emerald-800">
                        <span>🟢</span>
                        <span>Khớp tiêu chí ({candidate.matched_skills?.length || 0})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {candidate.matched_skills && candidate.matched_skills.length > 0 ? (
                          candidate.matched_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200"
                            >
                              ✓ {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-gray-400 italic">Chưa phát hiện từ khóa khớp cụ thể</span>
                        )}
                      </div>
                    </div>

                    {/* Missing Skills */}
                    <div className="rounded-lg bg-white p-3 border border-red-200">
                      <div className="flex items-center gap-1.5 mb-2 text-xs font-bold text-red-800">
                        <span>🔴</span>
                        <span>Thiếu kỹ năng bắt buộc ({candidate.missing_skills?.length || 0})</span>
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {candidate.missing_skills && candidate.missing_skills.length > 0 ? (
                          candidate.missing_skills.map((s, idx) => (
                            <span
                              key={idx}
                              className="rounded-md bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700 border border-red-200"
                            >
                              ✗ {s}
                            </span>
                          ))
                        ) : (
                          <span className="text-xs text-emerald-600 font-medium">✓ Đạt đủ mọi kỹ năng bắt buộc!</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Extracted Skills */}
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Tất cả kỹ năng bóc tách từ CV ({candidate.skills.length})
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills.map((s, idx) => (
                      <span key={idx} className="rounded-md bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                        {s}
                      </span>
                    ))}
                    {candidate.skills.length === 0 && (
                      <span className="text-xs text-gray-400">Không tìm thấy kỹ năng cụ thể</span>
                    )}
                  </div>
                </div>

                {/* Resume Document Viewer */}
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-200 pb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-gray-900">📄 File CV Ứng viên (Curriculum Vitae)</span>
                      <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-bold text-red-700">
                        PDF Format
                      </span>
                      {blindMode && (
                        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold text-blue-700">
                          🎭 Đã ẩn danh
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <div className="inline-flex rounded-lg border border-gray-200 bg-gray-100 p-0.5 text-xs">
                        <button
                          type="button"
                          onClick={() => setCvViewMode('pdf')}
                          className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                            cvViewMode === 'pdf'
                              ? 'bg-white text-gray-900 shadow-2xs font-bold'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          📄 File PDF
                        </button>
                        <button
                          type="button"
                          onClick={() => setCvViewMode('visual')}
                          className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                            cvViewMode === 'visual'
                              ? 'bg-white text-gray-900 shadow-2xs font-bold'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          📑 Trực quan (HTML)
                        </button>
                        <button
                          type="button"
                          onClick={() => setCvViewMode('raw')}
                          className={`rounded-md px-2.5 py-1 font-medium transition-colors ${
                            cvViewMode === 'raw'
                              ? 'bg-white text-gray-900 shadow-2xs font-bold'
                              : 'text-gray-600 hover:text-gray-900'
                          }`}
                        >
                          🔤 Text gốc
                        </button>
                      </div>

                      {pdfUrl && (
                        <>
                          <a
                            href={pdfUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded-lg border border-gray-300 bg-white px-2.5 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 flex items-center gap-1 shadow-2xs transition-colors"
                            title="Mở tài liệu PDF trong tab trình duyệt mới"
                          >
                            🖨️ Mở Tab mới ↗
                          </a>
                          <a
                            href={pdfUrl}
                            download={`CV_${candidate.candidate_name.replace(/\s+/g, '_')}.pdf`}
                            className="rounded-lg bg-red-600 px-3 py-1 text-xs font-bold text-white hover:bg-red-700 flex items-center gap-1 shadow-2xs transition-colors"
                            title="Tải file PDF về máy tính"
                          >
                            📥 Tải PDF
                          </a>
                        </>
                      )}

                      <button
                        type="button"
                        onClick={() => {
                          const textToCopy = blindMode ? candidate.resume_redacted_text : candidate.resume_raw_text
                          navigator.clipboard.writeText(textToCopy)
                          setCopiedCv(true)
                          setTimeout(() => setCopiedCv(false), 2000)
                        }}
                        className="rounded-lg border border-gray-300 bg-white px-2.5 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                      >
                        {copiedCv ? '✓ Đã sao chép!' : '📋 Copy Text'}
                      </button>
                    </div>
                  </div>

                  {cvViewMode === 'pdf' ? (
                    <div className="rounded-2xl border border-gray-300 bg-white overflow-hidden shadow-sm flex flex-col">
                      <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 flex items-center justify-between text-xs text-gray-600">
                        <span className="flex items-center gap-2 font-medium">
                          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                          Bản PDF Curriculum Vitae chuẩn A4 ({blindMode ? 'Chế độ Ẩn danh Blind CV' : 'Đầy đủ thông tin'})
                        </span>
                        <span className="text-[11px] text-gray-500">
                          Nếu trình duyệt không tải tự động, bấm <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className="text-brand-600 font-bold underline">vào đây để xem</a>
                        </span>
                      </div>
                      <iframe
                        key={`${candidate.id}-${blindMode}`}
                        src={`${pdfUrl}#toolbar=1&navpanes=0`}
                        className="w-full h-[650px] border-0 bg-white"
                        title={`CV PDF - ${candidate.candidate_name}`}
                      />
                    </div>
                  ) : cvViewMode === 'visual' ? (
                    <div className="rounded-2xl border border-gray-300 bg-white p-6 shadow-sm space-y-6 max-h-[500px] overflow-y-auto">
                      {/* CV Header Profile */}
                      <div className="border-b border-gray-200 pb-5">
                        <div className="flex flex-wrap items-start justify-between gap-4">
                          <div>
                            <h2 className="text-xl font-bold text-gray-900 tracking-tight">
                              {blindMode ? '🎭 [Ứng viên Ẩn danh - Blind Candidate]' : candidate.candidate_name}
                            </h2>
                            <p className="text-sm font-semibold text-brand-600 mt-0.5">
                              {candidate.current_title || 'Chuyên viên ứng tuyển'}
                              {candidate.years_of_experience ? ` · ${candidate.years_of_experience} năm kinh nghiệm` : ''}
                            </p>
                            {!blindMode && (
                              <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-gray-500">
                                {candidate.email && <span>✉️ {candidate.email}</span>}
                                {candidate.phone && <span>📞 {candidate.phone}</span>}
                                {candidate.location && <span>📍 {candidate.location}</span>}
                              </div>
                            )}
                          </div>

                          <div className="text-right">
                            <span className="rounded-xl bg-purple-50 border border-purple-200 px-3 py-1.5 text-xs font-bold text-purple-700 inline-block">
                              🎯 Phù hợp: {candidate.ai_score || 0}%
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Technical Skills Highlight */}
                      {candidate.skills && candidate.skills.length > 0 && (
                        <div>
                          <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2">
                            🛠️ Kỹ năng chuyên môn
                          </h4>
                          <div className="flex flex-wrap gap-1.5">
                            {candidate.skills.map((s, idx) => (
                              <span
                                key={idx}
                                className="rounded-md bg-gray-100 border border-gray-200 px-2.5 py-1 text-xs font-medium text-gray-800"
                              >
                                {s}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Resume Body Text Content */}
                      <div>
                        <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-2">
                          📋 Nội dung chi tiết hồ sơ & Kinh nghiệm làm việc
                        </h4>
                        <div className="rounded-xl bg-gray-50/80 p-4 border border-gray-200 text-xs text-gray-800 leading-relaxed font-sans whitespace-pre-wrap space-y-2">
                          {(blindMode ? candidate.resume_redacted_text : candidate.resume_raw_text) || 'Chưa có nội dung CV.'}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <pre className="rounded-xl border border-gray-200 bg-gray-50 p-4 text-xs font-mono text-gray-800 whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto">
                      {blindMode ? candidate.resume_redacted_text : candidate.resume_raw_text}
                    </pre>
                  )}
                </div>
              </div>
            )}

            {/* TAB 2: Scorecard */}
            {activeTab === 'scorecard' && (
              <div className="space-y-6">
                <form onSubmit={handleAddScorecard} className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-4">
                  <h3 className="text-sm font-bold text-gray-900">✍️ Điền phiếu đánh giá phỏng vấn (Scorecard)</h3>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <label className="block text-gray-600 mb-1">Người đánh giá:</label>
                      <input
                        type="text"
                        value={evaluatorName}
                        onChange={(e) => setEvaluatorName(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-gray-600 mb-1">Đề xuất tuyển dụng:</label>
                      <select
                        value={recommendation}
                        onChange={(e) => setRecommendation(e.target.value as any)}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      >
                        <option value="strong_hire">🌟 Rất đề xuất (Strong Hire)</option>
                        <option value="hire">✅ Đề xuất (Hire)</option>
                        <option value="neutral">⚖️ Trung lập (Neutral)</option>
                        <option value="no_hire">⚠️ Không tuyển (No Hire)</option>
                        <option value="strong_no_hire">❌ Kiên quyết loại (Strong No Hire)</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 text-xs">
                    <div>
                      <label className="block text-gray-600 mb-1">Chuyên môn (1-5★):</label>
                      <input
                        type="number"
                        min={1}
                        max={5}
                        value={techScore}
                        onChange={(e) => setTechScore(Number(e.target.value))}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-600 mb-1">Giao tiếp (1-5★):</label>
                      <input
                        type="number"
                        min={1}
                        max={5}
                        value={commScore}
                        onChange={(e) => setCommScore(Number(e.target.value))}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      />
                    </div>
                    <div>
                      <label className="block text-gray-600 mb-1">Kinh nghiệm (1-5★):</label>
                      <input
                        type="number"
                        min={1}
                        max={5}
                        value={expScore}
                        onChange={(e) => setExpScore(Number(e.target.value))}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Nhận xét chi tiết:</label>
                    <textarea
                      rows={2}
                      value={scoreNotes}
                      onChange={(e) => setScoreNotes(e.target.value)}
                      placeholder="Ghi lại ấn tượng về ứng viên, kỹ năng giải quyết vấn đề..."
                      className="w-full rounded-lg border border-gray-300 bg-white p-2 text-xs"
                    />
                  </div>

                  <button
                    type="submit"
                    className="rounded-lg bg-brand-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-brand-700"
                  >
                    Lưu đánh giá
                  </button>
                </form>

                {/* Scorecards History */}
                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Lịch sử đánh giá ({scorecards.length})
                  </h4>
                  {scorecards.map((sc) => (
                    <div key={sc.id} className="rounded-xl border border-gray-200 bg-white p-3.5 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-gray-900">{sc.evaluator_name}</span>
                        <span className="rounded-md bg-purple-100 px-2 py-0.5 font-semibold text-purple-700">
                          {sc.overall_recommendation.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex gap-4 text-gray-600">
                        <span>Chuyên môn: {sc.technical_score}★</span>
                        <span>Giao tiếp: {sc.communication_score}★</span>
                        <span>Kinh nghiệm: {sc.experience_score}★</span>
                      </div>
                      {sc.notes && <p className="text-gray-700 italic border-t border-gray-100 pt-1.5">{sc.notes}</p>}
                    </div>
                  ))}
                  {scorecards.length === 0 && <p className="text-xs text-gray-400">Chưa có đánh giá nào.</p>}
                </div>
              </div>
            )}

            {/* TAB 3: Recruiter Notes */}
            {activeTab === 'notes' && (
              <div className="space-y-6">
                <form onSubmit={handleAddNote} className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={noteAuthor}
                      onChange={(e) => setNoteAuthor(e.target.value)}
                      placeholder="Tên của bạn"
                      className="w-1/3 rounded-lg border border-gray-300 px-3 py-1.5 text-xs"
                      required
                    />
                    <input
                      type="text"
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      placeholder="Viết ghi chú trao đổi nội bộ..."
                      className="flex-1 rounded-lg border border-gray-300 px-3 py-1.5 text-xs"
                      required
                    />
                    <button
                      type="submit"
                      className="rounded-lg bg-brand-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-brand-700"
                    >
                      Thêm
                    </button>
                  </div>
                </form>

                <div className="space-y-3">
                  {notes.map((n) => (
                    <div key={n.id} className="rounded-xl border border-gray-200 bg-gray-50 p-3 text-xs">
                      <div className="flex items-center justify-between font-semibold text-gray-800 mb-1">
                        <span>{n.author_name}</span>
                        <span className="text-gray-400 font-normal">
                          {new Date(n.created_at).toLocaleTimeString('vi-VN')}
                        </span>
                      </div>
                      <p className="text-gray-700">{n.content}</p>
                    </div>
                  ))}
                  {notes.length === 0 && <p className="text-xs text-gray-400">Chưa có ghi chú nào.</p>}
                </div>
              </div>
            )}

            {/* TAB 4: Interviews */}
            {activeTab === 'interview' && (
              <div className="space-y-6">
                <form onSubmit={handleScheduleInterview} className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3 text-xs">
                  <h3 className="text-sm font-bold text-gray-900">🗓️ Lên lịch phỏng vấn mới</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-gray-600 mb-1">Vòng phỏng vấn:</label>
                      <select
                        value={roundType}
                        onChange={(e) => setRoundType(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      >
                        <option value="Phone Screen">Sơ vấn điện thoại (Phone Screen)</option>
                        <option value="Technical Interview">Phỏng vấn Kỹ thuật (Technical)</option>
                        <option value="Hiring Manager">Phỏng vấn Trưởng bộ phận (Manager)</option>
                        <option value="Culture Fit">Phù hợp văn hóa (Culture Fit)</option>
                        <option value="Final Round">Vòng chung kết (Final Round)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-gray-600 mb-1">Thời gian:</label>
                      <input
                        type="datetime-local"
                        value={scheduledAt}
                        onChange={(e) => setScheduledAt(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-gray-600 mb-1">Người phỏng vấn:</label>
                      <input
                        type="text"
                        value={interviewer}
                        onChange={(e) => setInterviewer(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-gray-600 mb-1">Link họp (Google Meet/Zoom):</label>
                      <input
                        type="text"
                        value={meetLink}
                        onChange={(e) => setMeetLink(e.target.value)}
                        className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    className="rounded-lg bg-brand-600 px-4 py-2 font-semibold text-white hover:bg-brand-700"
                  >
                    Xác nhận lên lịch
                  </button>
                </form>

                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Lịch phỏng vấn của ứng viên ({interviews.length})
                  </h4>
                  {interviews.map((iv) => (
                    <div key={iv.id} className="rounded-xl border border-gray-200 bg-white p-3.5 space-y-1.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-gray-900">{iv.round_type}</span>
                        <span className="rounded-md bg-blue-100 px-2 py-0.5 font-semibold text-blue-700">
                          {iv.status.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-gray-600">
                        ⏰ Thời gian: <span className="font-medium text-gray-800">{iv.scheduled_at}</span> (
                        {iv.duration_minutes} phút)
                      </p>
                      <p className="text-gray-600">👤 Người phỏng vấn: {iv.interviewer_name}</p>
                      {iv.meeting_link && (
                        <p className="text-gray-600">
                          🔗 Link: <a href={iv.meeting_link} target="_blank" rel="noreferrer" className="text-brand-600 underline">{iv.meeting_link}</a>
                        </p>
                      )}
                    </div>
                  ))}
                  {interviews.length === 0 && <p className="text-xs text-gray-400">Chưa có lịch hẹn nào.</p>}
                </div>
              </div>
            )}

            {/* TAB 5: Email */}
            {activeTab === 'email' && (
              <div className="space-y-6">
                <form onSubmit={handleSendEmail} className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3 text-xs">
                  <h3 className="text-sm font-bold text-gray-900">✉️ Gửi email cho ứng viên</h3>
                  <div>
                    <label className="block text-gray-600 mb-1">Mẫu email tự động:</label>
                    <select
                      value={emailTemplate}
                      onChange={(e) => updateEmailTemplate(e.target.value, candidate)}
                      className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                    >
                      <option value="interview_invite">Thư mời tham gia phỏng vấn (Interview Invitation)</option>
                      <option value="application_received">Xác nhận đã nhận hồ sơ (Application Received)</option>
                      <option value="job_offer">Thư mời nhận việc (Job Offer)</option>
                      <option value="rejection">Thư thông báo từ chối lịch sự (Polite Rejection)</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-gray-600 mb-1">Gửi tới email:</label>
                    <input
                      type="email"
                      value={candidate.email || 'candidate@example.com'}
                      readOnly
                      className="w-full rounded-lg border border-gray-200 bg-gray-100 px-2.5 py-1.5 text-gray-600"
                    />
                  </div>

                  <div>
                    <label className="block text-gray-600 mb-1">Tiêu đề:</label>
                    <input
                      type="text"
                      value={emailSubject}
                      onChange={(e) => setEmailSubject(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 bg-white px-2.5 py-1.5"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-gray-600 mb-1">Nội dung thư:</label>
                    <textarea
                      rows={6}
                      value={emailBody}
                      onChange={(e) => setEmailBody(e.target.value)}
                      className="w-full rounded-lg border border-gray-300 bg-white p-2 font-mono text-xs leading-relaxed"
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={emailSending}
                    className="rounded-lg bg-brand-600 px-4 py-2 font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
                  >
                    {emailSending ? 'Đang gửi…' : 'Gửi email ngay'}
                  </button>
                </form>

                <div className="space-y-3">
                  <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Lịch sử email đã gửi ({emailLogs.length})
                  </h4>
                  {emailLogs.map((log) => (
                    <div key={log.id} className="rounded-xl border border-gray-200 bg-white p-3 space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-gray-800">{log.subject}</span>
                        <span className="text-gray-400">{new Date(log.sent_at).toLocaleTimeString('vi-VN')}</span>
                      </div>
                      <p className="text-gray-600 whitespace-pre-wrap">{log.body}</p>
                    </div>
                  ))}
                  {emailLogs.length === 0 && <p className="text-xs text-gray-400">Chưa có email nào được gửi.</p>}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
