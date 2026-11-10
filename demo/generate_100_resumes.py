"""Script to generate exactly 100 diverse, professional sample PDF resumes.

Balanced 4-way intersectional demographic distribution (25 each):
  - 25 Black Female
  - 25 Black Male
  - 25 White Female
  - 25 White Male

Balanced 3-tier relevance distribution per group:
  - 10 Grade 2 (High Fit: Senior Python, Backend, Cloud, ML, DevOps)
  - 8 Grade 1 (Moderate Fit: Mid/Junior Developer, QA, Data Analyst)
  - 7 Grade 0 (Negative Controls: Accountant, Marketing, HR, Customer Success, etc.)

Total: 100 PDF resumes with JSON and CSV manifests.
"""

import json
import csv
import re
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.stimuli.manifest_builder import RAW_NAMES_DATA
from src.contracts.stimuli import IntersectionalGroup

OUTPUT_DIR = Path(__file__).resolve().parent / "sample_resumes"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 25 Realistic Archetypes mapped to 3 Relevance Tiers
ARCHETYPES = [
    # --- TIER 1: HIGH FIT (GRADE 2) - 10 roles ---
    {
        "id": "arch_01",
        "title": "Senior Full-Stack Python Engineer",
        "grade": 2,
        "exp_years": 6.0,
        "summary": "Full-Stack Python Engineer with 6 years of experience building distributed microservices, REST APIs, and scalable web architectures. Proven background in Docker containerization, PostgreSQL database optimization, Redis caching, and CI/CD pipelines.",
        "skills": [
            ("Languages", "Python, TypeScript, JavaScript, SQL"),
            ("Frameworks", "FastAPI, Django, Flask, React"),
            ("DevOps & Cloud", "Docker, Kubernetes, AWS, CI/CD, Git"),
            ("Databases", "PostgreSQL, Redis, SQLite"),
        ],
        "bullets": [
            "Architected high-throughput REST APIs handling 4M daily requests using FastAPI and PostgreSQL.",
            "Orchestrated container deployment pipelines with Docker and AWS ECS, cutting cycle times by 50%.",
            "Boosted database query response times by 35% using composite indexing and Redis caching.",
        ],
        "degree": "B.S. in Computer Science",
    },
    {
        "id": "arch_02",
        "title": "Senior Backend Systems Engineer",
        "grade": 2,
        "exp_years": 5.0,
        "summary": "Backend Systems Engineer with 5 years of specialized experience in Python backend development, PostgreSQL, distributed messaging systems, and containerized cloud architectures. Adept at FastAPI, Celery, and Kafka.",
        "skills": [
            ("Core Stack", "Python, Go, SQL, Bash"),
            ("Frameworks & Tools", "FastAPI, Flask, Celery, Kafka, Docker"),
            ("Databases & Cloud", "PostgreSQL, MongoDB, Redis, GCP, Git"),
            ("Architecture", "Microservices, Distributed Systems, TDD, CI/CD"),
        ],
        "bullets": [
            "Engineered real-time asynchronous data pipelines and microservices using Python, FastAPI, and Kafka.",
            "Reduced API p99 latency from 400ms to 75ms through PostgreSQL query plan optimization.",
            "Containerized 10 production services into Docker containers on Google Cloud Platform.",
        ],
        "degree": "B.S. in Software Engineering",
    },
    {
        "id": "arch_03",
        "title": "Staff Cloud & Distributed Systems Engineer",
        "grade": 2,
        "exp_years": 7.0,
        "summary": "Cloud and Distributed Systems Engineer with 7 years of expertise in high-scale infrastructure, Python backend architectures, Docker container orchestration, and PostgreSQL performance tuning on AWS.",
        "skills": [
            ("Core Languages", "Python, Go, SQL, Bash"),
            ("Cloud & Infrastructure", "Docker, Kubernetes, AWS, Terraform, CI/CD, Linux"),
            ("Databases", "PostgreSQL, Redis, DynamoDB"),
            ("Frameworks", "FastAPI, Django, Pytest"),
        ],
        "bullets": [
            "Architected enterprise multi-region cloud services on AWS using Docker, Terraform, and Kubernetes.",
            "Designed high-availability Python services using FastAPI with automatic failover.",
            "Spearheaded database scalability initiative, migrating legacy data to partition-tuned PostgreSQL clusters.",
        ],
        "degree": "M.S. in Computer Science",
    },
    {
        "id": "arch_04",
        "title": "Lead Platform & Python Engineer",
        "grade": 2,
        "exp_years": 6.0,
        "summary": "Platform and Python Engineer with 6 years of experience architecting distributed backend services, high-concurrency APIs, and containerized deployments with FastAPI, Docker, PostgreSQL, and AWS.",
        "skills": [
            ("Languages", "Python, TypeScript, SQL, Bash"),
            ("Frameworks", "FastAPI, Flask, Django, React"),
            ("DevOps & Cloud", "Docker, Kubernetes, AWS, GitHub Actions, Linux"),
            ("Databases", "PostgreSQL, Redis, MySQL"),
        ],
        "bullets": [
            "Directed architectural design of SaaS platforms built on Python (FastAPI) and PostgreSQL.",
            "Containerized backend services into standardized Docker containers with staging workflows.",
            "Engineered asynchronous task queues handling 2M transactions daily using Redis and Celery.",
        ],
        "degree": "B.S. in Computer Engineering",
    },
    {
        "id": "arch_05",
        "title": "Senior Machine Learning & Python Engineer",
        "grade": 2,
        "exp_years": 5.0,
        "summary": "Machine Learning Engineer with 5 years of experience developing production ML pipelines, NLP models, and scalable Python data services using FastAPI, PyTorch, Docker, and PostgreSQL on AWS.",
        "skills": [
            ("ML & Languages", "Python, PyTorch, Scikit-Learn, SQL, Pandas"),
            ("Backend & API", "FastAPI, Flask, Docker, Kubernetes, Celery"),
            ("Databases", "PostgreSQL, Redis, Snowflake"),
            ("MLOps", "AWS SageMaker, MLflow, CI/CD, Git"),
        ],
        "bullets": [
            "Deployed high-throughput Python inference microservices with FastAPI and Docker serving 8M daily requests.",
            "Integrated ML monitoring with PostgreSQL metadata storage and automated model retraining on AWS.",
            "Reduced model latency by 40% via ONNX runtime optimizations and batching.",
        ],
        "degree": "M.S. in Data Science",
    },
    {
        "id": "arch_06",
        "title": "Senior DevOps & Site Reliability Engineer",
        "grade": 2,
        "exp_years": 6.0,
        "summary": "DevOps and Site Reliability Engineer with 6 years of experience managing distributed cloud platforms, CI/CD deployment pipelines, and high-availability backend services using Python, Docker, Kubernetes, and PostgreSQL.",
        "skills": [
            ("DevOps & Cloud", "Docker, Kubernetes, AWS, Terraform, CI/CD, Linux"),
            ("Programming", "Python, Go, Bash, SQL"),
            ("Databases & Monitoring", "PostgreSQL, Redis, Prometheus, Grafana"),
            ("Frameworks", "FastAPI, Pytest"),
        ],
        "bullets": [
            "Maintained 99.99% platform availability across 25+ Kubernetes microservices in production.",
            "Created Python automation scripts and custom CLI tools with FastAPI for developer workflows.",
            "Managed PostgreSQL high-availability replication clusters with automated backups.",
        ],
        "degree": "B.S. in Computer Science",
    },
    {
        "id": "arch_07",
        "title": "Distributed Data Platform Engineer",
        "grade": 2,
        "exp_years": 5.0,
        "summary": "Data Platform Engineer with 5 years of experience building real-time data ingestion pipelines, streaming architectures, and Python data microservices with PostgreSQL, Docker, Kafka, and FastAPI.",
        "skills": [
            ("Data & Languages", "Python, SQL, Scala, Bash"),
            ("Streaming & Processing", "Apache Kafka, Spark, Celery, Airflow"),
            ("Databases & Storage", "PostgreSQL, ClickHouse, Redis, AWS S3"),
            ("Tools & Cloud", "Docker, Kubernetes, AWS, Git, CI/CD"),
        ],
        "bullets": [
            "Designed streaming ingestion pipeline processing 100M events daily using Kafka, Python, and PostgreSQL.",
            "Built RESTful data access APIs in FastAPI and containerized microservices in Docker.",
            "Optimized data warehousing schemas reducing analytical query costs by 30%.",
        ],
        "degree": "B.S. in Computer Engineering",
    },
    {
        "id": "arch_08",
        "title": "Senior Microservices & API Architect",
        "grade": 2,
        "exp_years": 7.0,
        "summary": "Software Architect with 7 years of experience designing robust microservice architectures, high-performance RESTful APIs, and distributed caching solutions in Python, Docker, FastAPI, and PostgreSQL.",
        "skills": [
            ("Architectural Stack", "Python, TypeScript, SQL, Go"),
            ("Frameworks", "FastAPI, Django, React, gRPC"),
            ("DevOps & Cloud", "Docker, Kubernetes, AWS, CI/CD, Git"),
            ("Databases", "PostgreSQL, Redis, Elasticsearch"),
        ],
        "bullets": [
            "Architected decoupled microservices for high-volume ecommerce transactions using FastAPI and PostgreSQL.",
            "Led transition from legacy monolith to containerized Docker workloads on AWS.",
            "Standardized API design guidelines and OpenAPI documentation across 5 development squads.",
        ],
        "degree": "M.S. in Software Systems",
    },
    {
        "id": "arch_09",
        "title": "Senior Python & Database Optimization Engineer",
        "grade": 2,
        "exp_years": 6.0,
        "summary": "Database and Backend Engineer with 6 years of experience optimizing relational schemas, building Python backend services, and managing containerized applications with Docker, PostgreSQL, and FastAPI.",
        "skills": [
            ("Core Focus", "Python, SQL, PL/pgSQL, Bash"),
            ("Databases", "PostgreSQL, MySQL, Redis, DynamoDB"),
            ("Frameworks & Tools", "FastAPI, SQLAlchemy, Docker, Linux, Git"),
            ("DevOps", "CI/CD, GitHub Actions, AWS RDS"),
        ],
        "bullets": [
            "Refactored relational schemas in PostgreSQL, cutting complex query latencies by 55%.",
            "Developed REST APIs in Python using FastAPI with SQLAlchemy ORM and connection pooling.",
            "Implemented automated database backup and disaster recovery validation with Docker scripts.",
        ],
        "degree": "B.S. in Information Systems",
    },
    {
        "id": "arch_10",
        "title": "Staff Software Engineer (Python & Cloud)",
        "grade": 2,
        "exp_years": 8.0,
        "summary": "Staff Software Engineer with 8 years of experience leading engineering squads, architecting enterprise Python platforms, containerized microservices with Docker, and mission-critical PostgreSQL databases on AWS.",
        "skills": [
            ("Core Expertise", "Python, TypeScript, Go, SQL"),
            ("Frameworks", "FastAPI, Django, React, Celery"),
            ("Cloud & Containers", "Docker, Kubernetes, AWS, Terraform, CI/CD"),
            ("Databases", "PostgreSQL, Redis, Cassandra"),
        ],
        "bullets": [
            "Led platform engineering for enterprise fintech applications handling $50M daily transactions.",
            "Built distributed services with FastAPI and PostgreSQL running on Kubernetes clusters.",
            "Mentored over 10 engineers in system design, testing methodologies, and clean architecture.",
        ],
        "degree": "M.S. in Computer Science",
    },

    # --- TIER 2: MODERATE FIT (GRADE 1) - 8 roles ---
    {
        "id": "arch_11",
        "title": "Python & Flask Backend Developer",
        "grade": 1,
        "exp_years": 3.0,
        "summary": "Backend Developer with 3 years of experience developing RESTful APIs with Python and Flask. Foundational experience with PostgreSQL queries, Docker container workflows, and Git collaboration.",
        "skills": [
            ("Languages", "Python, JavaScript, SQL"),
            ("Frameworks", "Flask, Django, FastAPI (basic)"),
            ("Databases & Tools", "PostgreSQL, SQLite, Docker, Git"),
            ("Web Tech", "REST APIs, JSON, Postman"),
        ],
        "bullets": [
            "Developed backend endpoints using Python and Flask for internal inventory management.",
            "Maintained PostgreSQL database queries and wrote automated tests in pytest.",
            "Created Dockerfiles for local developer containerization and collaborated via Git.",
        ],
        "degree": "B.S. in Computer Science",
    },
    {
        "id": "arch_12",
        "title": "Frontend Developer with Python Scripting",
        "grade": 1,
        "exp_years": 4.0,
        "summary": "Frontend Developer with 4 years of experience building interactive UI dashboards with React and TypeScript, combined with 1 year of Python backend scripting and Docker containerization.",
        "skills": [
            ("Frontend", "React, TypeScript, JavaScript, HTML5, CSS3, Tailwind"),
            ("Backend & Tools", "Python, FastAPI (basic), Node.js, Git, Docker"),
            ("Databases", "PostgreSQL (basic), SQLite"),
        ],
        "bullets": [
            "Built responsive web applications with React and TypeScript serving 80K users.",
            "Collaborated with backend engineers to integrate REST APIs built in Python.",
            "Used Docker and Git for local development workflows.",
        ],
        "degree": "B.A. in Digital Media",
    },
    {
        "id": "arch_13",
        "title": "QA Automation & Test Engineer (Python)",
        "grade": 1,
        "exp_years": 3.0,
        "summary": "Quality Assurance Automation Engineer with 3 years of experience writing automated test frameworks in Python using pytest, Selenium, and Postman for REST APIs with Docker integration.",
        "skills": [
            ("Testing & Code", "Python, Pytest, Selenium, Playwright, Postman"),
            ("Backend & Tools", "REST APIs, Docker, Git, CI/CD, SQL"),
            ("Databases", "PostgreSQL, SQLite"),
        ],
        "bullets": [
            "Built automated end-to-end testing frameworks in Python covering 200+ REST API endpoints.",
            "Integrated automated test runs into GitHub Actions CI/CD pipelines.",
            "Performed database verification queries in PostgreSQL during release cycles.",
        ],
        "degree": "B.S. in Information Technology",
    },
    {
        "id": "arch_14",
        "title": "Data Analyst & Python Developer",
        "grade": 1,
        "exp_years": 3.0,
        "summary": "Data Analyst with 3 years of experience in data extraction, ETL scripting with Python (Pandas/NumPy), SQL reporting in PostgreSQL, and building data dashboards.",
        "skills": [
            ("Data Tools", "Python, Pandas, NumPy, SQL, Tableau"),
            ("Databases", "PostgreSQL, MySQL, Excel, SQLite"),
            ("Development", "Git, Docker (basic), Jupyter, REST APIs"),
        ],
        "bullets": [
            "Created automated Python ETL scripts pulling data from PostgreSQL for weekly executive reporting.",
            "Designed analytical SQL queries to track user acquisition and product feature adoption.",
            "Containerized data analytics scripts with Docker for scheduled cron jobs.",
        ],
        "degree": "B.S. in Statistics",
    },
    {
        "id": "arch_15",
        "title": "Junior Full-Stack Web Developer",
        "grade": 1,
        "exp_years": 2.0,
        "summary": "Junior Full-Stack Web Developer with 2 years of experience developing responsive web applications using React on the frontend and Python (FastAPI/Django) on the backend with PostgreSQL.",
        "skills": [
            ("Languages", "Python, JavaScript, HTML5, CSS3, SQL"),
            ("Frameworks", "FastAPI, Django, React, Bootstrap"),
            ("Tools & DB", "PostgreSQL, Git, Docker (basic), Postman"),
        ],
        "bullets": [
            "Implemented CRUD REST API endpoints in Python using FastAPI.",
            "Built dynamic user interfaces using React and Tailwind CSS.",
            "Participated in agile code reviews and maintained unit tests in pytest.",
        ],
        "degree": "B.S. in Computer Science",
    },
    {
        "id": "arch_16",
        "title": "Junior Backend Developer (Django & SQL)",
        "grade": 1,
        "exp_years": 2.0,
        "summary": "Junior Backend Developer with 2 years of experience building web applications using Python, Django, and PostgreSQL. Familiar with Docker containers and Git version control.",
        "skills": [
            ("Languages & Web", "Python, SQL, HTML, CSS"),
            ("Frameworks", "Django, Flask, Pytest"),
            ("Databases & Tools", "PostgreSQL, SQLite, Docker (basic), Git"),
        ],
        "bullets": [
            "Built backend services with Django ORM and PostgreSQL databases.",
            "Created automated unit test suites in pytest increasing test coverage to 80%.",
            "Used Git for branching, pull requests, and code reviews.",
        ],
        "degree": "B.S. in Software Engineering",
    },
    {
        "id": "arch_17",
        "title": "Systems Administrator & Automation Scripter",
        "grade": 1,
        "exp_years": 4.0,
        "summary": "Systems Administrator with 4 years of experience managing Linux servers, automating deployment tasks with Python and Bash, and containerizing services with Docker.",
        "skills": [
            ("Systems & Scripting", "Linux, Bash, Python, PowerShell"),
            ("Containers & Cloud", "Docker, AWS (EC2/S3), Git, CI/CD"),
            ("Databases", "PostgreSQL (basic), MySQL"),
        ],
        "bullets": [
            "Automated system health monitoring and log rotation scripts in Python and Bash.",
            "Managed Docker containers across staging and production Linux environments.",
            "Configured PostgreSQL database backup schedules and user permissions.",
        ],
        "degree": "B.S. in Network Administration",
    },
    {
        "id": "arch_18",
        "title": "Application Support Engineer (Python & SQL)",
        "grade": 1,
        "exp_years": 3.0,
        "summary": "Application Support Engineer with 3 years of experience debugging production software, writing Python automation scripts, querying PostgreSQL databases, and analyzing API log files.",
        "skills": [
            ("Support & Scripting", "Python, SQL, Bash, REST APIs, JSON"),
            ("Databases & Tools", "PostgreSQL, MySQL, Postman, Git, Jira, Docker (basic)"),
        ],
        "bullets": [
            "Investigated production API issues using Postman and SQL queries in PostgreSQL.",
            "Developed Python data cleanup scripts to resolve customer record discrepancies.",
            "Collaborated with core engineering team to reproduce software bugs in Docker environments.",
        ],
        "degree": "B.S. in Information Technology",
    },

    # --- TIER 3: NEGATIVE CONTROLS (GRADE 0) - 7 roles ---
    {
        "id": "arch_19",
        "title": "Certified Public Accountant (CPA)",
        "grade": 0,
        "exp_years": 6.0,
        "summary": "Certified Public Accountant (CPA) with 6 years of experience in enterprise financial auditing, tax compliance, ledger reconciliation, and corporate balance sheet reviews under GAAP standards.",
        "skills": [
            ("Accounting & Audit", "GAAP, IFRS, Tax Compliance, Financial Auditing, SOX"),
            ("Software & ERP", "QuickBooks Enterprise, SAP ERP, NetSuite"),
            ("Analysis", "Advanced Excel (VBA, Power Query, Financial Modeling)"),
        ],
        "bullets": [
            "Led comprehensive financial audits for corporate clients with revenues up to $100M.",
            "Prepared monthly balance sheet reconciliations and quarterly tax documentation.",
            "Evaluated internal accounting controls to ensure strict compliance with GAAP guidelines.",
        ],
        "degree": "B.S. in Accounting, CPA Licensed",
    },
    {
        "id": "arch_20",
        "title": "Senior Digital Marketing Strategist",
        "grade": 0,
        "exp_years": 4.0,
        "summary": "Digital Marketing Strategist with 4 years of experience driving multi-channel advertising campaigns, search engine optimization (SEO/SEM), content strategy, and social media audience growth.",
        "skills": [
            ("Marketing & SEO", "SEO/SEM Strategy, Google Ads, Meta Ads Manager, A/B Testing"),
            ("Analytics & CRM", "Google Analytics 4, Looker Studio, HubSpot, Mailchimp"),
            ("Creative", "Content Marketing, Copywriting, Canva, WordPress"),
        ],
        "bullets": [
            "Managed $350K annual advertising spend across search and social channels delivering 3.5x ROAS.",
            "Spearheaded technical SEO keyword strategy, increasing organic website visits by 75%.",
            "Produced weekly marketing analytics reports using Google Analytics 4 and Looker Studio.",
        ],
        "degree": "B.A. in Marketing & Communications",
    },
    {
        "id": "arch_21",
        "title": "Customer Success & Client Account Manager",
        "grade": 0,
        "exp_years": 5.0,
        "summary": "Customer Success Manager with 5 years of experience leading enterprise client onboarding, user training, account retention strategies, and cross-functional support coordination.",
        "skills": [
            ("Client Relations", "Customer Success, Account Management, Enterprise Onboarding, QBRs"),
            ("Software & CRM", "Salesforce CRM, Zendesk, Gainsight, Slack Enterprise"),
            ("Competencies", "Client Retention, Relationship Building, Upselling"),
        ],
        "bullets": [
            "Managed portfolio of 30 enterprise accounts representing $3.5M in annual contract value.",
            "Lowered annual client churn rate from 7.5% to 2.8% through proactive engagement.",
            "Conducted quarterly business reviews with client directors to present product value metrics.",
        ],
        "degree": "B.A. in Business Administration",
    },
    {
        "id": "arch_22",
        "title": "Secondary STEM & Science Educator",
        "grade": 0,
        "exp_years": 6.0,
        "summary": "Secondary Science Educator with 6 years of experience designing high school STEM curricula, directing chemistry laboratory safety protocols, and mentoring student science Olympiad teams.",
        "skills": [
            ("Instruction & STEM", "Chemistry Instruction, Biology Lab Safety, AP Curriculum Design"),
            ("Classroom Tech", "Google Classroom, Canvas LMS, Lab Equipment Management"),
            ("Leadership", "Student Advisory, Science Fair Coordination, Academic Tutoring"),
        ],
        "bullets": [
            "Taught AP Chemistry and Physical Science courses with a 90% exam pass rate.",
            "Coordinated school-wide science laboratory safety protocols and equipment procurement.",
            "Mentored after-school robotics and science Olympiad competition teams.",
        ],
        "degree": "M.Ed. in Secondary Science Education",
    },
    {
        "id": "arch_23",
        "title": "Human Resources & Talent Acquisition Specialist",
        "grade": 0,
        "exp_years": 5.0,
        "summary": "Human Resources Specialist with 5 years of experience managing full-cycle talent acquisition, employee onboarding, benefits administration, and workplace compliance policy enforcement.",
        "skills": [
            ("HR & Talent", "Full-Cycle Recruiting, Talent Sourcing, Employee Onboarding, Benefits"),
            ("HRIS & ATS", "Workday, Greenhouse ATS, LinkedIn Recruiter, BambooHR"),
            ("People Operations", "Employee Relations, Conflict Resolution, HR Compliance"),
        ],
        "bullets": [
            "Recruited and onboarded over 120 professional hires across multiple corporate divisions.",
            "Managed applicant tracking workflows in Greenhouse, reducing time-to-hire by 25%.",
            "Conducted new hire orientation sessions and coordinated annual benefits enrollment.",
        ],
        "degree": "B.S. in Human Resource Management",
    },
    {
        "id": "arch_24",
        "title": "Healthcare & Clinical Operations Coordinator",
        "grade": 0,
        "exp_years": 5.0,
        "summary": "Clinical Operations Coordinator with 5 years of experience managing outpatient medical facility schedules, electronic health record (EHR) compliance, patient care workflows, and billing.",
        "skills": [
            ("Clinical Operations", "EHR/EMR Systems, Patient Scheduling, Medical Billing, HIPAA"),
            ("Software", "Epic Systems, Cerner, Microsoft Office, Medical Records"),
            ("Administration", "Patient Advocacy, Clinical Compliance, Quality Assurance"),
        ],
        "bullets": [
            "Coordinated daily patient care appointments and physician schedules for clinic with 15 providers.",
            "Audited electronic health records ensuring 100% compliance with HIPAA confidentiality guidelines.",
            "Supervised clinical administrative team and reduced patient wait times by 20%.",
        ],
        "degree": "B.S. in Health Services Administration",
    },
    {
        "id": "arch_25",
        "title": "Supply Chain & Logistics Operations Manager",
        "grade": 0,
        "exp_years": 6.0,
        "summary": "Supply Chain and Logistics Manager with 6 years of experience optimizing freight carrier networks, warehouse inventory control, shipment tracking, and vendor contract negotiations.",
        "skills": [
            ("Supply Chain", "Logistics Planning, Freight Management, Warehouse Operations, ERP"),
            ("Software", "SAP SCM, Manhattan Associates WMS, Advanced Excel, Oracle SCM"),
            ("Operations", "Inventory Optimization, Vendor Management, Cost Reduction"),
        ],
        "bullets": [
            "Directed regional distribution operations managing over 50,000 monthly shipment units.",
            "Negotiated transportation contracts resulting in $420K annual logistics savings.",
            "Implemented barcode inventory tracking systems increasing warehouse picking accuracy to 99.4%.",
        ],
        "degree": "B.S. in Supply Chain Management",
    },
]

