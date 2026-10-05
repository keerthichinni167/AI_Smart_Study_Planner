from datetime import date, timedelta, datetime


def generate_study_plan(subjects, available_hours=3):
    if not subjects:
        return []

    try:
        available_hours = int(available_hours)
    except (ValueError, TypeError):
        available_hours = 3

    available_hours = max(1, min(available_hours, 12))

    for subject in subjects:
        try:
            priority = float(subject.get("priority_score", 0) or 0)
        except (ValueError, TypeError):
            priority = 0

        total_topics = int(subject.get("total_topics", 0) or 0)
        completed_topics = int(subject.get("completed_topics", 0) or 0)

        remaining_topics = max(
            total_topics - completed_topics,
            0
        )

        subject["priority_score"] = priority
        subject["remaining_topics"] = remaining_topics

    subjects.sort(
        key=lambda x: x["priority_score"],
        reverse=True
    )

    total_sessions = available_hours * 7

    distribution = {}

    for subject in subjects:
        distribution[subject["subject_id"]] = 1

    remaining_sessions = total_sessions - len(subjects)

    if remaining_sessions > 0:
        total_priority = sum(
            max(subject["priority_score"], 1)
            for subject in subjects
        )

        for subject in subjects:
            weight = (
                max(subject["priority_score"], 1)
                / total_priority
            )

            extra = int(remaining_sessions * weight)

            distribution[subject["subject_id"]] += extra

        while sum(distribution.values()) < total_sessions:
            subject = min(
                subjects,
                key=lambda x: distribution[x["subject_id"]]
            )

            distribution[subject["subject_id"]] += 1

    queue = []

    for subject in subjects:
        count = distribution[subject["subject_id"]]

        for _ in range(count):
            queue.append(subject)

    plan = []
    today = date.today()
    session_index = 0

    for day in range(7):
        study_date = today + timedelta(days=day)

        for session in range(available_hours):
            subject = queue[session_index % len(queue)]

            if subject["remaining_topics"] > 0:
                topic = (
                    "Study remaining topics "
                    f"({subject['remaining_topics']} left)"
                )
            else:
                topic = "Revision and practice"

            start_time = datetime(
                study_date.year,
                study_date.month,
                study_date.day,
                17 + session,
                0
            )

            end_time = start_time + timedelta(hours=1)

            plan.append({
                "study_date": study_date,
                "subject_id": subject["subject_id"],
                "subject_name": subject["subject_name"],
                "topic": topic,
                "priority_score": subject["priority_score"],
                "start_time": start_time.time(),
                "end_time": end_time.time(),
                "status": "Pending"
            })

            session_index += 1

    return plan
