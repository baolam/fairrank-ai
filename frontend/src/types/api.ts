export type IntersectionalGroup =
  | 'Black_female'
  | 'Black_male'
  | 'White_female'
  | 'White_male'

export const INTERSECTIONAL_GROUPS: IntersectionalGroup[] = [
  'Black_female',
  'Black_male',
  'White_female',
  'White_male',
]

export const GROUP_LABELS: Record<IntersectionalGroup, string> = {
  Black_female: 'Black Female',
  Black_male: 'Black Male',
  White_female: 'White Female',
  White_male: 'White Male',
}

export type RelevanceGrade = 0 | 1 | 2

export const RELEVANCE_LABELS: Record<RelevanceGrade, string> = {
  0: 'NO_FIT',
  1: 'POTENTIAL_FIT',
  2: 'GOOD_FIT',
}

export interface ParsedResume {
  candidate_id: string
  predicted_name: string | null
  skills: string[]
  years_of_experience: number | null
  raw_text: string
  redacted_text: string
  detected_sensitive_entities: string[]
}

export interface CandidateRecord {
  id: string
  name: string
  group: IntersectionalGroup
  relevance_grade: RelevanceGrade
  resume: string
  redacted_text?: string
  skills?: string[]
  years_of_experience?: number | null
}

export type ModelName = 'bm25' | 'sbert'

export interface CandidateInputPayload {
  id: string
  name: string
  text: string
  group: IntersectionalGroup
  relevance_grade: RelevanceGrade
}

export interface RankingRequestPayload {
  job_description: string
  candidates: CandidateInputPayload[]
  model_name: ModelName
  redaction_enabled: boolean
  lambda_penalty: number | null
  cutoff_k: number
}

export interface RankedCandidateOutput {
  rank: number
  candidate_id: string
  candidate_name: string
  group: string
  raw_score: number
  normalized_score: number
  exposure_at_k: number
  relevance_grade: RelevanceGrade
}

export interface GroupSummaryOutput {
  group: string
  candidate_count: number
  mean_exposure_at_10: number
  selection_rate_at_10: number
}

export interface RankingResponse {
  ranked_candidates: RankedCandidateOutput[]
  ndcg_at_k: number
  mrr: number
  black_white_exposure_gap: number
  female_male_exposure_gap: number
  intersectional_excess: number
  noise_floor: number
  cross_group_excess: number
  group_summaries: GroupSummaryOutput[]
}

export interface ParetoSweepRequestPayload {
  job_description: string
  candidates: CandidateInputPayload[]
  lambda_min: number
  lambda_max: number
  steps: number
  cutoff_k: number
}

export interface ParetoPoint {
  lambda_penalty: number
  ndcg_at_k: number
  black_white_exposure_gap: number
  female_male_exposure_gap: number
  intersectional_excess: number
}

export interface CounterfactualAuditRequestPayload {
  job_description: string
  candidate_profile: string
  baseline_model: ModelName
}

export interface GroupScoreSummary {
  group: string
  sample_names: string[]
  mean_score: number
  score_variance: number
  scores: number[]
}

export interface CounterfactualAuditResponse {
  candidate_profile_preview: string
  group_results: GroupScoreSummary[]
  max_demographic_shift: number
  is_sensitive: boolean
  redacted_group_results: GroupScoreSummary[]
  mitigated_max_demographic_shift: number
}

export interface ReportExportRequestPayload {
  job_title: string
  job_description: string
  model_name: string
  mitigation_strategy: string
  lambda_val: number
  ranking_summary: RankingResponse
}

export interface JobPosting {
  id: string
  title: string
  description: string
  created_at: string
  application_count: number
}

export interface ApplicationRecord {
  id: string
  job_id: string
  candidate_name: string
  declared_group: IntersectionalGroup | null
  resume_raw_text: string
  resume_redacted_text: string
  skills: string[]
  years_of_experience: number | null
  submitted_at: string
}

export interface ApplicationSubmitResult {
  id: string
  job_id: string
  candidate_name: string
  declared_group: IntersectionalGroup | null
  submitted_at: string
}

export interface LastRunState {
  jobTitle: string
  jobDescription: string
  modelLabel: string
  modelName: ModelName
  lambdaVal: number
  cutoffK: number
  redactionEnabled: boolean
  candidatesPool: CandidateRecord[]
  ranking: RankingResponse
}
