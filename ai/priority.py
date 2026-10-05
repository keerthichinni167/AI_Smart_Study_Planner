
from datetime import date


# =====================================================
# AI PRIORITY CALCULATION
# =====================================================

def calculate_priority(
    marks,
    difficulty,
    exam_date,
    total_topics,
    completed_topics
):
    """
    Calculates the priority score of a subject.

    Higher score = higher study priority.
    """

    # -------------------------------------------------
    # SAFE INPUT CONVERSION
    # -------------------------------------------------

    try:
        marks = float(marks or 0)
    except (ValueError, TypeError):
        marks = 0

    try:
        total_topics = int(total_topics or 0)
    except (ValueError, TypeError):
        total_topics = 0

    try:
        completed_topics = int(completed_topics or 0)
    except (ValueError, TypeError):
        completed_topics = 0

    completed_topics = min(
        max(completed_topics, 0),
        total_topics
    )

    # -------------------------------------------------
    # 1. EXAM PRIORITY
    # -------------------------------------------------

    today = date.today()

    if isinstance(exam_date, str):
        exam_date = date.fromisoformat(exam_date)

    days_left = (exam_date - today).days

    if days_left <= 0:
        exam_score = 40
    elif days_left <= 3:
        exam_score = 40
    elif days_left <= 7:
        exam_score = 35
    elif days_left <= 14:
        exam_score = 28
    elif days_left <= 30:
        exam_score = 20
    elif days_left <= 60:
        exam_score = 10
    else:
        exam_score = 5

    # -------------------------------------------------
    # 2. PERFORMANCE PRIORITY
    # -------------------------------------------------

    if marks < 40:
        performance_score = 30
    elif marks < 50:
        performance_score = 25
    elif marks < 60:
        performance_score = 20
    elif marks < 70:
        performance_score = 15
    elif marks < 80:
        performance_score = 10
    else:
        performance_score = 5

    # -------------------------------------------------
    # 3. DIFFICULTY PRIORITY
    # -------------------------------------------------

    difficulty = str(difficulty or "Medium").lower()

    if difficulty == "hard":
        difficulty_score = 20
    elif difficulty == "medium":
        difficulty_score = 12
    else:
        difficulty_score = 5

    # -------------------------------------------------
    # 4. REMAINING TOPICS PRIORITY
    # -------------------------------------------------

    remaining_topics = max(
        total_topics - completed_topics,
        0
    )

    if total_topics > 0:
        remaining_percentage = (
            remaining_topics / total_topics
        ) * 100

        topic_score = (
            remaining_percentage / 100
        ) * 10
    else:
        remaining_percentage = 0
        topic_score = 0

    # -------------------------------------------------
    # 5. FINAL PRIORITY SCORE
    # -------------------------------------------------

    priority_score = (
        exam_score
        + performance_score
        + difficulty_score
        + topic_score
    )

    priority_score = round(
        priority_score,
        2
    )

    # -------------------------------------------------
    # 6. PRIORITY LEVEL
    # -------------------------------------------------

    if priority_score >= 75:
        priority_level = "HIGH"
    elif priority_score >= 50:
        priority_level = "MEDIUM"
    else:
        priority_level = "LOW"

    # -------------------------------------------------
    # 7. STUDY RECOMMENDATION
    # -------------------------------------------------

    if priority_level == "HIGH":
        recommendation = (
            "Study this subject as soon as possible."
        )
        study_suggestion = (
            "Give this subject more study time "
            "and focus on unfinished topics."
        )

    elif priority_level == "MEDIUM":
        recommendation = (
            "Give regular attention to this subject."
        )
        study_suggestion = (
            "Maintain consistent study sessions "
            "and complete remaining topics."
        )

    else:
        recommendation = (
            "Continue regular revision and practice."
        )
        study_suggestion = (
            "Use shorter revision sessions "
            "to maintain your performance."
        )

    # -------------------------------------------------
    # 8. RETURN AI ANALYSIS
    # -------------------------------------------------

    return {
        "score": priority_score,
        "level": priority_level,
        "days_left": days_left,

        "exam_score": exam_score,
        "performance_score": performance_score,
        "difficulty_score": difficulty_score,
        "topic_score": round(topic_score, 2),

        "remaining_topics": remaining_topics,
        "remaining_percentage": round(
            remaining_percentage,
            2
        ),

        "recommendation": recommendation,
        "study_suggestion": study_suggestion
    }
