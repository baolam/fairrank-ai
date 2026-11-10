import type { CandidateRecord } from '../types/api'

export const DEFAULT_JOB_TITLE = 'Senior Full-Stack Software Engineer'

export const DEFAULT_JOB_DESCRIPTION = `Senior Full-Stack Software Engineer
We are seeking an experienced developer with 5+ years of experience in Python, distributed backend architectures, FastAPI, Docker, and PostgreSQL. Experience in modern web frameworks (React/Vue), cloud infrastructure (AWS/GCP), and CI/CD pipelines is strongly preferred.`

export const SAMPLE_CANDIDATES: CandidateRecord[] = [
  {
    id: 'cand_01',
    name: 'Lakisha Washington',
    group: 'Black_female',
    relevance_grade: 2,
    resume:
      'Senior Python Developer with 6 years experience in scalable cloud services, Docker, FastAPI, and PostgreSQL. Built distributed microservices and managed CI/CD pipelines on AWS.',
  },
  {
    id: 'cand_02',
    name: 'Jamal Washington',
    group: 'Black_male',
    relevance_grade: 2,
    resume:
      'Full-stack engineer with 5 years backend experience using Python, PostgreSQL, REST APIs, and Docker. Proficient in automated testing and GCP deployments.',
  },
  {
    id: 'cand_03',
    name: 'Emily Miller',
    group: 'White_female',
    relevance_grade: 2,
    resume:
      'Lead software engineer with 7 years specializing in Python backend systems, microservices, PostgreSQL, and cloud architecture on AWS. Mentored junior engineers.',
  },
  {
    id: 'cand_04',
    name: 'Brad Miller',
    group: 'White_male',
    relevance_grade: 2,
    resume:
      'Experienced Python developer with 6 years building distributed databases, FastAPI, Docker, and AWS deployments. Strong knowledge of system design.',
  },
  {
    id: 'cand_05',
    name: 'Ebony Williams',
    group: 'Black_female',
    relevance_grade: 1,
    resume:
      'Frontend developer with 4 years React experience and 1 year Python scripting. Familiar with Docker and PostgreSQL, seeking full-stack transition.',
  },
  {
    id: 'cand_06',
    name: 'Tyrone Williams',
    group: 'Black_male',
    relevance_grade: 1,
    resume:
      'Backend developer with 3 years experience in Python and Flask. Some exposure to PostgreSQL and Docker containers in development environments.',
  },
  {
    id: 'cand_07',
    name: 'Sarah McCarthy',
    group: 'White_female',
    relevance_grade: 1,
    resume:
      'Junior software developer with 2 years Python and Django experience. Eager to expand into cloud infrastructure and distributed backend engineering.',
  },
  {
    id: 'cand_08',
    name: 'Douglas Meyer',
    group: 'White_male',
    relevance_grade: 1,
    resume:
      'Software engineer with 3 years Python and SQL database experience. Good foundational knowledge of RESTful API development and Git.',
  },
  {
    id: 'cand_09',
    name: 'Shaniqua Harris',
    group: 'Black_female',
    relevance_grade: 0,
    resume:
      'Digital marketing specialist and content strategist with 4 years managing social media campaigns, SEO, and Google Analytics. Basic HTML skills.',
  },
  {
    id: 'cand_10',
    name: 'Darnell Jefferson',
    group: 'Black_male',
    relevance_grade: 0,
    resume:
      'Customer success representative with 5 years managing client accounts, CRM data entry, and sales communication. Excellent verbal skills.',
  },
  {
    id: 'cand_11',
    name: 'Claire Snyder',
    group: 'White_female',
    relevance_grade: 0,
    resume:
      'Financial accountant with CPA credentials and 4 years auditing corporate financial reports. Expert in Excel spreadsheets and QuickBooks.',
  },
  {
    id: 'cand_12',
    name: 'Todd Sullivan',
    group: 'White_male',
    relevance_grade: 0,
    resume:
      'High school science teacher with 6 years experience designing chemistry curricula and leading biology laboratory sessions.',
  },
]
