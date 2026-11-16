# AI Career Twin: Review-2 Readiness

## 1. Problem Statement

Candidate evidence is fragmented across profiles, skills, assessments, projects, interviews, and learning activity. The system connects that evidence to a target role and measures whether recommended actions improve readiness.

## 2. Proposed Solution

AI Career Twin is a structured career-intelligence application. Deterministic scoring and role requirements drive skill gaps and recommendations. LLM features are intentionally deferred to value-add narrative tasks; the Review-2 core does not depend on generated advice.

## 3. System Architecture

- React/Vite frontend
- FastAPI API
- SQLAlchemy persistence
- PostgreSQL for application data
- Alembic migrations
- JWT authentication
- SQLite dependency override for automated API tests

Flow: candidate evidence -> skill state -> role gaps -> recommendation -> action -> outcome -> updated skill state -> next recommendation.

## 4. Database Design

The schema separates users, candidate profiles, skills, role requirements, performance records, projects, recommendations, outcomes, Career Twin snapshots, events, and persisted skill gaps. PostgreSQL setup is provided through Docker Compose and Alembic.

## 5. Candidate Model

A candidate has an authenticated user account, profile attributes, selected target role, skill evidence, performance records, project evidence, recommendation history, and Career Twin history.

## 6. Skill Model

Candidate skill levels use a bounded 0-5 scale. Each skill stores confidence and textual evidence. Role skills store required level and importance.

## 7. Skill-Gap Methodology

`gap = max(0, required_level - current_level)`.

Priority uses the existing deterministic weighting:

`1.5 * gap + 2.0 * importance + 1.2 * recency + 0.8 * confidence`.

## 8. Recommendation Methodology

The next recommendation is selected from the highest-ranked role gap. It includes target skill, reason, activity, expected outcome, effort estimate, and success metric.

## 9. Feedback Loop

1. Candidate selects a role and records evidence.
2. The system generates a role-grounded recommendation.
3. Candidate accepts and completes the action.
4. Before/after outcome evidence is stored.
5. Improvement is converted to the 0-5 scale: percentage-point improvement / 100 * 5.
6. Candidate skill state, persisted gaps, Career Twin snapshot, and event history are updated.
7. The evaluated recommendation remains historical and a new recommendation is generated from the updated state.

Scores from 0-5 are accepted as normalized scores; scores above 5 are treated as percentages. Historical performance and outcomes are never deleted.

## 10. Career Twin Implementation

The Career Twin API returns the candidate summary, selected role, current skills, evidence, strong and weak skills, gaps, performance, recommendation history, outcomes, snapshots, and update events. The frontend visualizes these values and does not use hard-coded metrics.

## 11. Career Comparison

The comparison API accepts two role IDs and returns structured requirements for each role, including candidate level, required level, gap, importance, evidence, and a recommended action. It does not declare a best career.

## 12. Career Simulation

The simulation API accepts temporary skill overrides and returns current versus simulated role gaps and affected skills. It returns `mutated: false`; no candidate record, outcome, snapshot, or event is changed.

## 13. Testing

Implemented checks include:

- Unit smoke test for application startup
- Weighted recommendation ranking regression test
- SQLite API integration test covering registration, login, profile, role selection, skill evidence, recommendation, accept, complete, outcome, skill update, gap persistence, snapshot creation, and next recommendation
- Frontend production build
- Alembic offline PostgreSQL SQL generation
- Browser route validation for authentication entry

## 14. Evaluation Methodology

| Metric | Measurement | Current result | Limitation |
|---|---|---|---|
| Skill-gap calculation | Deterministic formula test cases | Implemented and covered by integration flow | Broader benchmark set is planned |
| Recommendation relevance | Weighted ranking test with controlled role/evidence inputs | Implemented; importance and evidence affect selection | No human-rated relevance dataset yet |
| Before-vs-after improvement | Stored outcome before/after and calculated improvement | Implemented; integration test verifies state change | Demo outcomes are not experimental results |
| Feedback-loop success | End-to-end API state transition test | Passing | PostgreSQL live execution is environment-dependent |
| API response validation | FastAPI route tests and health probe | Passing | Full browser workflow with seeded PostgreSQL remains for live environment |
| Prediction performance | Predictive model metrics | To be evaluated in final phase | No predictive model is required for Review-2 |

## 15. Current Results

The Review-2 core is implemented: authenticated candidate data flows through role-based analysis, recommendation action, measured outcome, skill update, persisted gaps, Career Twin history, and next recommendation. Comparison and simulation use structured role data.

Seed data is explicitly demo data. It is suitable for demonstration and is not evidence of real-world recommendation accuracy or user improvement.

## 16. Current Limitations

- Live PostgreSQL execution could not be run in the current environment because PostgreSQL/Docker was unavailable.
- Performance records are stored and displayed; advanced automatic evidence fusion across every record type is planned.
- Role taxonomy and human relevance evaluation are limited to seeded demonstration data.
- React Router and dependency deprecation warnings remain non-blocking.

## 17. Future Work

- Run PostgreSQL in CI and add migration smoke tests against a disposable database.
- Add richer assessment-to-skill evidence fusion and trend models.
- Add human-rated recommendation relevance studies.
- Add resume/project parsing with reviewable structured extraction.
- Improve frontend code splitting and production deployment.
- Add advanced comparison filters and historical trend charts.
