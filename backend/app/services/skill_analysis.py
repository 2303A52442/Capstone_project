from typing import Iterable


def calculate_skill_level(assessment_score: float = 0, coding_score: float = 0, project_score: float = 0,
                          interview_score: float = 0, learning_score: float = 0, recency_factor: float = 1.0) -> float:
    """Weighted skill scoring method with recency factor to prioritize recent evidence."""
    weighted_score = (
        0.35 * assessment_score +
        0.25 * coding_score +
        0.20 * project_score +
        0.10 * interview_score +
        0.10 * learning_score
    )
    return round(min(max((weighted_score * recency_factor), 0), 5), 2)


def calculate_skill_gap(current_level: float, required_level: float) -> float:
    """Gap is the shortfall between current ability and required role level."""
    return round(max(0.0, required_level - current_level), 2)


def rank_skill_gaps(gaps: Iterable[dict]) -> list[dict]:
    """Prioritize gaps by size, role importance, recency, and dependencies."""
    ranked = []
    for gap in gaps:
        priority_score = (
            float(gap.get("gap", 0)) * 1.5 +
            float(gap.get("importance", 0)) * 2.0 +
            float(gap.get("recency", 0)) * 1.2 +
            float(gap.get("confidence", 0)) * 0.8
        )
        gap_copy = dict(gap)
        gap_copy["priority_score"] = round(priority_score, 2)
        ranked.append(gap_copy)
    return sorted(ranked, key=lambda item: item["priority_score"], reverse=True)
