import os
from typing import Optional


def generate_recommendation_explanation(
    target_skill: str,
    current_level: float,
    required_level: float,
    gap: float,
    importance: float,
    confidence: float,
    recent_performance_score: Optional[float] = None,
    previous_improvement: Optional[float] = None,
    candidate_name: str = "you",
) -> str:
    """Generate a natural-language explanation for a recommendation using an LLM or fallback deterministic text."""
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not openai_key:
        return _generate_fallback_explanation(
            target_skill, current_level, required_level, gap, importance, confidence,
            recent_performance_score, previous_improvement, candidate_name
        )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        prompt = f"""Generate a brief, personalized career recommendation explanation for {candidate_name}.

Skill: {target_skill}
Current level: {current_level}/5
Target requirement: {required_level}/5
Gap: {gap}
Role importance of this skill: {importance}
Confidence in current level estimate: {confidence}
Recent performance score: {recent_performance_score}
Previous improvement from this skill: {previous_improvement}

Explain why {target_skill} is the recommended next focus, considering the gap size, importance, and evidence quality. Keep it under 2 sentences. Do not invent skill levels or claims not in the data."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _generate_fallback_explanation(
            target_skill, current_level, required_level, gap, importance, confidence,
            recent_performance_score, previous_improvement, candidate_name
        )


def _generate_fallback_explanation(
    target_skill: str,
    current_level: float,
    required_level: float,
    gap: float,
    importance: float,
    confidence: float,
    recent_performance_score: Optional[float] = None,
    previous_improvement: Optional[float] = None,
    candidate_name: str = "you",
) -> str:
    """Generate a deterministic explanation when no LLM is available."""
    gap_desc = "significant" if gap >= 1.5 else "moderate" if gap >= 0.5 else "small"
    confidence_desc = "strong" if confidence >= 0.7 else "moderate" if confidence >= 0.5 else "limited"

    base = f"{target_skill} is a {gap_desc} gap between your current level ({current_level:.1f}) and the requirement ({required_level:.1f})."
    importance_note = f" With role importance {importance:.1f}, closing this gap is critical for your career goal." if importance >= 3 else ""
    evidence_note = f" Your {confidence_desc} evidence ({confidence:.0%} confidence) supports focused practice."
    performance_note = f" Recent performance ({recent_performance_score}%) indicates immediate room for growth." if recent_performance_score and recent_performance_score < 70 else ""
    outcome_note = f" Prior outcome recorded an improvement of {previous_improvement:+0.1f}." if previous_improvement is not None else ""

    return f"{base}{importance_note} {evidence_note}{performance_note}{outcome_note}".strip()


def generate_career_twin_summary(
    candidate_name: str,
    target_role: Optional[str],
    readiness_score: float,
    strong_skills: list[str],
    weak_skills: list[str],
) -> str:
    """Generate a personalized narrative Career Twin summary using LLM or deterministic fallback."""
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()

    if not openai_key:
        return _generate_fallback_summary(candidate_name, target_role, readiness_score, strong_skills, weak_skills)

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        prompt = f"""Provide a concise 2-sentence executive summary for {candidate_name}'s Career Twin.
Target Role: {target_role or 'Unassigned'}
Readiness Score: {readiness_score}%
Strong skills: {', '.join(strong_skills) or 'None yet'}
Gaps to close: {', '.join(weak_skills) or 'None'}
Strict rule: Do not invent numbers or new skills."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return _generate_fallback_summary(candidate_name, target_role, readiness_score, strong_skills, weak_skills)


def _generate_fallback_summary(
    candidate_name: str,
    target_role: Optional[str],
    readiness_score: float,
    strong_skills: list[str],
    weak_skills: list[str],
) -> str:
    role_str = f" for the {target_role} path" if target_role else ""
    status = "strong readiness" if readiness_score >= 80 else "steady progress" if readiness_score >= 50 else "early-stage development"
    strong_str = f" Anchored by solid proficiency in {', '.join(strong_skills[:3])}." if strong_skills else ""
    weak_str = f" Key focus areas to bridge are {', '.join(weak_skills[:3])}." if weak_skills else " All primary competencies currently meet role criteria."
    return f"{candidate_name} exhibits {status}{role_str} at {readiness_score:.1f}% readiness.{strong_str}{weak_str}"


def generate_career_comparison_explanation(
    candidate_name: str,
    role_a_name: str,
    role_a_gaps: list[dict],
    role_b_name: str,
    role_b_gaps: list[dict],
) -> str:
    """Generate a comparative analysis between two career paths."""
    gap_a_sum = sum(g.get("gap", 0) for g in role_a_gaps)
    gap_b_sum = sum(g.get("gap", 0) for g in role_b_gaps)

    closer_role = role_a_name if gap_a_sum <= gap_b_sum else role_b_name
    return (
        f"Comparative Analysis for {candidate_name}: You have a shorter gap trajectory toward {closer_role} "
        f"(total cumulative gap: {min(gap_a_sum, gap_b_sum):.1f}) compared to "
        f"{role_b_name if closer_role == role_a_name else role_a_name} (total cumulative gap: {max(gap_a_sum, gap_b_sum):.1f}). "
        f"Prioritizing high-importance overlapping skills accelerates progress across both paths."
    )
