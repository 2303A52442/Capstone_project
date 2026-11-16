# Database Design Overview

The PostgreSQL schema is normalized around candidate data, skills, target roles, and performance evidence. The most important design goal is to avoid mixing static profile facts with dynamic performance signals.

## Core entities

- users
- candidate_profiles
- skills
- candidate_skills
- target_roles
- role_skills
- projects
- project_skills
- performance_records
- assessment_results
- interviews
- learning_activities
- skill_gaps
- recommendations
- recommendation_outcomes
- career_twin_snapshots
- candidate_events

## Design principles

- one-to-one profile per user
- many-to-many relationships for skills and roles
- timestamps for auditability
- explicit evidence fields for skill updates
- separate records for recommendations and outcomes
