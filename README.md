# AI Smart Study Planner

## 📌 Project Overview

AI Smart Study Planner is a web-based application developed to help students organize their studies, manage subjects and exams, and generate personalized study plans.

The system uses student performance, subject difficulty, completed topics, and upcoming exam dates to calculate study priorities and generate a structured study schedule.

## 🎯 Objectives

* Manage student academic information
* Add and manage subjects
* Track marks and subject difficulty
* Manage upcoming examinations
* Calculate subject priority using AI-based logic
* Generate personalized study plans
* Track study progress
* Provide project documentation and viva preparation
* Present academic information through a simple web interface

## 🛠️ Technologies Used

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* Python
* Flask

### Database

* MySQL

### AI / Data Processing

* Scikit-learn
* Pandas
* NumPy
* Matplotlib

## 🧠 AI Priority Calculation

The system calculates a priority score for each subject using factors such as:

* Exam urgency
* Student marks/performance
* Subject difficulty
* Remaining topics

Subjects with higher priority scores receive more attention in the generated study plan.

## 📚 Main Modules

1. Student Login and Registration
2. Dashboard
3. Subject Management
4. Exam Management
5. AI Priority Calculation
6. AI Study Plan Generation
7. Progress Tracking
8. Resources
9. Project Documentation
10. PPT Presentation
11. Viva Questions

## 📅 Study Plan Generation

The study planner generates a seven-day study schedule based on:

* Available study hours
* Subject priority
* Remaining topics
* Student academic information

The generated plan assigns study sessions to different subjects according to their priority.

## 📊 Progress Tracking

Students can track:

* Hours studied
* Topics completed
* Subject-wise progress
* Overall learning progress
* Completed study sessions

## 🗄️ Database Tables

The application uses MySQL with the following tables:

* `students`
* `subjects`
* `exams`
* `study_plans`
* `progress`

## 📁 Project Structure

```text
AI_Smart_Study_Planner/
│
├── app.py
├── requirements.txt
├── README.md
│
├── ai/
│   ├── planner.py
│   └── priority.py
│
├── data/
│   └── sample_data.csv
│
├── database/
│   └── database.sql
│
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── exams.html
│   ├── index.html
│   ├── login.html
│   ├── progress.html
│   ├── register.html
│   ├── study_plan.html
│   ├── subjects.html
│   ├── resources.html
│   ├── documentation.html
│   ├── ppt.html
│   └── viva.html
│
└── utils/
    └── helpers.py
```

## ▶️ How to Run

### 1. Open CMD

Go to the project folder:

```cmd
cd "C:\Users\keert\OneDrive\Desktop\AI_Smart_Study_Planner"
```

### 2. Activate the virtual environment

```cmd
venv\Scripts\activate
```

### 3. Install dependencies

```cmd
pip install -r requirements.txt
```

### 4. Start the Flask application

```cmd
python app.py
```

### 5. Open the application

Open the following address in your browser:

```text
http://127.0.0.1:5000
```

## 🔐 Database Configuration

The application uses MySQL database:

```text
Database: ai_smart_study_planner
```

The database structure is available in:

```text
database/database.sql
```

## 🚀 Future Scope

Possible future improvements include:

* Machine learning-based study prediction
* Automatic timetable optimization
* AI chatbot for academic assistance
* Email and notification reminders
* Mobile application
* Cloud deployment
* Advanced student performance analytics
* More personalized recommendations

## 👩‍💻 Project

**AI Smart Study Planner**

Developed as a B.Tech academic project using Python, Flask, MySQL, and AI/data-processing technologies.