CITIES = [
    "Seattle, WA", "Atlanta, GA", "Chicago, IL", "Austin, TX", "San Francisco, CA",
    "New York, NY", "Denver, CO", "Philadelphia, PA", "Minneapolis, MN", "Boston, MA",
    "Dallas, TX", "Raleigh, NC", "San Diego, CA", "Washington, DC", "Portland, OR",
    "Phoenix, AZ", "Detroit, MI", "Charlotte, NC", "Nashville, TN", "Baltimore, MD",
    "Salt Lake City, UT", "Columbus, OH", "Indianapolis, IN", "Kansas City, MO", "Pittsburgh, PA",
]


def render_pdf_resume(data: dict, output_path: Path):
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    primary_color = colors.HexColor("#1e3a8a")
    dark_gray = colors.HexColor("#1f2937")
    accent_gray = colors.HexColor("#4b5563")

    name_style = ParagraphStyle(
        "CandName",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=primary_color,
        spaceAfter=2,
    )
    title_style = ParagraphStyle(
        "CandTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=dark_gray,
        spaceAfter=3,
    )
    contact_style = ParagraphStyle(
        "CandContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11.5,
        textColor=accent_gray,
        spaceAfter=8,
    )
    sec_style = ParagraphStyle(
        "CandSec",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13.5,
        textColor=primary_color,
        spaceBefore=7,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "CandBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=dark_gray,
        spaceAfter=3,
    )
    bullet_style = ParagraphStyle(
        "CandBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=dark_gray,
        leftIndent=10,
        spaceAfter=2,
    )
    role_style = ParagraphStyle(
        "CandRole",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=dark_gray,
    )
    period_style = ParagraphStyle(
        "CandPeriod",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=accent_gray,
        alignment=2,
    )

    story = [
        Paragraph(data["name"], name_style),
        Paragraph(data["title"], title_style),
        Paragraph(data["contact"], contact_style),
        HRFlowable(width="100%", thickness=1.5, color=primary_color, spaceAfter=6),
        Paragraph("PROFESSIONAL SUMMARY", sec_style),
        Paragraph(data["summary"], body_style),
        Spacer(1, 2),
        Paragraph("SKILLS & CORE COMPETENCIES", sec_style),
    ]

    for cat, skills_str in data["skills"]:
        story.append(Paragraph(f"<b>{cat}:</b> {skills_str}", body_style))

    story.append(Spacer(1, 2))
    story.append(Paragraph("PROFESSIONAL WORK EXPERIENCE", sec_style))

    for exp in data["experience"]:
        col1 = Paragraph(f"<b>{exp['role']}</b> | {exp['company']}", role_style)
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

    story.append(Paragraph("EDUCATION & CREDENTIALS", sec_style))
    story.append(Paragraph(data["education"], body_style))

    doc.build(story)


