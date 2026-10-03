"""Synthetic evaluation dataset for Job Matching Engine.

Contains realistic test cases for:
1. Strong match
2. Partial match
3. Weak match
4. Semantically related wording
5. Exact keyword mismatch but semantic match
6. Misleading keyword occurrence (negative constraints)
"""

EVALUATION_DATASET = {
    "strong_match": {
        "job": {
            "title": "Senior Backend Engineer",
            "company": "ScaleGrid",
            "raw_text": """About the Role:
ScaleGrid is looking for a Senior Backend Engineer to build high-performance distributed systems.

Responsibilities:
- Build and maintain REST APIs using FastAPI and Python.
- Architect high-throughput data processing workflows with PostgreSQL and Redis.
- Collaborate with platform engineers on cloud deployments.

Requirements:
- 5+ years of experience in backend software engineering.
- Deep expertise in Python and FastAPI.
- Strong proficiency with PostgreSQL and Redis caching.
- Experience with Docker containerization.

Preferred Qualifications:
- Familiarity with Kubernetes and microservices architecture.
- Experience with Kafka or message queues.
""",
        },
        "candidate": {
            "full_name": "Jordan Lee",
            "headline": "Senior Backend & Distributed Systems Engineer",
            "years_of_experience": 6.0,
            "skills": [
                {"name": "Python", "category": "TECHNICAL", "proficiency": "EXPERT"},
                {"name": "FastAPI", "category": "TECHNICAL", "proficiency": "EXPERT"},
                {"name": "PostgreSQL", "category": "TECHNICAL", "proficiency": "ADVANCED"},
                {"name": "Redis", "category": "TECHNICAL", "proficiency": "ADVANCED"},
                {"name": "Docker", "category": "TECHNICAL", "proficiency": "ADVANCED"},
                {"name": "Microservices", "category": "TECHNICAL", "proficiency": "INTERMEDIATE"},
            ],
            "experiences": [
                {
                    "company": "Nexus Systems",
                    "title": "Senior Backend Developer",
                    "description": "Engineered distributed microservices using FastAPI, Python, and PostgreSQL.",
                    "achievements": [
                        "Optimized Redis cache hit ratio from 65% to 94%, reducing query latencies by 60ms.",
                        "Containerized backend microservices using Docker and orchestrated deployments.",
                    ],
                }
            ],
            "projects": [
                {
                    "name": "Cloud Telemetry Pipeline",
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker"],
                    "description": "High-throughput data ingestion pipeline handling 50k events per second.",
                }
            ],
        },
    },
    "partial_match": {
        "job": {
            "title": "Full Stack Platform Engineer",
            "company": "VentureApp",
            "raw_text": """Responsibilities:
- Develop modern web interfaces and scalable backend services.

Requirements:
- 3+ years of web application development.
- Strong proficiency with React and TypeScript.
- Experience with Node.js backend services.
- Production experience with Kubernetes cluster management.

Preferred Qualifications:
- Experience with GraphQL APIs.
- Familiarity with AWS infrastructure.
""",
        },
        "candidate": {
            "full_name": "Morgan Davis",
            "headline": "Frontend-leaning Full Stack Engineer",
            "years_of_experience": 4.0,
            "skills": [
                {"name": "React", "category": "TECHNICAL"},
                {"name": "TypeScript", "category": "TECHNICAL"},
                {"name": "Next.js", "category": "TECHNICAL"},
                {"name": "Node.js", "category": "TECHNICAL"},
                {"name": "AWS", "category": "TECHNICAL"},
            ],
            "experiences": [
                {
                    "company": "PixelCraft",
                    "title": "Full Stack Developer",
                    "description": "Built user interfaces in React/TypeScript and backend services in Node.js on AWS.",
                }
            ],
            "projects": [
                {
                    "name": "E-Commerce Webapp",
                    "technologies": ["React", "TypeScript", "Node.js"],
                    "description": "Server-side rendered web store deployed on AWS cloud.",
                }
            ],
        },
    },
    "weak_match": {
        "job": {
            "title": "Senior iOS Engineer",
            "company": "MobileFirst",
            "raw_text": """Requirements:
- 5+ years of native mobile iOS development.
- Expert knowledge of Swift, SwiftUI, and Objective-C.
- Strong grasp of CoreData and Apple iOS SDK.
- Experience shipping apps to the Apple App Store.
""",
        },
        "candidate": {
            "full_name": "Sam Taylor",
            "headline": "Data Scientist & ML Engineer",
            "years_of_experience": 3.0,
            "skills": [
                {"name": "Python", "category": "TECHNICAL"},
                {"name": "PyTorch", "category": "TECHNICAL"},
                {"name": "SQL", "category": "TECHNICAL"},
                {"name": "Pandas", "category": "TECHNICAL"},
            ],
            "experiences": [
                {
                    "company": "DataCorp",
                    "title": "Machine Learning Specialist",
                    "description": "Trained predictive regression models and neural networks using PyTorch.",
                }
            ],
            "projects": [
                {
                    "name": "Customer Churn Predictor",
                    "technologies": ["Python", "PyTorch", "Pandas"],
                    "description": "Machine learning system forecasting subscription cancellations.",
                }
            ],
        },
    },
    "semantically_related_wording": {
        "job": {
            "title": "DevOps Engineer",
            "company": "CloudNative",
            "raw_text": """Requirements:
- Proven experience with container orchestration and cluster scaling.
- Automated infrastructure provisioning via code.
- Continuous deployment automation.
""",
        },
        "candidate": {
            "full_name": "Alex Chen",
            "headline": "Cloud Infrastructure Engineer",
            "years_of_experience": 5.0,
            "skills": [
                {"name": "Kubernetes", "category": "TECHNICAL"},
                {"name": "Docker", "category": "TECHNICAL"},
                {"name": "Terraform", "category": "TECHNICAL"},
                {"name": "CI/CD", "category": "TECHNICAL"},
            ],
            "experiences": [
                {
                    "company": "InfraStack",
                    "title": "DevOps Specialist",
                    "description": "Automated AWS infrastructure with Terraform and managed multi-tenant Kubernetes clusters.",
                }
            ],
            "projects": [
                {
                    "name": "Automated GitOps Pipeline",
                    "technologies": ["Kubernetes", "Terraform", "GitHub Actions"],
                    "description": "Zero-downtime continuous deployment pipeline managing 40 microservice clusters.",
                }
            ],
        },
    },
    "misleading_keyword_negative_constraint": {
        "job": {
            "title": "Go Distributed Systems Developer",
            "company": "FastNetwork",
            "raw_text": """Note: We are NOT looking for Java or C# developers for this role.
Requirements:
- 4+ years of Go (Golang) programming experience.
- Distributed consensus algorithms (Raft or Paxos).
- Experience building networking proxies and gRPC services.
""",
        },
        "candidate": {
            "full_name": "Devin Smith",
            "headline": "Java Backend Developer",
            "years_of_experience": 4.0,
            "skills": [
                {"name": "Java", "category": "TECHNICAL"},
                {"name": "Spring Boot", "category": "TECHNICAL"},
                {"name": "MySQL", "category": "TECHNICAL"},
            ],
            "experiences": [
                {
                    "company": "LegacyEnterprise",
                    "title": "Java Software Engineer",
                    "description": "Built monolithic applications using Java and Spring Boot.",
                }
            ],
            "projects": [],
        },
    },
}

