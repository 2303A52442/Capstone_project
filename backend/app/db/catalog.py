from sqlalchemy.orm import Session

from app.models.skill import RoleSkill, Skill, TargetRole


SKILLS = [
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

ROLE_REQUIREMENTS = {
    "Software Developer": {"Python": (3.5, 4), "Java": (3.5, 4), "SQL": (3.0, 3), "Testing": (3.0, 3)},
    "Backend Developer": {"Python": (4.0, 5), "SQL": (3.5, 4), "System Design": (4.0, 5), "Testing": (3.0, 3), "Docker": (3.0, 2)},
    "Full Stack Developer": {"JavaScript": (4.0, 5), "React": (3.5, 4), "Python": (3.0, 3), "SQL": (3.0, 3), "Testing": (3.0, 3)},
    "Data Analyst": {"SQL": (4.0, 5), "Excel": (4.0, 4), "Statistics": (3.5, 4), "Pandas": (3.5, 4)},
    "Machine Learning Engineer": {"Python": (4.0, 5), "Statistics": (4.0, 4), "Pandas": (3.5, 4), "TensorFlow": (3.5, 4), "System Design": (3.0, 2)},
    "AI Engineer": {"Python": (4.0, 5), "TensorFlow": (4.0, 5), "NLP": (3.5, 4), "Docker": (3.0, 3), "System Design": (3.5, 4)},
}


def ensure_catalog(db: Session) -> None:
    skills = {}
    for name, category, description in SKILLS:
        skill = db.query(Skill).filter(Skill.name == name).first()
        if skill is None:
            skill = Skill(name=name, category=category, description=description)
            db.add(skill)
            db.flush()
        skills[name] = skill

    for role_name, requirements in ROLE_REQUIREMENTS.items():
        role = db.query(TargetRole).filter(TargetRole.name == role_name).first()
        if role is None:
            role = TargetRole(
                name=role_name,
                domain="Technology",
                description=f"Demo target profile for a {role_name} career path.",
            )
            db.add(role)
            db.flush()

        for skill_name, (required_level, importance) in requirements.items():
            role_skill = db.query(RoleSkill).filter(
                RoleSkill.role_id == role.id,
                RoleSkill.skill_id == skills[skill_name].id,
            ).first()
            if role_skill is None:
                db.add(RoleSkill(
                    role_id=role.id,
                    skill_id=skills[skill_name].id,
                    required_level=required_level,
                    importance=importance,
                ))

    db.commit()
