# Architecture Overview

The AI Career Twin is organized as a monorepo with a Python FastAPI backend and a React frontend. The backend handles candidate data, role metadata, performance events, and recommendation logic. The frontend presents the dashboard and application flows in a clean career-intelligence interface.

## Backend responsibilities

- API routing and auth
- business logic and validation
- data access through SQLAlchemy
- deterministic skill analysis and recommendation ranking
- optional AI summarization and resume extraction integrations

## Frontend responsibilities

- login and registration flows
- onboarding and profile management
- dashboard data visualization
- Career Twin and recommendations experience
- career comparison and simulation

## Why the design matters

This project separates static profile evidence from dynamic performance evidence and gives the recommendation engine a grounded basis for action. The feedback loop is central and is explicitly modeled through status transitions across recommendations and updated skill evidence.
