from collections.abc import Iterable


def _to_skill_level(score: float | None) -> float:
    if score is None:
        return 0.0
    value = float(score)
    if value <= 5:
        return value
    if 5 < value <= 100:
        return value / 20
    return value


def _get_value(item, key):
    """Extract a value from either a dict or an object."""
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def calculate_evaluation_metrics(
    recommendations: Iterable,
    outcomes: Iterable,
    current_gaps: Iterable,
    role_requirements: Iterable,
) -> dict:
    recommendations = list(recommendations)
    outcomes = list(outcomes)
    current_gaps = list(current_gaps)

    requirements = {}
    for item in role_requirements:
        name = _get_value(item, "name") or getattr(item, "skill", None).name if getattr(item, "skill", None) else None
        required_level = _get_value(item, "required_level")
        if required_level is None:
            required_level = getattr(item, "required_level", None)
        if name and required_level is not None:
            requirements[name] = float(required_level)

    total_recommendations = len(recommendations)
    completed_recommendations = sum(1 for item in recommendations if item.status in {"completed", "evaluated"})
    completion_rate = round((completed_recommendations / total_recommendations) * 100, 1) if total_recommendations else None

    skill_improvements = []
    improvements = []
    before_after_rows = []
    for item in outcomes:
        recommendation = getattr(item, "recommendation", None)
        target_skill = getattr(recommendation, "target_skill", None) or getattr(item, "target_skill", None)
        before_score = _to_skill_level(_get_value(item, "before_score") or getattr(item, "before_score", 0))
        after_score = _to_skill_level(_get_value(item, "after_score") or getattr(item, "after_score", 0))
        improvement = float(after_score - before_score)
        if target_skill is None:
            target_skill = getattr(item, "target_skill", None)
        if target_skill is not None:
            skill_improvements.append({
                "recommendation_id": getattr(item, "recommendation_id", None),
                "target_skill": target_skill,
                "before_score": before_score,
                "after_score": after_score,
                "improvement": round(improvement, 2),
            })
            before_after_rows.append({
                "recommendation_id": getattr(item, "recommendation_id", None),
                "target_skill": target_skill,
                "before_score": round(before_score, 2),
                "after_score": round(after_score, 2),
                "improvement": round(improvement, 2),
            })
        improvements.append(improvement)

    successful_outcomes = sum(1 for improvement in improvements if improvement > 0)
    average_skill_improvement = round(sum(improvements) / len(improvements), 2) if improvements else None

    identified_skill_gaps = sum(1 for item in current_gaps if float(_get_value(item, "gap") or 0) > 0)
    improved_gaps = 0
    resolved_gaps = 0
    for outcome in outcomes:
        recommendation = getattr(outcome, "recommendation", None)
        target_skill = getattr(recommendation, "target_skill", None)
        required = requirements.get(target_skill)
        if required is None:
            continue
        before_level = _to_skill_level(getattr(outcome, "before_score", 0))
        after_level = _to_skill_level(getattr(outcome, "after_score", 0))
        before_gap = max(0.0, required - before_level)
        after_gap = max(0.0, required - after_level)
        if before_gap > 0 and after_gap < before_gap:
            improved_gaps += 1
        if before_gap > 0 and after_gap == 0:
            resolved_gaps += 1

    return {
        "total_recommendations": total_recommendations,
        "completed_recommendations": completed_recommendations,
        "recommendation_completion_rate": completion_rate,
        "successful_outcomes": successful_outcomes,
        "skill_improvements": skill_improvements,
        "average_skill_improvement": average_skill_improvement,
        "identified_skill_gaps": identified_skill_gaps,
        "total_identified_skill_gaps": identified_skill_gaps,
        "improved_skill_gaps": improved_gaps,
        "resolved_skill_gaps": resolved_gaps,
        "before_after_skill_levels": before_after_rows,
    }
