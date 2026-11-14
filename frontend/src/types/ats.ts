import type { IntersectionalGroup } from './api'

export type ApplicationStage =
  | 'new'
  | 'screening'
  | 'shortlisted'
  | 'interviewing'
  | 'offered'
  | 'hired'
  | 'rejected'

export const ATS_STAGES: { id: ApplicationStage; label: string; color: string; badge: string }[] = [
  { id: 'new', label: 'Mới nộp', color: 'border-blue-300 bg-blue-50/50', badge: 'bg-blue-100 text-blue-700' },
  { id: 'screening', label: 'Sàng lọc AI', color: 'border-purple-300 bg-purple-50/50', badge: 'bg-purple-100 text-purple-700' },
  { id: 'shortlisted', label: 'Lọt chọn lọc', color: 'border-amber-300 bg-amber-50/50', badge: 'bg-amber-100 text-amber-700' },
  { id: 'interviewing', label: 'Phỏng vấn', color: 'border-indigo-300 bg-indigo-50/50', badge: 'bg-indigo-100 text-indigo-700' },
  { id: 'offered', label: 'Đã gửi Offer', color: 'border-emerald-300 bg-emerald-50/50', badge: 'bg-emerald-100 text-emerald-700' },
  { id: 'hired', label: 'Đã tuyển dụng', color: 'border-teal-300 bg-teal-50/50', badge: 'bg-teal-100 text-teal-700' },
  { id: 'rejected', label: 'Bị loại', color: 'border-gray-300 bg-gray-50/50', badge: 'bg-gray-100 text-gray-700' },
]

export interface AICriteria {
  must_have_skills: string[]
  nice_to_have_skills: string[]
  min_experience_years: number
  weight_semantic: number
  weight_keyword: number
  weight_experience: number
  auto_advance_threshold: number
}

export interface JobPostingFull {
  id: string
  title: string
  description: string
  created_at: string
  department?: string
  location?: string
  employment_type?: string
  experience_level?: string
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  status?: 'published' | 'draft' | 'paused' | 'closed'
  deadline?: string | null
  requirements?: string[]
  application_count: number
  ai_criteria?: AICriteria
}

export interface CandidateApplicationFull {
  id: string
  job_id: string
  candidate_name: string
  declared_group: IntersectionalGroup | null
  resume_raw_text: string
  resume_redacted_text: string
  skills: string[]
  years_of_experience: number | null
  submitted_at: string
  email?: string
  phone?: string
  current_title?: string
  location?: string
  linkedin_url?: string
  stage: ApplicationStage
  rejection_reason?: string
  overall_rating?: number
  ai_score?: number
  ai_rationale?: string
  matched_skills?: string[]
  missing_skills?: string[]
  job_title?: string
  job_department?: string
}

export interface ScorecardRecord {
  id: string
  application_id: string
  evaluator_name: string
  overall_recommendation: 'strong_hire' | 'hire' | 'neutral' | 'no_hire' | 'strong_no_hire'
  technical_score: number
  communication_score: number
  experience_score: number
  notes: string
  created_at: string
}

export interface RecruiterNoteRecord {
  id: string
  application_id: string
  author_name: string
  content: string
  created_at: string
}

export interface InterviewRecord {
  id: string
  application_id: string
  round_type: string
  scheduled_at: string
  duration_minutes: number
  interviewer_name: string
  meeting_link?: string
  location?: string
  status: 'scheduled' | 'completed' | 'cancelled'
  notes?: string
  created_at: string
  candidate_name?: string
  job_id?: string
  job_title?: string
}

export interface EmailLogRecord {
  id: string
  application_id: string
  recipient_email: string
  template_type: string
  subject: string
  body: string
  sent_at: string
  status: string
}

export interface AdverseImpactSummary {
  group: string
  total: number
  passed: number
  selection_rate: number
  adverse_impact_ratio: number
  is_adverse: boolean
}

export interface JobFunnelAnalytics {
  job_id: string
  total_applications: number
  stage_counts: Record<ApplicationStage, number>
  adverse_impact: AdverseImpactSummary[]
}
