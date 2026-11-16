# AI Career Twin

AI Career Twin is a full-stack career intelligence platform that models a candidate as a dynamic skill profile rather than a static resume. The platform combines structured performance tracking, skill-gap analysis, recommendation generation, and a continuous feedback loop so a candidate can improve toward a target role with measurable outcomes.

## Problem Statement

Students and early-career professionals often have fragmented evidence of skill readiness. Their resumes, project history, self-assessment, coding scores, interview feedback, and learning activity are often not connected into a single decision engine. As a result, recommendations are generic, skill gaps are unclear, and progress is not measured in a practical, role-based way.

## Objectives

- Build a complete candidate profiling system with static and dynamic evidence separation.
- Model a structured Career Twin that changes over time with new performance data.
- Detect skill gaps against realistic target-role requirements.
- Recommend the next most relevant learning or career action based on evidence.
- Track recommendation outcomes and update the candidate model with real improvements.
- Demonstrate the continuous feedback loop across profile, skill analysis, recommendation, and outcome measurement.

## Proposed Solution

The system uses:

- A relational PostgreSQL database for normalized candidate and role data.
- A FastAPI backend with Pydantic validation and SQLAlchemy models.
- A deterministic skill scoring and gap methodology for interpretable recommendations.
- A recommendation engine grounded in structured candidate evidence.
- A lightweight AI/LLM layer for resume parsing, narrative explanation, and unstructured summarization only when it adds value.
- A React frontend that visualizes the career twin, skill readiness, recent performance, and recommendation lifecycle.

## Architecture

```text
frontend/
  src/
    components/
    pages/
    services/
    hooks/
    charts/
    contexts/
    utils/

backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    ai/
    recommendation/
    skill_analysis/
    utils/

tests/
docs/
```

## Technology Stack

- Frontend: React + Vite + JavaScript/TypeScript
- Backend: Python + FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Validation: Pydantic
- Authentication: JWT and bcrypt/argon2 hashing
- ML: scikit-learn for optional analytics and trend evaluation
- AI: OpenAI-compatible LLM integration for resume extraction and explanations
- Vector memory: optional embeddings for unstructured resume/project notes
- Testing: pytest
- Containerization: Docker Compose (optional)

## Database Design

A normalized schema separates:

- user account and profile data
- static profile data vs dynamic performance data
- skills and targets
- projects and evidence
- assessments and recommendation outcomes
- snapshots and event history

The database is designed for future extensibility, role benchmarking, and audit-friendly progress tracking.

## AI/ML Approach

AI/ML is used only where it provides real value:

- Deterministic algorithms: skill scoring, gap detection, priority ranking, recommendation selection
- LLM usage: resume/project analysis, explanation generation, summary writing, natural-language recommendation framing
- ML/trend evaluation: optional predictive analytics or learning-behavior trend models, if meaningful

The goal is to avoid fake ML and ensure the system is explainable and defensible.

## Skill Scoring Methodology

Each skill score is computed using weighted evidence from multiple sources:

- assessment performance
- coding performance
- project evidence
- interview performance
- learning completion
- recent activity recency

A sample formula:

skill_score = 0.35 * assessment + 0.25 * coding + 0.20 * project + 0.10 * interview + 0.10 * learning

Recent performance is weighted more strongly using a recency factor, so fresh evidence matters more than historical activity.

The scale is:

- 0 = No evidence
- 1 = Beginner
- 2 = Basic
- 3 = Intermediate
- 4 = Advanced
- 5 = Strong

## Skill Gap Methodology

Skill gaps are calculated as:

gap = max(0, required_level - current_level)

The recommendation priority considers:

- gap magnitude
- role importance
- evidence confidence
- recency of performance
- dependency relationships between related skills

## Recommendation Methodology

The recommendation engine ranks the next best action using structured candidate data, not generic advice. It considers:

- current skill levels
- target role constraints
- historical assessment outcomes
- recent learning progress
- evidence of performance weakness
- prior recommendation outcomes

A recommendation can include:

- target skill
- reason
- expected outcome
- estimated effort
- success metric
- status lifecycle

## Feedback Loop

The central contribution of the project is the continuous feedback loop:

1. Candidate profile and performance data are collected.
2. Skill scoring and gap analysis update the Career Twin.
3. Recommendations are generated for the most relevant skill gap.
4. The user accepts and completes the action.
5. Outcome is recorded with before/after evidence.
6. Skill scores and the Career Twin are updated.
7. The next recommendation is generated from the updated state.

## Setup Instructions

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Database

- Create a PostgreSQL database
- Update environment variables in a .env file
- Run migrations with `alembic upgrade head` from the `backend` directory
- Seed a local demo candidate with `python seed.py` from the `backend` directory

The seed creates `demo_user` with password `demo123`, a Backend Developer target
role, structured skill evidence, and an initial recommendation. The operation is
idempotent and can be rerun during development.

For a fresh database:

```bash
cd backend
alembic upgrade head
python seed.py
```

## Environment Variables

Create a .env file with values such as:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/ai_career_twin
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
OPENAI_API_KEY=
VECTOR_DB_URL=
```

## API Documentation

FastAPI automatically serves Swagger UI at:

- http://localhost:8000/docs
- http://localhost:8000/redoc

## Testing

```bash
cd backend
pytest
```

## Core Workflow API

After registration and profile creation, the candidate workflow is:

1. `GET /roles` lists available target roles.
2. `PUT /roles/{role_id}/select` selects the candidate's target role.
3. `PUT /skills/candidate` records structured skill evidence.
4. `POST /recommendations/generate` ranks current gaps and persists the next recommendation.
5. `POST /recommendations/{recommendation_id}/accept` and `/complete` track progress.
6. `POST /recommendations/{recommendation_id}/outcome` records before/after evidence.
7. `GET /dashboard` returns live readiness, skill gaps, snapshots, and active recommendation counts.

## Evaluation Methodology

The project is designed for later evaluation of:

- skill-gap detection quality
- recommendation relevance
- user improvement over time
- system explainability
- actual measured feedback-loop effectiveness



## Limitations

- This version focuses on a working end-to-end prototype with realistic logic, not production-scale ML orchestration.
- Resume parsing and LLM behavioral explanation require external API access and human review.
- Recommendation quality depends on the quality of candidate evidence and role skill metadata.

## Future Work

- richer role taxonomy
- more advanced skill inference
- better predictive modeling
- advanced recommendation personalization
- richer analytics and cohort comparison

---


