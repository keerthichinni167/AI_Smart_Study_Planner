from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

import mysql.connector
import os

from datetime import date, timedelta, datetime, time

from ai.priority import calculate_priority
from ai.planner import generate_study_plan


# =====================================================
# FLASK APP
# =====================================================

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY")


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():

    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.environ.get("MYSQL_PASSWORD"),
        database="ai_smart_study_planner"
    )

    return connection


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    return render_template("index.html")


# =====================================================
# REGISTER
# =====================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        course = request.form["course"]
        branch = request.form["branch"]

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO students
                (name, email, password, course, branch)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    name,
                    email,
                    password,
                    course,
                    branch
                )
            )

            connection.commit()

            return redirect(
                url_for("login")
            )

        except mysql.connector.Error as error:

            print(
                "Registration Error:",
                error
            )

            return render_template(
                "register.html",
                error="Email may already exist."
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "register.html"
    )


# =====================================================
# LOGIN
# =====================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = None
        cursor = None

        try:

            connection = get_db_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM students
                WHERE email = %s
                AND password = %s
                """,
                (
                    email,
                    password
                )
            )

            student = cursor.fetchone()

            if student:

                session["student_id"] = (
                    student["student_id"]
                )

                session["student_name"] = (
                    student["name"]
                )

                return redirect(
                    url_for("dashboard")
                )

            else:

                return render_template(
                    "login.html",
                    error="Invalid email or password."
                )

        except mysql.connector.Error as error:

            print(
                "Login Error:",
                error
            )

            return render_template(
                "login.html",
                error="Database connection error."
            )

        finally:

            if cursor:
                cursor.close()

            if connection:
                connection.close()

    return render_template(
        "login.html"
    )


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # 1. TOTAL SUBJECTS
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total_subjects
            FROM subjects
            WHERE student_id = %s
            """,
            (student_id,)
        )

        subject_result = cursor.fetchone()

        total_subjects = int(
            subject_result["total_subjects"] or 0
        )


        # =================================================
        # 2. UPCOMING EXAMS
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS upcoming_exams
            FROM exams
            WHERE student_id = %s
            AND exam_date >= CURDATE()
            """,
            (student_id,)
        )

        exam_result = cursor.fetchone()

        upcoming_exams = int(
            exam_result["upcoming_exams"] or 0
        )


        # =================================================
        # 3. UPCOMING EXAM LIST
        # =================================================

        cursor.execute(
            """
            SELECT
                exams.exam_id,
                exams.exam_date,
                subjects.subject_name
            FROM exams
            INNER JOIN subjects
                ON exams.subject_id = subjects.subject_id
            WHERE exams.student_id = %s
            AND exams.exam_date >= CURDATE()
            ORDER BY exams.exam_date ASC
            """,
            (student_id,)
        )

        upcoming_exam_list = (
            cursor.fetchall()
        )


        # =================================================
        # 4. TOTAL PENDING STUDY SESSIONS
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total_sessions
            FROM study_plans
            WHERE student_id = %s
            AND status = 'Pending'
            """,
            (student_id,)
        )

        session_result = cursor.fetchone()

        total_sessions = int(
            session_result["total_sessions"] or 0
        )


        # =================================================
        # 5. COMPLETED STUDY SESSIONS
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS completed_sessions
            FROM study_plans
            WHERE student_id = %s
            AND status = 'Completed'
            """,
            (student_id,)
        )

        completed_result = cursor.fetchone()

        completed_sessions = int(
            completed_result[
                "completed_sessions"
            ] or 0
        )


        # =================================================
        # 6. TOTAL HOURS STUDIED
        # =================================================

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(hours_studied),
                    0
                ) AS total_hours
            FROM progress
            WHERE student_id = %s
            """,
            (student_id,)
        )

        hours_result = cursor.fetchone()

        total_hours = float(
            hours_result["total_hours"] or 0
        )

        total_hours = round(
            total_hours,
            2
        )


        # =================================================
        # 7. OVERALL LEARNING PROGRESS
        # =================================================

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(total_topics),
                    0
                ) AS total_topics,

                COALESCE(
                    SUM(completed_topics),
                    0
                ) AS completed_topics

            FROM subjects

            WHERE student_id = %s
            """,
            (student_id,)
        )

        progress_summary = (
            cursor.fetchone()
        )

        total_topics = int(
            progress_summary[
                "total_topics"
            ] or 0
        )

        completed_topics = int(
            progress_summary[
                "completed_topics"
            ] or 0
        )

        if total_topics > 0:

            completed_topics = min(
                max(
                    completed_topics,
                    0
                ),
                total_topics
            )

            learning_progress = round(
                (
                    completed_topics
                    / total_topics
                ) * 100,
                2
            )

        else:

            learning_progress = 0


        # =================================================
        # 8. AI SUBJECT PRIORITY
        # =================================================

        cursor.execute(
            """
            SELECT
                s.subject_id,
                s.subject_name,
                s.marks,
                s.difficulty,
                s.total_topics,
                s.completed_topics,
                e.exam_date

            FROM subjects s

            LEFT JOIN exams e
                ON s.subject_id = e.subject_id

            WHERE s.student_id = %s

            ORDER BY e.exam_date ASC
            """,
            (student_id,)
        )

        subject_rows = cursor.fetchall()

        priority_subjects = []


        for subject in subject_rows:

            exam_date = subject["exam_date"]

            if exam_date is None:

                exam_date = (
                    date.today()
                    + timedelta(days=90)
                )


            priority = calculate_priority(

                marks=float(
                    subject["marks"] or 0
                ),

                difficulty=(
                    subject["difficulty"]
                    or "Medium"
                ),

                exam_date=exam_date,

                total_topics=int(
                    subject["total_topics"]
                    or 0
                ),

                completed_topics=int(
                    subject["completed_topics"]
                    or 0
                )
            )


            subject["priority_score"] = (
                priority["score"]
            )

            subject["priority_level"] = (
                priority["level"]
            )

            subject["days_left"] = (
                priority["days_left"]
            )

            priority_subjects.append(
                subject
            )


        priority_subjects.sort(
            key=lambda x: float(
                x["priority_score"]
            ),
            reverse=True
        )


        # =================================================
        # 9. TODAY'S STUDY REMINDER
        # =================================================

        cursor.execute(
            """
            SELECT
                sp.plan_id,
                sp.study_date,
                sp.start_time,
                sp.end_time,
                sp.topic,
                sp.status,
                s.subject_name

            FROM study_plans sp

            INNER JOIN subjects s
                ON sp.subject_id = s.subject_id

            WHERE sp.student_id = %s

            AND sp.study_date = CURDATE()

            ORDER BY
                sp.start_time ASC
            """,
            (student_id,)
        )

        today_sessions = cursor.fetchall()


        # =================================================
        # 10. FORMAT TODAY'S TIMES
        # =================================================

        for reminder in today_sessions:

            start_value = reminder[
                "start_time"
            ]

            if start_value:

                if isinstance(
                    start_value,
                    timedelta
                ):

                    total_seconds = int(
                        start_value.total_seconds()
                    )

                    hours = (
                        total_seconds // 3600
                    ) % 24

                    minutes = (
                        total_seconds % 3600
                    ) // 60

                    period = (
                        "AM"
                        if hours < 12
                        else "PM"
                    )

                    display_hour = (
                        hours % 12
                    )

                    if display_hour == 0:
                        display_hour = 12

                    reminder[
                        "start_time_display"
                    ] = (
                        f"{display_hour:02d}:"
                        f"{minutes:02d} "
                        f"{period}"
                    )

                elif isinstance(
                    start_value,
                    time
                ):

                    reminder[
                        "start_time_display"
                    ] = start_value.strftime(
                        "%I:%M %p"
                    )

                elif isinstance(
                    start_value,
                    datetime
                ):

                    reminder[
                        "start_time_display"
                    ] = start_value.strftime(
                        "%I:%M %p"
                    )

                else:

                    reminder[
                        "start_time_display"
                    ] = str(
                        start_value
                    )

            else:

                reminder[
                    "start_time_display"
                ] = ""


            end_value = reminder[
                "end_time"
            ]

            if end_value:

                if isinstance(
                    end_value,
                    timedelta
                ):

                    total_seconds = int(
                        end_value.total_seconds()
                    )

                    hours = (
                        total_seconds // 3600
                    ) % 24

                    minutes = (
                        total_seconds % 3600
                    ) // 60

                    period = (
                        "AM"
                        if hours < 12
                        else "PM"
                    )

                    display_hour = (
                        hours % 12
                    )

                    if display_hour == 0:
                        display_hour = 12

                    reminder[
                        "end_time_display"
                    ] = (
                        f"{display_hour:02d}:"
                        f"{minutes:02d} "
                        f"{period}"
                    )

                elif isinstance(
                    end_value,
                    time
                ):

                    reminder[
                        "end_time_display"
                    ] = end_value.strftime(
                        "%I:%M %p"
                    )

                elif isinstance(
                    end_value,
                    datetime
                ):

                    reminder[
                        "end_time_display"
                    ] = end_value.strftime(
                        "%I:%M %p"
                    )

                else:

                    reminder[
                        "end_time_display"
                    ] = str(
                        end_value
                    )

            else:

                reminder[
                    "end_time_display"
                ] = ""


        # =================================================
        # 11. REMINDER SUMMARY
        # =================================================

        today_total_sessions = len(
            today_sessions
        )

        today_completed_sessions = sum(
            1
            for reminder in today_sessions
            if reminder["status"] == "Completed"
        )

        today_pending_sessions = (
            today_total_sessions
            - today_completed_sessions
        )


        # =================================================
        # 12. NEXT PENDING SESSION
        # =================================================

        next_session = None

        for reminder in today_sessions:

            if reminder["status"] != "Completed":

                next_session = reminder

                break


        # =================================================
        # 13. REMINDER MESSAGE
        # =================================================

        if today_total_sessions == 0:

            reminder_message = (
                "No study sessions are scheduled "
                "for today."
            )

        elif today_pending_sessions == 0:

            reminder_message = (
                "Excellent! You completed "
                "all today's study sessions. 🎉"
            )

        else:

            reminder_message = (
                f"You have "
                f"{today_pending_sessions} "
                f"study session"
                f"{'s' if today_pending_sessions != 1 else ''} "
                f"remaining today."
            )


        # =================================================
        # 14. RENDER DASHBOARD
        # =================================================

        return render_template(

            "dashboard.html",

            total_subjects=(
                total_subjects
            ),

            upcoming_exams=(
                upcoming_exams
            ),

            upcoming_exam_list=(
                upcoming_exam_list
            ),

            total_sessions=(
                total_sessions
            ),

            completed_sessions=(
                completed_sessions
            ),

            total_hours=(
                total_hours
            ),

            learning_progress=(
                learning_progress
            ),

            priority_list=(
                priority_subjects
            ),

            today_sessions=(
                today_sessions
            ),

            today_total_sessions=(
                today_total_sessions
            ),

            today_completed_sessions=(
                today_completed_sessions
            ),

            today_pending_sessions=(
                today_pending_sessions
            ),

            next_session=(
                next_session
            ),

            reminder_message=(
                reminder_message
            )
        )


    except mysql.connector.Error as error:

        print(
            "Dashboard Error:",
            error
        )

        return render_template(

            "dashboard.html",

            total_subjects=0,

            upcoming_exams=0,

            upcoming_exam_list=[],

            total_sessions=0,

            completed_sessions=0,

            total_hours=0,

            learning_progress=0,

            priority_list=[],

            today_sessions=[],

            today_total_sessions=0,

            today_completed_sessions=0,

            today_pending_sessions=0,

            next_session=None,

            reminder_message=(
                "Unable to load today's "
                "study reminders."
            ),

            error=(
                "Unable to load dashboard data."
            )
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# SUBJECTS
# =====================================================

@app.route(
    "/subjects",
    methods=["GET", "POST"]
)
def subjects():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # ADD SUBJECT
        # =================================================

        if request.method == "POST":

            subject_name = request.form[
                "subject_name"
            ]

            marks = request.form[
                "marks"
            ]

            difficulty = request.form[
                "difficulty"
            ]

            total_topics = request.form[
                "total_topics"
            ]

            completed_topics = request.form.get(
                "completed_topics",
                0
            )


            cursor.execute(
                """
                INSERT INTO subjects
                (
                    student_id,
                    subject_name,
                    marks,
                    difficulty,
                    total_topics,
                    completed_topics
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,

                (
                    student_id,
                    subject_name,
                    marks,
                    difficulty,
                    total_topics,
                    completed_topics
                )
            )

            connection.commit()


        # =================================================
        # GET SUBJECTS
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM subjects
            WHERE student_id = %s
            ORDER BY subject_id DESC
            """,
            (student_id,)
        )

        subject_list = cursor.fetchall()


        return render_template(
            "subjects.html",
            subjects=subject_list
        )


    except mysql.connector.Error as error:

        print(
            "Subjects Error:",
            error
        )

        return render_template(
            "subjects.html",
            subjects=[],
            error="Unable to load subjects."
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# EDIT SUBJECT
# =====================================================

@app.route(
    "/edit-subject/<int:subject_id>",
    methods=["GET", "POST"]
)
def edit_subject(subject_id):

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # UPDATE SUBJECT
        # =================================================

        if request.method == "POST":

            subject_name = request.form[
                "subject_name"
            ]

            marks = request.form[
                "marks"
            ]

            difficulty = request.form[
                "difficulty"
            ]

            total_topics = request.form[
                "total_topics"
            ]

            completed_topics = request.form.get(
                "completed_topics",
                0
            )


            # Keep completed topics within valid range

            try:

                total_topics_int = int(
                    total_topics
                )

                completed_topics_int = int(
                    completed_topics
                )

                completed_topics_int = max(
                    0,
                    min(
                        completed_topics_int,
                        total_topics_int
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                completed_topics_int = 0


            cursor.execute(
                """
                UPDATE subjects

                SET
                    subject_name = %s,
                    marks = %s,
                    difficulty = %s,
                    total_topics = %s,
                    completed_topics = %s

                WHERE subject_id = %s

                AND student_id = %s
                """,

                (
                    subject_name,
                    marks,
                    difficulty,
                    total_topics,
                    completed_topics_int,
                    subject_id,
                    student_id
                )
            )

            connection.commit()


            return redirect(
                url_for("subjects")
            )


        # =================================================
        # GET SUBJECT
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM subjects

            WHERE subject_id = %s

            AND student_id = %s
            """,

            (
                subject_id,
                student_id
            )
        )

        subject = cursor.fetchone()


        if not subject:

            return redirect(
                url_for("subjects")
            )


        return render_template(
            "edit_subject.html",
            subject=subject
        )


    except mysql.connector.Error as error:

        print(
            "Edit Subject Error:",
            error
        )

        return redirect(
            url_for("subjects")
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# DELETE SUBJECT
# =====================================================

@app.route(
    "/delete-subject/<int:subject_id>",
    methods=["POST"]
)
def delete_subject(subject_id):

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()


        cursor.execute(
            """
            DELETE FROM subjects

            WHERE subject_id = %s

            AND student_id = %s
            """,

            (
                subject_id,
                student_id
            )
        )

        connection.commit()


        return redirect(
            url_for("subjects")
        )


    except mysql.connector.Error as error:

        print(
            "Delete Subject Error:",
            error
        )

        return redirect(
            url_for("subjects")
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# EXAMS
# =====================================================

@app.route(
    "/exams",
    methods=["GET", "POST"]
)
def exams():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # ADD EXAM
        # =================================================

        if request.method == "POST":

            subject_id = request.form[
                "subject_id"
            ]

            exam_date = request.form[
                "exam_date"
            ]


            cursor.execute(
                """
                INSERT INTO exams
                (
                    student_id,
                    subject_id,
                    exam_date
                )

                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,

                (
                    student_id,
                    subject_id,
                    exam_date
                )
            )

            connection.commit()


        # =================================================
        # GET SUBJECTS
        # =================================================

        cursor.execute(
            """
            SELECT
                subject_id,
                subject_name

            FROM subjects

            WHERE student_id = %s

            ORDER BY subject_name
            """,

            (student_id,)
        )

        subject_list = (
            cursor.fetchall()
        )


        # =================================================
        # GET EXAMS
        # =================================================

        cursor.execute(
            """
            SELECT
                e.exam_id,
                e.exam_date,
                s.subject_name

            FROM exams e

            INNER JOIN subjects s
                ON e.subject_id = s.subject_id

            WHERE e.student_id = %s

            ORDER BY e.exam_date ASC
            """,

            (student_id,)
        )

        exam_list = (
            cursor.fetchall()
        )


        return render_template(

            "exams.html",

            subjects=subject_list,

            exams=exam_list
        )


    except mysql.connector.Error as error:

        print(
            "Exam Error:",
            error
        )

        return render_template(

            "exams.html",

            subjects=[],

            exams=[],

            error="Unable to load exams."
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# AI STUDY PLAN
# =====================================================

@app.route(
    "/study-plan",
    methods=["GET", "POST"]
)
def study_plan():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # GENERATE NEW PLAN
        # =================================================

        if request.method == "POST":

            available_hours = request.form.get(
                "available_hours",
                3
            )


            # ---------------------------------------------
            # GET SUBJECTS
            # ---------------------------------------------

            cursor.execute(
                """
                SELECT
                    s.subject_id,
                    s.subject_name,
                    s.marks,
                    s.difficulty,
                    s.total_topics,
                    s.completed_topics,
                    e.exam_date

                FROM subjects s

                LEFT JOIN exams e
                    ON s.subject_id = e.subject_id

                WHERE s.student_id = %s
                """,

                (student_id,)
            )

            subjects_data = (
                cursor.fetchall()
            )


            # ---------------------------------------------
            # CALCULATE PRIORITY
            # ---------------------------------------------

            planner_subjects = []


            for subject in subjects_data:

                exam_date = subject[
                    "exam_date"
                ]

                if exam_date is None:

                    exam_date = (
                        date.today()
                        + timedelta(days=90)
                    )


                priority = calculate_priority(

                    marks=float(
                        subject["marks"]
                        or 0
                    ),

                    difficulty=(
                        subject["difficulty"]
                        or "Medium"
                    ),

                    exam_date=exam_date,

                    total_topics=int(
                        subject[
                            "total_topics"
                        ] or 0
                    ),

                    completed_topics=int(
                        subject[
                            "completed_topics"
                        ] or 0
                    )
                )


                subject["priority_score"] = (
                    priority["score"]
                )

                planner_subjects.append(
                    subject
                )


            # ---------------------------------------------
            # DELETE ONLY PENDING PLANS
            # ---------------------------------------------

            cursor.execute(
                """
                DELETE FROM study_plans

                WHERE student_id = %s

                AND status = 'Pending'
                """,

                (student_id,)
            )


            # ---------------------------------------------
            # GENERATE PLAN
            # ---------------------------------------------

            generated_plan = (
                generate_study_plan(
                    planner_subjects,
                    available_hours
                )
            )


            # ---------------------------------------------
            # SAVE PLAN
            # ---------------------------------------------

            for plan in generated_plan:

                cursor.execute(
                    """
                    INSERT INTO study_plans
                    (
                        student_id,
                        subject_id,
                        study_date,
                        start_time,
                        end_time,
                        topic,
                        priority_score,
                        status
                    )

                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,

                    (
                        student_id,
                        plan["subject_id"],
                        plan["study_date"],
                        plan["start_time"],
                        plan["end_time"],
                        plan["topic"],
                        plan["priority_score"],
                        plan["status"]
                    )
                )


            connection.commit()


        # =================================================
        # GET SAVED STUDY PLANS
        # =================================================

        cursor.execute(
            """
            SELECT
                sp.plan_id,
                sp.study_date,
                sp.start_time,
                sp.end_time,
                sp.topic,
                sp.priority_score,
                sp.status,
                s.subject_name

            FROM study_plans sp

            INNER JOIN subjects s
                ON sp.subject_id = s.subject_id

            WHERE sp.student_id = %s

            ORDER BY
                sp.study_date ASC,
                sp.start_time ASC
            """,

            (student_id,)
        )

        plans = cursor.fetchall()


        # =================================================
        # FORMAT TIMES
        # =================================================

        for plan in plans:

            start_value = plan["start_time"]

            if start_value:

                if isinstance(
                    start_value,
                    timedelta
                ):

                    total_seconds = int(
                        start_value.total_seconds()
                    )

                    hours = (
                        total_seconds // 3600
                    ) % 24

                    minutes = (
                        total_seconds % 3600
                    ) // 60

                    period = (
                        "AM"
                        if hours < 12
                        else "PM"
                    )

                    display_hour = (
                        hours % 12
                    )

                    if display_hour == 0:
                        display_hour = 12

                    plan[
                        "start_time_display"
                    ] = (
                        f"{display_hour:02d}:"
                        f"{minutes:02d} "
                        f"{period}"
                    )

                elif isinstance(
                    start_value,
                    time
                ):

                    plan[
                        "start_time_display"
                    ] = start_value.strftime(
                        "%I:%M %p"
                    )

                elif isinstance(
                    start_value,
                    datetime
                ):

                    plan[
                        "start_time_display"
                    ] = start_value.strftime(
                        "%I:%M %p"
                    )

                elif isinstance(
                    start_value,
                    str
                ):

                    try:

                        parsed_time = (
                            datetime.strptime(
                                start_value,
                                "%H:%M:%S"
                            )
                        )

                        plan[
                            "start_time_display"
                        ] = parsed_time.strftime(
                            "%I:%M %p"
                        )

                    except ValueError:

                        plan[
                            "start_time_display"
                        ] = start_value

                else:

                    plan[
                        "start_time_display"
                    ] = str(
                        start_value
                    )

            else:

                plan[
                    "start_time_display"
                ] = ""


            end_value = plan["end_time"]

            if end_value:

                if isinstance(
                    end_value,
                    timedelta
                ):

                    total_seconds = int(
                        end_value.total_seconds()
                    )

                    hours = (
                        total_seconds // 3600
                    ) % 24

                    minutes = (
                        total_seconds % 3600
                    ) // 60

                    period = (
                        "AM"
                        if hours < 12
                        else "PM"
                    )

                    display_hour = (
                        hours % 12
                    )

                    if display_hour == 0:
                        display_hour = 12

                    plan[
                        "end_time_display"
                    ] = (
                        f"{display_hour:02d}:"
                        f"{minutes:02d} "
                        f"{period}"
                    )

                elif isinstance(
                    end_value,
                    time
                ):

                    plan[
                        "end_time_display"
                    ] = end_value.strftime(
                        "%I:%M %p"
                    )

                elif isinstance(
                    end_value,
                    datetime
                ):

                    plan[
                        "end_time_display"
                    ] = end_value.strftime(
                        "%I:%M %p"
                    )

                elif isinstance(
                    end_value,
                    str
                ):

                    try:

                        parsed_time = (
                            datetime.strptime(
                                end_value,
                                "%H:%M:%S"
                            )
                        )

                        plan[
                            "end_time_display"
                        ] = parsed_time.strftime(
                            "%I:%M %p"
                        )

                    except ValueError:

                        plan[
                            "end_time_display"
                        ] = end_value

                else:

                    plan[
                        "end_time_display"
                    ] = str(
                        end_value
                    )

            else:

                plan[
                    "end_time_display"
                ] = ""


        return render_template(

            "study_plan.html",

            plans=plans
        )


    except mysql.connector.Error as error:

        print(
            "Study Plan Database Error:",
            error
        )

        return render_template(

            "study_plan.html",

            plans=[],

            error=(
                "Unable to generate study plan."
            )
        )


    except Exception as error:

        print(
            "Study Plan Error:",
            error
        )

        return render_template(

            "study_plan.html",

            plans=[],

            error=(
                "An error occurred while "
                "loading the study plan."
            )
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# COMPLETE STUDY SESSION
# =====================================================

@app.route(
    "/complete-study/<int:plan_id>",
    methods=["POST"]
)
def complete_study(plan_id):

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                plan_id,
                subject_id,
                study_date,
                status

            FROM study_plans

            WHERE plan_id = %s

            AND student_id = %s
            """,

            (
                plan_id,
                student_id
            )
        )

        plan = cursor.fetchone()


        if not plan:

            return redirect(
                url_for("study_plan")
            )


        if plan["status"] != "Completed":

            cursor.execute(
                """
                UPDATE study_plans

                SET status = 'Completed'

                WHERE plan_id = %s

                AND student_id = %s
                """,

                (
                    plan_id,
                    student_id
                )
            )


            cursor.execute(
                """
                SELECT
                    total_topics,
                    completed_topics

                FROM subjects

                WHERE subject_id = %s

                AND student_id = %s
                """,

                (
                    plan["subject_id"],
                    student_id
                )
            )

            subject = cursor.fetchone()


            if subject:

                total_topics = int(
                    subject[
                        "total_topics"
                    ] or 0
                )

                completed_topics = int(
                    subject[
                        "completed_topics"
                    ] or 0
                )


                if completed_topics < total_topics:

                    completed_topics += 1

                    cursor.execute(
                        """
                        UPDATE subjects

                        SET completed_topics = %s

                        WHERE subject_id = %s

                        AND student_id = %s
                        """,

                        (
                            completed_topics,
                            plan["subject_id"],
                            student_id
                        )
                    )


                if total_topics > 0:

                    progress_percentage = round(
                        (
                            completed_topics
                            / total_topics
                        ) * 100,
                        2
                    )

                else:

                    progress_percentage = 0


                cursor.execute(
                    """
                    SELECT
                        progress_id,
                        hours_studied,
                        topics_completed

                    FROM progress

                    WHERE student_id = %s

                    AND subject_id = %s

                    AND study_date = %s
                    """,

                    (
                        student_id,
                        plan["subject_id"],
                        plan["study_date"]
                    )
                )

                existing_progress = (
                    cursor.fetchone()
                )


                if existing_progress:

                    new_hours = float(
                        existing_progress[
                            "hours_studied"
                        ] or 0
                    ) + 1

                    new_topics = int(
                        existing_progress[
                            "topics_completed"
                        ] or 0
                    ) + 1


                    cursor.execute(
                        """
                        UPDATE progress

                        SET
                            hours_studied = %s,
                            topics_completed = %s,
                            progress_percentage = %s

                        WHERE progress_id = %s
                        """,

                        (
                            new_hours,
                            new_topics,
                            progress_percentage,
                            existing_progress[
                                "progress_id"
                            ]
                        )
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO progress
                        (
                            student_id,
                            subject_id,
                            study_date,
                            hours_studied,
                            topics_completed,
                            progress_percentage
                        )

                        VALUES
                        (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        """,

                        (
                            student_id,
                            plan["subject_id"],
                            plan["study_date"],
                            1,
                            1,
                            progress_percentage
                        )
                    )


            connection.commit()


        return redirect(
            url_for("study_plan")
        )


    except mysql.connector.Error as error:

        print(
            "Complete Study Error:",
            error
        )

        return redirect(
            url_for("study_plan")
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# PROGRESS TRACKING
# =====================================================

@app.route("/progress")
def progress_page():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    student_id = session["student_id"]

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # =================================================
        # 1. GET SUBJECT INFORMATION
        # =================================================

        cursor.execute(
            """
            SELECT
                subject_id,
                subject_name,
                total_topics,
                completed_topics,
                difficulty

            FROM subjects

            WHERE student_id = %s

            ORDER BY subject_name ASC
            """,

            (student_id,)
        )

        subjects = cursor.fetchall()

        subject_progress = []

        total_topics = 0
        completed_topics = 0


        # =================================================
        # 2. SUBJECT-WISE PROGRESS
        # =================================================

        for subject in subjects:

            subject_total = int(
                subject["total_topics"] or 0
            )

            subject_completed = int(
                subject["completed_topics"] or 0
            )


            if subject_total > 0:

                subject_completed = min(
                    max(
                        subject_completed,
                        0
                    ),
                    subject_total
                )

                percentage = round(
                    (
                        subject_completed
                        / subject_total
                    ) * 100,
                    2
                )

            else:

                subject_completed = 0

                percentage = 0


            total_topics += (
                subject_total
            )

            completed_topics += (
                subject_completed
            )


            subject[
                "progress_percentage"
            ] = percentage


            subject_progress.append(
                subject
            )


        # =================================================
        # 3. OVERALL LEARNING PROGRESS
        # =================================================

        if total_topics > 0:

            learning_progress = round(
                (
                    completed_topics
                    / total_topics
                ) * 100,
                2
            )

        else:

            learning_progress = 0


        # =================================================
        # 4. TOTAL STUDY HOURS
        # =================================================

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(hours_studied),
                    0
                ) AS total_hours

            FROM progress

            WHERE student_id = %s
            """,

            (student_id,)
        )

        hours_result = cursor.fetchone()

        total_hours = float(
            hours_result[
                "total_hours"
            ] or 0
        )

        total_hours = round(
            total_hours,
            2
        )


        # =================================================
        # 5. COMPLETED STUDY SESSIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS completed_sessions

            FROM study_plans

            WHERE student_id = %s

            AND status = 'Completed'
            """,

            (student_id,)
        )

        completed_result = (
            cursor.fetchone()
        )

        completed_sessions = int(
            completed_result[
                "completed_sessions"
            ] or 0
        )


        # =================================================
        # 6. TOTAL STUDY SESSIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                COUNT(*) AS total_sessions

            FROM study_plans

            WHERE student_id = %s
            """,

            (student_id,)
        )

        total_result = cursor.fetchone()

        total_sessions = int(
            total_result[
                "total_sessions"
            ] or 0
        )


        # =================================================
        # 7. PENDING STUDY SESSIONS
        # =================================================

        pending_sessions = max(
            total_sessions
            - completed_sessions,
            0
        )


        # =================================================
        # 8. TOTAL SUBJECTS
        # =================================================

        total_subjects = len(
            subject_progress
        )


        # =================================================
        # 9. DISPLAY PROGRESS PAGE
        # =================================================

        return render_template(

            "progress.html",

            learning_progress=(
                learning_progress
            ),

            total_hours=(
                total_hours
            ),

            completed_sessions=(
                completed_sessions
            ),

            total_subjects=(
                total_subjects
            ),

            pending_sessions=(
                pending_sessions
            ),

            subject_progress=(
                subject_progress
            )
        )


    except mysql.connector.Error as error:

        print(
            "Progress Error:",
            error
        )

        return render_template(

            "progress.html",

            learning_progress=0,

            total_hours=0,

            completed_sessions=0,

            total_subjects=0,

            pending_sessions=0,

            subject_progress=[],

            error=(
                "Unable to load progress data."
            )
        )


    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# PROJECT RESOURCES
# =====================================================

@app.route("/resources")
def resources():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "resources.html"
    )


# =====================================================
# PROJECT DOCUMENTATION
# =====================================================

@app.route("/documentation")
def documentation():

    if "student_id" not in session:

        return redirect(
            url_for("login")
        )

    return render_template(
        "documentation.html"
    )
# =====================================================
# PROJECT PPT
# =====================================================

@app.route("/ppt")
def project_ppt():

    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template("ppt.html")


# =====================================================
# VIVA QUESTIONS
# =====================================================

@app.route("/viva")
def viva():

    if "student_id" not in session:
        return redirect(url_for("login"))

    return render_template("viva.html")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )