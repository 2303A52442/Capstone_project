"""Seed a local AI Career Twin database with a usable demo candidate."""

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.candidate_profile import CandidateProfile
from app.models.performance import AssessmentResult, PerformanceRecord
from app.models.projects import Project, ProjectSkill
from app.models.recommendation import Recommendation, RecommendationOutcome
from app.models.skill import CandidateSkill, CandidateTargetRole, RoleSkill, Skill, TargetRole
from app.models.user import User
from app.services.career_twin_service import refresh_candidate_state
from app.services.recommendation_engine import generate_recommendation

# Import remaining model modules so their tables and relationships are registered.
from app.models import career_twin, performance, projects  # noqa: F401, E402


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "demo_user").first()
        if user is None:
            user = User(
                email="candidate@example.com",
                username="demo_user",
                full_name="Demo Candidate",
                hashed_password=hash_password("demo123"),
            )
            db.add(user)
            db.flush()

        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if profile is None:
            profile = CandidateProfile(
                user_id=user.id,
                name="Demo Candidate",
                education="Computer Science",
                degree="BSc",
                specialization="Backend Engineering",
                graduation_year=2026,
                career_goal="Backend Developer",
                bio="Seeded candidate for local development and demonstrations.",
            )
            db.add(profile)
            db.flush()

        skill_data = [
            ("Python", "Programming", "Backend application development"),
            ("SQL", "Data", "Relational data modeling and querying"),
            ("System Design", "Architecture", "Designing reliable backend systems"),
            ("Testing", "Engineering", "Automated testing and quality practices"),
            ("Java", "Programming", "Object-oriented application development"),
            ("JavaScript", "Programming", "Web application programming"),
            ("React", "Frontend", "Component-based frontend development"),
            ("Excel", "Analytics", "Spreadsheet analysis and reporting"),
            ("Statistics", "Analytics", "Statistical reasoning and analysis"),
            ("Pandas", "Data", "Data manipulation and analysis"),
            ("TensorFlow", "Machine Learning", "Neural network development"),
            ("NLP", "Machine Learning", "Natural language processing"),
            ("Docker", "DevOps", "Containerized application delivery"),
        ]
        skills = {}
        for name, category, description in skill_data:
            skill = db.query(Skill).filter(Skill.name == name).first()
            if skill is None:
                skill = Skill(name=name, category=category, description=description)
                db.add(skill)
                db.flush()
            skills[name] = skill

        role_requirements = {
            "Software Developer": {"Python": (3.5, 4), "Java": (3.5, 4), "SQL": (3.0, 3), "Testing": (3.0, 3)},
            "Backend Developer": {"Python": (4.0, 5), "SQL": (3.5, 4), "System Design": (4.0, 5), "Testing": (3.0, 3), "Docker": (3.0, 2)},
            "Full Stack Developer": {"JavaScript": (4.0, 5), "React": (3.5, 4), "Python": (3.0, 3), "SQL": (3.0, 3), "Testing": (3.0, 3)},
            "Data Analyst": {"SQL": (4.0, 5), "Excel": (4.0, 4), "Statistics": (3.5, 4), "Pandas": (3.5, 4)},
            "Machine Learning Engineer": {"Python": (4.0, 5), "Statistics": (4.0, 4), "Pandas": (3.5, 4), "TensorFlow": (3.5, 4), "System Design": (3.0, 2)},
            "AI Engineer": {"Python": (4.0, 5), "TensorFlow": (4.0, 5), "NLP": (3.5, 4), "Docker": (3.0, 3), "System Design": (3.5, 4)},
        }
        roles = {}
        for role_name, requirements in role_requirements.items():
            role = db.query(TargetRole).filter(TargetRole.name == role_name).first()
            if role is None:
                role = TargetRole(name=role_name, domain="Technology", description=f"Demo target profile for a {role_name} career path.")
                db.add(role)
                db.flush()
            roles[role_name] = role
            for name, (required_level, importance) in requirements.items():
                role_skill = db.query(RoleSkill).filter(RoleSkill.role_id == role.id, RoleSkill.skill_id == skills[name].id).first()
                if role_skill is None:
                    db.add(RoleSkill(role_id=role.id, skill_id=skills[name].id, required_level=required_level, importance=importance))

        role = roles["Backend Developer"]
        requirements = role_requirements["Backend Developer"]

        target = db.query(CandidateTargetRole).filter(
            CandidateTargetRole.candidate_profile_id == profile.id,
        ).first()
        if target is None:
            db.add(CandidateTargetRole(candidate_profile_id=profile.id, role_id=role.id))

        evidence = {
            "Python": (3.8, 0.9, "Built FastAPI services and automation scripts"),
            "SQL": (3.1, 0.85, "Completed relational query and schema exercises"),
            "System Design": (2.0, 0.7, "Reviewed API architecture patterns"),
            "Testing": (3.2, 0.8, "Maintained pytest regression coverage"),
            "Java": (2.8, 0.6, "Completed object-oriented programming coursework"),
            "JavaScript": (2.4, 0.6, "Built browser interaction exercises"),
            "React": (2.2, 0.55, "Created component-based interfaces"),
            "Excel": (2.5, 0.6, "Used spreadsheets for data summaries"),
            "Statistics": (2.3, 0.55, "Studied descriptive statistics"),
            "Pandas": (2.5, 0.65, "Completed dataframe analysis exercises"),
            "TensorFlow": (1.5, 0.4, "Explored neural network tutorials"),
            "NLP": (1.2, 0.35, "Read introductory NLP material"),
            "Docker": (1.8, 0.5, "Ran local services in containers"),
        }
        for name, (level, confidence, description) in evidence.items():
            candidate_skill = db.query(CandidateSkill).filter(
                CandidateSkill.candidate_profile_id == profile.id,
                CandidateSkill.skill_id == skills[name].id,
            ).first()
            if candidate_skill is None:
                db.add(CandidateSkill(
                    candidate_profile_id=profile.id,
                    skill_id=skills[name].id,
                    current_level=level,
                    confidence=confidence,
                    evidence=description,
                ))

        db.commit()

        if not db.query(Project).filter(Project.candidate_profile_id == profile.id).first():
            project = Project(
                candidate_profile_id=profile.id,
                name="Career Twin Platform",
                description="A data-backed career intelligence platform with a measurable feedback loop.",
                domain="Software Engineering",
                technologies=["Python", "FastAPI", "React", "PostgreSQL"],
                role_responsibility="Designed the API workflow and recommendation lifecycle.",
            )
            db.add(project)
            db.flush()
            db.add_all([ProjectSkill(project_id=project.id, skill_name="Python", evidence_strength=4), ProjectSkill(project_id=project.id, skill_name="System Design", evidence_strength=3)])

        if not db.query(PerformanceRecord).filter(PerformanceRecord.candidate_profile_id == profile.id).first():
            performance = PerformanceRecord(candidate_profile_id=profile.id, record_type="assessment", topic="SQL joins assessment", score=62, difficulty="medium", attempts=1, notes="Demo baseline assessment")
            db.add(performance)
            db.flush()
            db.add(AssessmentResult(performance_record_id=performance.id, total_questions=20, correct_answers=12, score_percent=62, skill_focus="SQL"))
            db.commit()

        metrics = [
            {"skill_name": name, "current_level": level, "confidence": confidence, "recency": 1.0}
            for name, (level, confidence, _) in evidence.items()
        ]
        role_skills = [
            {"skill_name": name, "required_level": required, "importance": importance}
            for name, (required, importance) in requirements.items()
        ]
        recommendation_data = generate_recommendation(metrics, role_skills)
        if recommendation_data and not db.query(Recommendation).filter(
            Recommendation.candidate_profile_id == profile.id,
            Recommendation.status == "generated",
        ).first():
            db.add(Recommendation(
                candidate_profile_id=profile.id,
                target_skill=recommendation_data["target_skill"],
                recommendation_text=recommendation_data["recommendation"],
                reason=recommendation_data["reason"],
                priority=2 if recommendation_data["priority"] == "High" else 1,
                expected_outcome=recommendation_data["expected_outcome"],
                suggested_activity=recommendation_data["suggested_activity"],
                estimated_effort_hours=recommendation_data["estimated_effort_hours"],
                success_metric=recommendation_data["success_metric"],
            ))
            db.commit()

        generated = db.query(Recommendation).filter(
            Recommendation.candidate_profile_id == profile.id,
            Recommendation.status == "generated",
        ).first()
        if generated and not db.query(RecommendationOutcome).filter(RecommendationOutcome.recommendation_id == generated.id).first():
            generated.status = "evaluated"
            db.add(RecommendationOutcome(
                recommendation_id=generated.id,
                accepted=True,
                completed=True,
                recommendation_followed=True,
                before_score=50,
                after_score=70,
                improvement=20,
                completion_status="evaluated",
                outcome_notes="Demo outcome data for Review-2 demonstration.",
            ))
            db.commit()
            try:
                refresh_candidate_state(db, profile, generated.target_skill, 50, 70, "Demo outcome data; not an experimental result.")
                db.commit()
            except ValueError:
                db.rollback()

        print("Seeded demo_user / demo123 with Backend Developer role data.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