def generate_100_pool():
    print("Building 100 CV candidate profiles across 4 intersectional groups...")

    group_prefixes = {
        IntersectionalGroup.BLACK_FEMALE: "bf",
        IntersectionalGroup.BLACK_MALE: "bm",
        IntersectionalGroup.WHITE_FEMALE: "wf",
        IntersectionalGroup.WHITE_MALE: "wm",
    }

    manifest_records = []
    cv_global_index = 1

    for group, group_info in RAW_NAMES_DATA.items():
        g_prefix = group_prefixes[group]
        names = group_info["names"][:25]  # Take 25 distinct names

        for i, name in enumerate(names):
            arch = ARCHETYPES[i]  # 1-to-1 match to archetype (0 to 24)
            city = CITIES[i % len(CITIES)]
            clean_name_slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
            filename = f"cv_{cv_global_index:03d}_{g_prefix}_{clean_name_slug}.pdf"
            pdf_path = OUTPUT_DIR / filename

            email_domain = "techtalent.dev" if arch["grade"] > 0 else "corpmail.org"
            email = f"{clean_name_slug.replace('_', '.')}@{email_domain}"
            phone = f"(555) {100 + cv_global_index:03d}-{1000 + cv_global_index:04d}"
            contact = f"{city} | {email} | {phone} | Verified Candidate"

            company_year = 2026 - int(arch["exp_years"])
            experience = [
                {
                    "role": arch["title"],
                    "company": f"Enterprise Solutions Corp — {city}",
                    "period": f"{company_year + 2} – Present ({int(arch['exp_years']) - 2} yrs)",
                    "bullets": arch["bullets"][:2],
                },
                {
                    "role": f"Associate {arch['title'].split()[0]}",
                    "company": f"Apex Systems Lab — {city}",
                    "period": f"{company_year} – {company_year + 2} (2 yrs)",
                    "bullets": [arch["bullets"][-1]],
                },
            ]

            cv_data = {
                "name": name,
                "title": arch["title"],
                "contact": contact,
                "summary": arch["summary"],
                "skills": arch["skills"],
                "experience": experience,
                "education": f"{arch['degree']} | Accredited University",
            }

            # Generate the actual PDF
            render_pdf_resume(cv_data, pdf_path)

            # Record in manifest
            all_skills_flat = []
            for _, sk_str in arch["skills"]:
                all_skills_flat.extend([s.strip() for s in sk_str.split(",")])

            manifest_records.append({
                "index": cv_global_index,
                "id": f"cand_{cv_global_index:03d}",
                "name": name,
                "group": group.value,
                "relevance_grade": arch["grade"],
                "target_role": arch["title"],
                "experience_years": arch["exp_years"],
                "filename": filename,
                "pdf_path": str(pdf_path),
                "skills_count": len(all_skills_flat),
                "skills": all_skills_flat,
            })

            cv_global_index += 1

    # Save JSON manifest
    manifest_json_path = OUTPUT_DIR / "manifest_100.json"
    with open(manifest_json_path, "w", encoding="utf-8") as f:
        json.dump(manifest_records, f, indent=2, ensure_ascii=False)

    # Save CSV manifest
    manifest_csv_path = OUTPUT_DIR / "manifest_100.csv"
    with open(manifest_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["index", "id", "name", "group", "relevance_grade", "target_role", "experience_years", "filename", "skills_count"]
        )
        writer.writeheader()
        for r in manifest_records:
            row = {k: r[k] for k in writer.fieldnames}
            writer.writerow(row)

    print(f"Success! Generated {len(manifest_records)} PDF resumes.")
    print(f"  -> Manifest JSON: {manifest_json_path}")
    print(f"  -> Manifest CSV:  {manifest_csv_path}")


if __name__ == "__main__":
    generate_100_pool()
