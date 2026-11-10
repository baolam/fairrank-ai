"""Script to generate a comprehensive, balanced suite of 14 professional sample PDF resumes.

Covers 4 intersectional demographic groups:
  - Black Female
  - Black Male
  - White Female
  - White Male

With calibrated relevance tiers:
  - Grade 2: High Fit (Senior Python, Cloud, Backend, ML, DevOps)
  - Grade 1: Moderate Fit (Junior/Mid Developer, Frontend transitioning to full-stack)
  - Grade 0: Negative Controls (Accountant, Marketing, Customer Success, Science Educator)
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_DIR = Path(__file__).resolve().parent / "sample_resumes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


RESUMES_DATA = [
    # -------------------------------------------------------------
    # 1. Sarah McCarthy (White Female - Grade 2: High Fit)
    # -------------------------------------------------------------
    {
        "filename": "sarah_mccarthy_senior_python.pdf",
        "name": "Sarah McCarthy",
        "title": "Senior Full-Stack Python Engineer",
        "contact": "Seattle, WA | sarah.mccarthy@cloudtech.dev | (206) 555-0192 | linkedin.com/in/sarah-mccarthy",
        "summary": "Results-driven Full-Stack Python Engineer with 6+ years of experience building distributed microservices, high-throughput REST APIs, and scalable web architectures. Proven track record in Docker containerization, PostgreSQL database optimization, Redis caching, and automated CI/CD deployment pipelines on AWS.",
        "skills": [
            ("Core Languages", "Python, JavaScript, TypeScript, SQL, Bash"),
            ("Frameworks", "FastAPI, Django, Flask, React, Node.js"),
            ("Cloud & DevOps", "Docker, Kubernetes, AWS (ECS, RDS, S3), CI/CD, Git"),
            ("Databases & Storage", "PostgreSQL, Redis, SQLite, Elasticsearch"),
        ],
        "experience": [
            {
                "role": "Senior Software Engineer",
                "company": "CloudTech Solutions — Seattle, WA",
                "period": "2022 – Present (3 years)",
                "bullets": [
                    "Architected high-throughput microservices using FastAPI and PostgreSQL handling over 5,000,000 daily API requests with sub-50ms latency.",
                    "Orchestrated container deployment pipelines with Docker and AWS ECS, reducing release cycle time by 60%.",
                    "Optimized complex PostgreSQL database queries and introduced Redis caching, boosting read throughput by 40%.",
                    "Mentored 4 junior engineers in test-driven development, code reviews, and software architecture best practices.",
                ],
            },
            {
                "role": "Software Engineer",
                "company": "Apex Digital Labs — Seattle, WA",
                "period": "2019 – 2022 (3 years)",
                "bullets": [
                    "Developed and maintained full-stack web applications utilizing React on the frontend and Django/Python on the backend.",
                    "Designed scalable relational schemas and automated migration scripts for PostgreSQL databases.",
                    "Implemented end-to-end testing with pytest and automated deployment workflows using GitHub Actions.",
                ],
            },
        ],
        "education": "B.S. in Computer Science | University of Washington, Magna Cum Laude",
    },

    # -------------------------------------------------------------
    # 2. Jamal Washington (Black Male - Grade 2: High Fit)
    # -------------------------------------------------------------
    {
        "filename": "jamal_washington_backend_engineer.pdf",
        "name": "Jamal Washington",
        "title": "Senior Backend Systems Engineer",
        "contact": "Atlanta, GA | jamal.washington@devworks.io | (404) 555-8831 | github.com/jamal-wash",
        "summary": "Senior Backend Systems Engineer with 5+ years of specialized experience in Python backend development, PostgreSQL, distributed messaging systems, and containerized cloud architectures on GCP. Adept at designing resilient event-driven systems with FastAPI, Celery, and Kafka.",
        "skills": [
            ("Languages", "Python, Go, SQL, Bash"),
            ("Frameworks & Tools", "FastAPI, Flask, Celery, Kafka, Docker, Kubernetes"),
            ("Databases & Cloud", "PostgreSQL, MongoDB, Redis, Google Cloud Platform (GCP), Git"),
            ("Engineering Practices", "Microservices, Distributed Systems, TDD, CI/CD Pipelines"),
        ],
        "experience": [
            {
                "role": "Senior Backend Engineer",
                "company": "DataForge Corp — Atlanta, GA",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Engineered real-time asynchronous data pipelines and microservices using Python, FastAPI, and Apache Kafka.",
                    "Reduced API p99 latency from 450ms to 85ms by re-architecting PostgreSQL schemas and query execution plans.",
                    "Led cloud infrastructure migration of 12 production microservices into Docker containers on Google Kubernetes Engine (GKE).",
                    "Authored comprehensive unit and integration test suites achieving 94% test coverage.",
                ],
            },
            {
                "role": "Backend Developer",
                "company": "Nexus Systems — Atlanta, GA",
                "period": "2019 – 2021 (2 years)",
                "bullets": [
                    "Built robust RESTful APIs with Python and Flask supporting 250,000 monthly active users.",
                    "Maintained automated CI/CD deployment workflows and monitored system reliability with Prometheus and Grafana.",
                    "Collaborated with frontend and QA teams in fast-paced Agile sprint cycles.",
                ],
            },
        ],
        "education": "B.S. in Software Engineering | Georgia Institute of Technology",
    },

    # -------------------------------------------------------------
    # 3. Lakisha Washington (Black Female - Grade 2: High Fit)
    # -------------------------------------------------------------
    {
        "filename": "lakisha_washington_cloud_engineer.pdf",
        "name": "Lakisha Washington",
        "title": "Staff Cloud & Distributed Systems Engineer",
        "contact": "Chicago, IL | lakisha.washington@nexustech.io | (312) 555-7719 | linkedin.com/in/lakisha-wash",
        "summary": "Accomplished Cloud & Distributed Systems Engineer with 6+ years of expertise in high-scale infrastructure, Python backend architectures, Docker container orchestration, and PostgreSQL performance tuning. Proven leader in deploying fault-tolerant services on AWS.",
        "skills": [
            ("Core Expertise", "Python, Go, Distributed Systems Architecture, REST APIs"),
            ("Cloud & DevOps", "Docker, Kubernetes, AWS, Terraform, CI/CD, Git, Linux"),
            ("Databases", "PostgreSQL, Redis, DynamoDB, TimescaleDB"),
            ("Frameworks", "FastAPI, Django, Flask, Pytest"),
        ],
        "experience": [
            {
                "role": "Lead Cloud Infrastructure Engineer",
                "company": "Nexus Enterprise Tech — Chicago, IL",
                "period": "2022 – Present (3 years)",
                "bullets": [
                    "Architected enterprise-grade multi-region cloud services on AWS utilizing Docker and Terraform.",
                    "Designed high-availability Python services using FastAPI with automatic failover and load balancing.",
                    "Spearheaded database scalability initiative, migrating legacy data to partition-tuned PostgreSQL clusters.",
                    "Established strict security and compliance standards for container images and cloud access.",
                ],
            },
            {
                "role": "Senior DevOps & Backend Engineer",
                "company": "Vanguard Cloud Labs — Chicago, IL",
                "period": "2019 – 2022 (3 years)",
                "bullets": [
                    "Automated infrastructure provisioning with Docker, Kubernetes, and GitLab CI/CD pipelines.",
                    "Developed backend microservices in Python for internal developer platform used by 200+ engineers.",
                    "Reduced cloud hosting costs by 28% through autoscaling and container workload rightsizing.",
                ],
            },
        ],
        "education": "M.S. in Computer Science | University of Illinois at Chicago | B.S. in Computer Engineering",
    },

    # -------------------------------------------------------------
    # 4. Brad Miller (White Male - Grade 2: High Fit)
    # -------------------------------------------------------------
    {
        "filename": "brad_miller_python_developer.pdf",
        "name": "Brad Miller",
        "title": "Lead Python & Platform Engineer",
        "contact": "Austin, TX | brad.miller@sysarch.org | (512) 555-3392 | github.com/bradmiller-dev",
        "summary": "Principal-level Python and Platform Engineer with 6+ years of experience architecting distributed backend services, high-concurrency APIs, and containerized deployments. Extensive hands-on experience with FastAPI, Docker, PostgreSQL, and AWS cloud solutions.",
        "skills": [
            ("Languages", "Python, TypeScript, SQL, Bash"),
            ("Frameworks", "FastAPI, Flask, Django, React"),
            ("DevOps & Cloud", "Docker, Kubernetes, AWS, GitHub Actions, Linux"),
            ("Databases", "PostgreSQL, Redis, MySQL"),
        ],
        "experience": [
            {
                "role": "Lead Platform Engineer",
                "company": "Systemic Architecture — Austin, TX",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Direct the architectural vision of core SaaS platforms built on Python (FastAPI) and PostgreSQL.",
                    "Containerized all backend services into standardized Docker containers with automated staging environments.",
                    "Engineered asynchronous task queues handling 2M transactions daily using Redis and Celery.",
                    "Mentored junior and mid-level developers in API design and unit testing methodologies.",
                ],
            },
            {
                "role": "Software Developer",
                "company": "Austin Tech Solutions — Austin, TX",
                "period": "2019 – 2021 (2 years)",
                "bullets": [
                    "Implemented RESTful web services using Python, Docker, and PostgreSQL databases.",
                    "Participated in agile code reviews and continuous delivery pipelines.",
                ],
            },
        ],
        "education": "B.S. in Computer Science | University of Texas at Austin",
    },

    # -------------------------------------------------------------
    # 5. Emily Miller (White Female - Grade 2: High Fit)
    # -------------------------------------------------------------
    {
        "filename": "emily_miller_lead_software_engineer.pdf",
        "name": "Emily Miller",
        "title": "Lead Software Engineer & Cloud Architect",
        "contact": "San Francisco, CA | emily.miller@codepath.io | (415) 555-0823 | linkedin.com/in/emily-miller-dev",
        "summary": "Lead Software Engineer with 7+ years of experience specializing in distributed Python backend architectures, high-scale microservices, PostgreSQL, and cloud deployments on AWS. Recognized for building fault-tolerant architectures and leading cross-functional engineering squads.",
        "skills": [
            ("Core Languages", "Python, TypeScript, Go, SQL"),
            ("Backend Frameworks", "FastAPI, Django, Flask, gRPC, Celery"),
            ("Cloud & Infrastructure", "AWS (EKS, Aurora, Lambda), Docker, Kubernetes, Terraform"),
            ("Databases", "PostgreSQL, Redis, DynamoDB"),
        ],
        "experience": [
            {
                "role": "Lead Software Engineer",
                "company": "Horizon Cloud Technologies — San Francisco, CA",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Spearheaded architectural evolution of core fintech platform using Python, FastAPI, and Docker on AWS EKS.",
                    "Engineered distributed transactional services processing $40M daily volume with 99.99% reliability.",
                    "Mentored 6 software engineers and instituted rigorous automated CI/CD pipelines with GitHub Actions.",
                ],
            },
            {
                "role": "Senior Backend Developer",
                "company": "BriteScale Software — San Jose, CA",
                "period": "2018 – 2021 (3 years)",
                "bullets": [
                    "Designed RESTful microservices in Python with PostgreSQL storage and Redis distributed caching.",
                    "Managed Docker containerization and orchestrated zero-downtime database schema migrations.",
                ],
            },
        ],
        "education": "M.S. in Computer Science | Stanford University | B.S. in EECS | UC Berkeley",
    },

    # -------------------------------------------------------------
    # 6. Aaliyah Jackson (Black Female - Grade 2: High Fit / ML)
    # -------------------------------------------------------------
    {
        "filename": "aaliyah_jackson_data_scientist.pdf",
        "name": "Aaliyah Jackson",
        "title": "Senior Machine Learning & Python Engineer",
        "contact": "New York, NY | aaliyah.jackson@mlsystems.ai | (212) 555-3918 | github.com/aaliyah-ai",
        "summary": "Senior ML & Python Systems Engineer with 5+ years of experience developing production machine learning pipelines, natural language processing services, and REST APIs using FastAPI, PyTorch, Docker, and PostgreSQL on AWS.",
        "skills": [
            ("AI & Languages", "Python, PyTorch, Scikit-Learn, SQL, R"),
            ("Backend & API", "FastAPI, Flask, Docker, Kubernetes, Celery"),
            ("Data & Storage", "PostgreSQL, Redis, Pandas, NumPy, Snowflake"),
            ("Cloud MLOps", "AWS SageMaker, MLflow, CI/CD, Git, Linux"),
        ],
        "experience": [
            {
                "role": "Senior Machine Learning Engineer",
                "company": "NeuralMetrics Corp — New York, NY",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Deployed high-throughput Python inference microservices with FastAPI and Docker serving 10M daily predictions.",
                    "Integrated ML model monitoring with PostgreSQL metadata storage and automated model retraining pipelines on AWS.",
                    "Decreased embedding inference latency by 45% via ONNX runtime optimizations and batching.",
                ],
            },
            {
                "role": "Data Scientist",
                "company": "Vantage Analytics — New York, NY",
                "period": "2019 – 2021 (2 years)",
                "bullets": [
                    "Built predictive customer retention models with Python and scikit-learn, generating $1.8M annual savings.",
                    "Designed PostgreSQL database schemas and automated daily ETL pipelines.",
                ],
            },
        ],
        "education": "M.S. in Data Science | Columbia University | B.S. in Applied Mathematics",
    },

    # -------------------------------------------------------------
    # 7. Matthew Baker (White Male - Grade 2: High Fit / DevOps)
    # -------------------------------------------------------------
    {
        "filename": "matthew_baker_devops_engineer.pdf",
        "name": "Matthew Baker",
        "title": "Senior DevOps & Site Reliability Engineer",
        "contact": "Denver, CO | matthew.baker@cloudinfra.net | (303) 555-8291 | github.com/matthewbaker-sre",
        "summary": "Senior DevOps & Platform Engineer with 6 years of experience managing distributed cloud infrastructures, CI/CD deployment pipelines, and high-availability backend services using Python, Docker, Kubernetes, Terraform, and PostgreSQL.",
        "skills": [
            ("DevOps & Cloud", "Docker, Kubernetes, AWS, Terraform, Helm, CI/CD, Linux"),
            ("Programming", "Python, Go, Bash, SQL"),
            ("Databases & Monitoring", "PostgreSQL, Redis, Prometheus, Grafana, Datadog"),
            ("Frameworks", "FastAPI, Flask, Pytest"),
        ],
        "experience": [
            {
                "role": "Senior Site Reliability Engineer",
                "company": "Alpine Cloud Platforms — Denver, CO",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Maintained 99.99% platform availability across 30+ Kubernetes microservices in production.",
                    "Created Python automation scripts and custom CLI tools with FastAPI for internal developer workflows.",
                    "Managed PostgreSQL high-availability replication clusters and automated disaster recovery backups.",
                ],
            },
            {
                "role": "Cloud Infrastructure Engineer",
                "company": "Peak Systems — Boulder, CO",
                "period": "2019 – 2021 (2 years)",
                "bullets": [
                    "Built automated GitLab CI/CD pipelines and provisioned multi-region AWS environments using Terraform.",
                    "Containerized legacy monolithic services with Docker and orchestrated deployments on ECS.",
                ],
            },
        ],
        "education": "B.S. in Computer Engineering | University of Michigan, Ann Arbor",
    },

    # -------------------------------------------------------------
    # 8. Ebony Williams (Black Female - Grade 1: Moderate Fit)
    # -------------------------------------------------------------
    {
        "filename": "ebony_williams_frontend_developer.pdf",
        "name": "Ebony Williams",
        "title": "Full-Stack & Frontend Software Developer",
        "contact": "New York, NY | ebony.williams@webstudio.co | (212) 555-6641 | ebonywilliams.design",
        "summary": "Creative Full-Stack and Frontend Developer with 4 years of experience delivering interactive web applications using React, TypeScript, and modern CSS frameworks, combined with 1+ year of Python backend API scripting and Docker containerization.",
        "skills": [
            ("Frontend", "React, TypeScript, JavaScript, HTML5, CSS3, Tailwind CSS, Next.js"),
            ("Backend & Tools", "Python, FastAPI, Node.js, REST APIs, Git, Docker"),
            ("Databases", "PostgreSQL, SQLite, MongoDB"),
        ],
        "experience": [
            {
                "role": "Frontend Developer",
                "company": "PixelCraft Studios — New York, NY",
                "period": "2022 – Present (3 years)",
                "bullets": [
                    "Built responsive, accessible web dashboards with React and TypeScript serving 100K+ users.",
                    "Collaborated with backend engineers to integrate REST APIs built in Python and FastAPI.",
                    "Standardized frontend testing with Jest and Cypress, decreasing bug regression rates by 35%.",
                ],
            },
            {
                "role": "Junior Web Developer",
                "company": "Metro Media Labs — New York, NY",
                "period": "2021 – 2022 (1 year)",
                "bullets": [
                    "Developed client landing pages and interactive components using React and Tailwind CSS.",
                    "Utilized Git and Docker for local development workflows and deployments.",
                ],
            },
        ],
        "education": "B.A. in Digital Media & Computer Science | New York University",
    },

    # -------------------------------------------------------------
    # 9. Tyrone Williams (Black Male - Grade 1: Moderate Fit)
    # -------------------------------------------------------------
    {
        "filename": "tyrone_williams_backend_developer.pdf",
        "name": "Tyrone Williams",
        "title": "Python & Backend Developer",
        "contact": "Philadelphia, PA | tyrone.williams@phillytech.org | (215) 555-4920 | github.com/tyrone-w",
        "summary": "Dedicated Backend Developer with 3 years of experience building web services in Python and Flask. Possesses foundational experience with PostgreSQL database queries, Docker container workflows, and RESTful API integrations.",
        "skills": [
            ("Programming", "Python, JavaScript, SQL, Bash"),
            ("Frameworks", "Flask, Django, FastAPI, Pytest"),
            ("Databases & Cloud", "PostgreSQL, SQLite, Docker, Git, Linux"),
            ("Web Technologies", "REST APIs, JSON, Postman, HTML/CSS"),
        ],
        "experience": [
            {
                "role": "Junior Backend Developer",
                "company": "Keystone Data Solutions — Philadelphia, PA",
                "period": "2022 – Present (3 years)",
                "bullets": [
                    "Developed backend endpoints using Python and Flask for internal inventory management system.",
                    "Maintained PostgreSQL database queries and assisted in writing integration tests with pytest.",
                    "Created Dockerfiles for local developer containerization and collaborated via Git pull requests.",
                ],
            },
            {
                "role": "Technical Support Analyst",
                "company": "Liberty Software Systems — Philadelphia, PA",
                "period": "2021 – 2022 (1 year)",
                "bullets": [
                    "Diagnosed API response errors and wrote automated Python scripts to clean customer data logs.",
                    "Resolved over 300 technical customer tickets with a 98% customer satisfaction score.",
                ],
            },
        ],
        "education": "B.S. in Information Technology | Morehouse College",
    },

    # -------------------------------------------------------------
    # 10. Douglas Meyer (White Male - Grade 1: Moderate Fit)
    # -------------------------------------------------------------
    {
        "filename": "douglas_meyer_software_engineer.pdf",
        "name": "Douglas Meyer",
        "title": "Software Engineer & Python Developer",
        "contact": "Minneapolis, MN | douglas.meyer@midwestcode.com | (612) 555-7381 | github.com/doug-meyer",
        "summary": "Software Engineer with 3 years of experience in Python software development, relational SQL databases, and RESTful API engineering. Familiar with Docker containers, automated unit tests, and continuous integration pipelines.",
        "skills": [
            ("Languages", "Python, SQL, JavaScript, HTML5, CSS3"),
            ("Frameworks", "Django, Flask, FastAPI (basic), Pytest"),
            ("Tools & DB", "PostgreSQL, MySQL, Git, Docker, GitHub Actions"),
        ],
        "experience": [
            {
                "role": "Associate Software Engineer",
                "company": "NorthStar Digital — Minneapolis, MN",
                "period": "2022 – Present (3 years)",
                "bullets": [
                    "Maintained Django web applications and implemented new RESTful endpoints for ecommerce clients.",
                    "Wrote automated unit test suites in pytest increasing test coverage from 60% to 82%.",
                    "Assisted DevOps team in creating Docker container images for deployment on staging servers.",
                ],
            },
            {
                "role": "Junior Programmer",
                "company": "Twin Cities Tech — St. Paul, MN",
                "period": "2021 – 2022 (1 year)",
                "bullets": [
                    "Authored Python data extraction scripts and maintained relational database tables in PostgreSQL.",
                    "Documented REST API schemas using Postman and Swagger OpenAPI specifications.",
                ],
            },
        ],
        "education": "B.S. in Computer Science | Purdue University",
    },

    # -------------------------------------------------------------
    # 11. Claire Snyder (White Female - Grade 0: Non-tech / Negative Control)
    # -------------------------------------------------------------
    {
        "filename": "claire_snyder_financial_accountant.pdf",
        "name": "Claire Snyder",
        "title": "Senior Certified Public Accountant (CPA)",
        "contact": "Chicago, IL | claire.snyder@cpa-audit.com | (312) 555-4421 | Member AICPA",
        "summary": "Detail-oriented Certified Public Accountant (CPA) and Corporate Financial Analyst with 6 years of experience in enterprise financial auditing, tax compliance, balance sheet reconciliation, and budget forecasting. Deep expertise in GAAP, SEC filings, and ERP accounting systems.",
        "skills": [
            ("Accounting & Compliance", "GAAP, IFRS, SEC Reporting, Internal Controls, Sarbanes-Oxley (SOX)"),
            ("Software & ERP", "QuickBooks Enterprise, SAP ERP, NetSuite, Oracle Financials"),
            ("Data & Analysis", "Advanced Excel (VBA, Power Query, VLOOKUP, Pivots), Financial Modeling"),
        ],
        "experience": [
            {
                "role": "Senior Audit Associate",
                "company": "Sterling & Meyer LLP — Chicago, IL",
                "period": "2020 – Present (5 years)",
                "bullets": [
                    "Supervised comprehensive financial audits for mid-market corporate clients with revenues up to $150M.",
                    "Evaluated internal control procedures, audited general ledgers, and verified compliance with GAAP standards.",
                    "Prepared consolidated corporate financial statements, cash flow forecasts, and executive tax packages.",
                ],
            },
            {
                "role": "Staff Accountant",
                "company": "Horizon Financial Partners — Chicago, IL",
                "period": "2019 – 2020 (1 year)",
                "bullets": [
                    "Performed monthly close reconciliations, payroll audits, and sales tax compliance filings.",
                    "Maintained accounts payable/receivable records in QuickBooks Enterprise with 99.8% accuracy.",
                ],
            },
        ],
        "education": "B.S. in Accounting | University of Illinois Urbana-Champaign\nCertified Public Accountant (CPA License #49281)",
    },

    # -------------------------------------------------------------
    # 12. Shaniqua Harris (Black Female - Grade 0: Non-tech / Negative Control)
    # -------------------------------------------------------------
    {
        "filename": "shaniqua_harris_digital_marketing.pdf",
        "name": "Shaniqua Harris",
        "title": "Senior Digital Marketing Strategist",
        "contact": "Atlanta, GA | shaniqua.harris@growthmark.org | (404) 555-1940 | linkedin.com/in/shaniqua-harris",
        "summary": "Creative and analytical Digital Marketing Strategist with 4 years of experience driving organic brand acquisition, social media campaign optimization, search engine marketing (SEO/SEM), and conversion funnel analytics. Proven success boosting engagement by 150%.",
        "skills": [
            ("Marketing & SEO", "SEO/SEM Strategy, Google Ads, Meta Ads Manager, Content Marketing, A/B Testing"),
            ("Analytics & CRM", "Google Analytics 4, Looker Studio, HubSpot, Mailchimp, Hootsuite"),
            ("Creative & Web", "Canva, Adobe Creative Cloud, Basic HTML, WordPress CMS, Copywriting"),
        ],
        "experience": [
            {
                "role": "Senior Digital Marketing Specialist",
                "company": "Apex Brand Agency — Atlanta, GA",
                "period": "2022 – Present (3 years)",
                "bullets": [
                    "Managed $450K annual ad spend across Meta, Google, and LinkedIn ad platforms with 3.8x ROAS.",
                    "Spearheaded technical SEO audit and keyword optimization, growing organic search traffic by 85%.",
                    "Produced monthly analytics performance dashboards using Looker Studio and Google Analytics 4.",
                ],
            },
            {
                "role": "Social Media Coordinator",
                "company": "Urban Pulse Media — Atlanta, GA",
                "period": "2021 – 2022 (1 year)",
                "bullets": [
                    "Authored compelling copywriting and curated digital creative assets for viral brand campaigns.",
                    "Engaged with audience community of 250,000 followers, increasing direct message conversions by 40%.",
                ],
            },
        ],
        "education": "B.A. in Marketing & Communications | Howard University, Summa Cum Laude",
    },

    # -------------------------------------------------------------
    # 13. Darnell Jefferson (Black Male - Grade 0: Non-tech / Negative Control)
    # -------------------------------------------------------------
    {
        "filename": "darnell_jefferson_customer_success.pdf",
        "name": "Darnell Jefferson",
        "title": "Customer Success Manager & Client Strategist",
        "contact": "Charlotte, NC | darnell.jefferson@successpulse.com | (704) 555-6184 | linkedin.com/in/darnell-j",
        "summary": "Results-oriented Customer Success Manager with 5 years of experience leading enterprise customer onboarding, retention strategies, and account growth. Adept at building executive stakeholder relationships and driving net revenue retention (NRR) above 115%.",
        "skills": [
            ("Client Strategy", "Customer Retention, Account Management, Enterprise Onboarding, QBR Leadership"),
            ("Software & CRM", "Salesforce, Gainsight, Zendesk, ChurnZero, Slack Enterprise, Jira"),
            ("Core Competencies", "Cross-Functional Collaboration, Conflict Resolution, Contract Renewals, Upselling"),
        ],
        "experience": [
            {
                "role": "Enterprise Customer Success Manager",
                "company": "CloudPeak SaaS — Charlotte, NC",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Managed portfolio of 35 strategic enterprise accounts representing $4.2M in annual recurring revenue.",
                    "Decreased annual client churn rate from 8.2% to 3.1% through proactive health score monitoring in Gainsight.",
                    "Conducted over 120 Quarterly Business Reviews (QBRs) delivering strategic ROI presentations to C-suite executives.",
                ],
            },
            {
                "role": "Client Onboarding Specialist",
                "company": "Beacon Solutions — Charlotte, NC",
                "period": "2019 – 2021 (2 years)",
                "bullets": [
                    "Led end-to-end technical onboarding and user training workshops for over 200 corporate clients.",
                    "Created comprehensive knowledge base documentation and self-serve help center guides.",
                ],
            },
        ],
        "education": "B.A. in Business Administration | Florida A&M University",
    },

    # -------------------------------------------------------------
    # 14. Todd Sullivan (White Male - Grade 0: Non-tech / Negative Control)
    # -------------------------------------------------------------
    {
        "filename": "todd_sullivan_science_educator.pdf",
        "name": "Todd Sullivan",
        "title": "High School Science Educator & STEM Department Head",
        "contact": "Boston, MA | todd.sullivan@bostonacademy.edu | (617) 555-2749 | Mass. Dept. of Ed. Certified",
        "summary": "Dedicated Secondary Science Educator and STEM Department Chair with 6 years of experience designing advanced chemistry curricula, directing biology laboratory safety programs, and mentoring student science Olympiad teams.",
        "skills": [
            ("Pedagogy & Teaching", "STEM Curriculum Design, Chemistry Instruction, AP Biology, Lab Safety Protocols"),
            ("Educational Tools", "Google Classroom, Canvas LMS, Vernier LabQuest Sensors, Smart Board Tech"),
            ("Leadership & Mentorship", "Department Budgeting, Science Olympiad Coaching, Student Academic Advisory"),
        ],
        "experience": [
            {
                "role": "STEM Department Chair & Chemistry Teacher",
                "company": "Boston Collegiate Academy — Boston, MA",
                "period": "2021 – Present (4 years)",
                "bullets": [
                    "Direct the science department of 9 faculty members, managing curriculum alignment and laboratory equipment budgets.",
                    "Taught AP Chemistry with 92% of students achieving passing scores of 4 or 5 on national exams.",
                    "Implemented inquiry-based laboratory experiments emphasizing scientific rigor and collaborative problem solving.",
                ],
            },
            {
                "role": "Science Teacher",
                "company": "Bay State High School — Boston, MA",
                "period": "2019 – 2021 (2 years)",
                "bullets": [
                    "Instructed 150+ students in introductory biology and physical science courses.",
                    "Fostered inclusive classroom environments and spearheaded after-school robotics club.",
                ],
            },
        ],
        "education": "M.Ed. in Secondary Science Education | Boston College | B.S. in Chemistry | Tufts University",
    },
]


def create_resume_pdf(data: dict, output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styling
    primary_color = colors.HexColor("#1e3a8a")  # Deep Navy Blue
    dark_gray = colors.HexColor("#1f2937")
    accent_gray = colors.HexColor("#4b5563")

    name_style = ParagraphStyle(
        "CandidateName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=2,
    )

    title_style = ParagraphStyle(
        "JobTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=dark_gray,
        spaceAfter=3,
    )

    contact_style = ParagraphStyle(
        "ContactInfo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=accent_gray,
        spaceAfter=8,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=primary_color,
        spaceBefore=7,
        spaceAfter=3,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_gray,
        spaceAfter=3,
    )

    bullet_style = ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=dark_gray,
        leftIndent=10,
        spaceAfter=2,
    )

    role_title_style = ParagraphStyle(
        "RoleTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=dark_gray,
    )

    period_style = ParagraphStyle(
        "RolePeriod",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=accent_gray,
        alignment=2,  # Right aligned
    )

    story = []

    # 1. Header (Name, Title, Contact)
    story.append(Paragraph(data["name"], name_style))
    story.append(Paragraph(data["title"], title_style))
    story.append(Paragraph(data["contact"], contact_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=6))

    # 2. Professional Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_heading))
    story.append(Paragraph(data["summary"], body_style))
    story.append(Spacer(1, 2))

    # 3. Technical Skills / Competencies
    story.append(Paragraph("SKILLS & CORE COMPETENCIES", section_heading))
    for category, skills_str in data["skills"]:
        p_text = f"<b>{category}:</b> {skills_str}"
        story.append(Paragraph(p_text, body_style))
    story.append(Spacer(1, 2))

    # 4. Work Experience
    story.append(Paragraph("PROFESSIONAL WORK EXPERIENCE", section_heading))
    for exp in data["experience"]:
        col1 = Paragraph(f"<b>{exp['role']}</b> | {exp['company']}", role_title_style)
        col2 = Paragraph(exp["period"], period_style)
        t = Table([[col1, col2]], colWidths=[385, 155])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        story.append(t)

        for bullet in exp["bullets"]:
            story.append(Paragraph(f"• {bullet}", bullet_style))
        story.append(Spacer(1, 3))

    # 5. Education
    story.append(Paragraph("EDUCATION & CREDENTIALS", section_heading))
    for edu_line in data["education"].split("\n"):
        story.append(Paragraph(edu_line, body_style))

    doc.build(story)


def main():
    print(f"Generating 14 sample PDF resumes in {OUTPUT_DIR}...")
    for item in RESUMES_DATA:
        file_path = OUTPUT_DIR / item["filename"]
        create_resume_pdf(item, file_path)
        print(f"  -> Generated: {file_path.name}")
    print("Done! All 14 sample PDF resumes generated successfully.")


if __name__ == "__main__":
    main()
