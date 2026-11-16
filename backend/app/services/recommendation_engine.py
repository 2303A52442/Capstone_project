from typing import Iterable

from app.services.skill_analysis import rank_skill_gaps

SKILL_PREREQUISITES: dict[str, str] = {
    "System Design": "SQL",
    "NLP": "Python",
    "TensorFlow": "Python",
    "React": "JavaScript",
    "Pandas": "Python",
    "Docker": "Testing",
}


def generate_recommendation(
    candidate_skill_metrics: Iterable[dict],
    target_role_skills: Iterable[dict],
    previous_outcomes: Iterable[dict] = (),
    recent_performance: Iterable[dict] = (),
) -> dict | None:
    """Select the next most relevant recommendation using role requirement, candidate evidence, and adaptive history."""
    skill_map = {item["skill_name"]: item for item in candidate_skill_metrics}
    previous_outcomes_list = list(previous_outcomes)
    performance_list = list(recent_performance)
    ranked = []

    for role_skill in target_role_skills:
        skill_name = role_skill.get("skill_name")
        candidate = skill_map.get(skill_name, {})
        current = float(candidate.get("current_level", 0))
        required = float(role_skill.get("required_level", 0))
        gap = max(0.0, required - current)
        if gap <= 0:
            continue
        ranked.append({
            "skill_name": skill_name,
            "current_level": current,
            "required_level": required,
            "gap": gap,
            "importance": float(role_skill.get("importance", 1.0)),
            "recency": float(candidate.get("recency", 0.0)),
            "confidence": float(candidate.get("confidence", 0.0)),
            "reason": f"{skill_name} is below the target profile for this role and is limiting readiness.",
        })

    if not ranked:
        return None

    ranked_gaps = rank_skill_gaps(ranked)
    best = ranked_gaps[0]

    # Check for outcomes on this top candidate skill
    skill_outcomes = [item for item in previous_outcomes_list if item.get("target_skill") == best["skill_name"]]
    
    # Check if candidate repeatedly struggled (2+ consecutive non-positive improvements)
    consecutive_stagnant = 0
    for item in reversed(skill_outcomes):
        if float(item.get("improvement", 0)) <= 0:
            consecutive_stagnant += 1
        else:
            break

    # If repeated stagnation on this skill, check for prerequisite weaknesses
    prerequisite_skill = SKILL_PREREQUISITES.get(best["skill_name"])
    if consecutive_stagnant >= 2 and prerequisite_skill:
        # Check if the prerequisite has a gap in the role
        prereq_gap = next((g for g in ranked_gaps if g["skill_name"] == prerequisite_skill), None)
        if prereq_gap:
            best = prereq_gap
            skill_outcomes = [item for item in previous_outcomes_list if item.get("target_skill") == best["skill_name"]]
            strategy_prefix = f"Repeated stagnation on higher-level skill identified prerequisite gap. Focus first on foundational {best['skill_name']}."
        else:
            strategy_prefix = f"Repeated bottleneck on {best['skill_name']} detected. Switching from standard practice to structured diagnostic breakdown with conceptual walkthroughs."
    elif skill_outcomes:
        last_improvement = float(skill_outcomes[-1].get("improvement", 0))
        if last_improvement >= 0.5:
            # Significant improvement: increase difficulty or advance
            if best["gap"] <= 0.5 and len(ranked_gaps) > 1:
                # Move to next priority skill since this gap is nearly closed
                best = ranked_gaps[1]
                strategy_prefix = f"Significant improvement demonstrated on prior skill. Advancing to next role priority: {best['skill_name']}."
            else:
                strategy_prefix = f"Strong prior progress (+{last_improvement:.1f}) verified. Increasing challenge to advanced implementation and comprehensive project-level exercises."
        elif last_improvement <= 0:
            # Stagnant/no improvement: change recommended strategy
            strategy_prefix = f"Prior practice produced limited progress ({last_improvement:+.1f}). Switching approach to interactive diagnostic problem-solving with automated checkpoint validation."
        else:
            strategy_prefix = f"Moderate prior improvement (+{last_improvement:.1f}) recorded. Continue targeted exercises to reach role threshold."
    else:
        strategy_prefix = "Practice with focused exercises and an assessment checkpoint."

    # Look up recent performance matching the target skill
    perf_match = None
    for p in performance_list:
        topic = str(p.get("topic") or p.get("skill_focus") or "").lower()
        if best["skill_name"].lower() in topic:
            perf_match = p
            break

    perf_note = ""
    if perf_match and perf_match.get("score") is not None:
        perf_note = f" Recent performance: {perf_match['score']}%. "

    last_outcome_summary = "No previous outcome recorded."
    if skill_outcomes:
        last_outcome_summary = f"Previous outcome improvement: {skill_outcomes[-1].get('improvement', 0):+.1f}."

    reason_text = (
        f"Current skill: {best['current_level']:.1f}/5. "
        f"Target requirement: {best['required_level']:.1f}/5. "
        f"Gap: {best['gap']:.1f}. "
        f"Role importance: {best['importance']:.1f}. "
        f"Evidence confidence: {best['confidence']:.0%}. "
        f"{perf_note}"
        f"{last_outcome_summary}"
    )

    is_advanced = "advanced" in strategy_prefix.lower()
    is_remedial = "diagnostic" in strategy_prefix.lower() or "foundational" in strategy_prefix.lower()
    suggested_activity = (
        f"Build a production-grade {best['skill_name']} solution and pass an advanced verification assessment."
        if is_advanced
        else f"Complete a guided diagnostic {best['skill_name']} module with step-by-step feedback."
        if is_remedial
        else f"Complete a focused practice set on {best['skill_name']} and take a verification assessment."
    )
    effort_hours = 4.5 if is_advanced else 2.5 if is_remedial else 3.0

    return {
        "target_skill": best["skill_name"],
        "recommendation": f"{strategy_prefix} Target {best['skill_name']}.",
        "reason": reason_text,
        "priority": "High" if best["gap"] >= 1.5 or best["importance"] >= 4.0 else "Medium",
        "expected_outcome": f"Reach at least {best['required_level']} proficiency on {best['skill_name']}.",
        "suggested_activity": suggested_activity,
        "estimated_effort_hours": effort_hours,
        "success_metric": f"Achieve >= {best['required_level']} on the next {best['skill_name']} assessment.",
        "priority_score": best["priority_score"],
        "current_level": best["current_level"],
        "required_level": best["required_level"],
        "gap": best["gap"],
        "importance": best.get("importance", 1),
        "confidence": best.get("confidence", 0),
    }

