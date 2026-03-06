from fastapi import FastAPI
from pydantic import BaseModel
from database import create_table, save_interview
import sqlite3
import random
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
create_table()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Request model
class AnswerRequest(BaseModel):
    username: str
    mode: str      # 'HR' or 'Technical'
    question: str
    answer: str

# Questions
hr_questions = [
    "Tell me about yourself.",
    "Why should we hire you?",
    "What are your strengths and weaknesses?",
    "Where do you see yourself in 5 years?",
    "Why do you want to work with us?"
]

technical_questions = [
    "What is time complexity?",
    "Explain OOPS concepts.",
    "What is a linked list?",
    "Difference between list and tuple in Python?",
    "What is normalization in DBMS?",
    "Explain recursion with example.",
    "What is REST API?",
    "What is difference between stack and queue?"
]

# Home
@app.get("/")
def home():
    return {"message": "AI interview platform Running"}

# HR question
@app.get("/get-hr-question")
def get_hr_question():
    question = random.choice(hr_questions)
    return {"question": question}

# Technical question
@app.get("/get-technical-question")
def get_technical_question():
    question = random.choice(technical_questions)
    return {"question": question}

# Submit answer
@app.post("/submit-answer")
def submit_answer(data: AnswerRequest):
    answer = data.answer.lower()
    score = 0

    # Base score by word count (better than character length)
    word_count = len(answer.split())
    score += min(word_count // 5, 5)

    # Keywords
    hr_keywords = ["team", "lead", "responsible", "improve", "learn", "project"]
    technical_keywords = [
        "time complexity", "o(", "class", "object",
        "stack", "queue", "database", "table",
        "recursion", "array", "linked list",
        "api", "http", "algorithm"
    ]

    # Mode based scoring
    if data.mode.lower() == "hr":
        for word in hr_keywords:
            if word in answer:
                score += 1
    else:
        for word in technical_keywords:
            if word in answer:
                score += 2

    # Limit max score
    score = min(score, 20)
    # Feedback
    if score >= 12:
        feedback = "Excellent answer with strong content and keywords!"
    elif score >= 7:
        feedback = "Good answer, but can improve clarity."
    else:
        feedback = "Try to add more details and strong keywords."

    # Save to DB
    save_interview(data.username, data.mode, data.question, data.answer, score)

    return {
        "username": data.username,
        "mode": data.mode,
        "question": data.question,
        "your_answer": data.answer,
        "score": score,
        "feedback": feedback
    }

# Get all results
@app.get("/get-all-results")
def get_all_results():
    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, mode, question, answer, score FROM interviews")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "username": row[0],
            "mode": row[1],
            "question": row[2],
            "answer": row[3],
            "score": row[4]
        })
    return {"results": results}

@app.get("/get-average-score/{username}")
def get_average_score(username: str):
    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT score FROM interviews WHERE username = ?",
        (username,)
    )

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"message": "No interviews found for this user"}

    scores = [row[0] for row in rows]

    total_interviews = len(scores)
    average_score = sum(scores) / total_interviews
    highest_score = max(scores)
    lowest_score = min(scores)

    if average_score >= 15:
        performance = "Excellent performance! You are interview ready."
    elif average_score >= 10:
        performance = "Good performance, but needs improvement."
    else:
        performance = "You need serious improvement. Practice more."

    return {
        "username": username,
        "total_interviews": total_interviews,
        "average_score": round(average_score, 2),
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "performance": performance
    }

    @app.get("/get-mode-average/{username}")
    def get_mode_average(username: str):

        "weak_area": "Technical"
        
        conn = sqlite3.connect("interview.db")
        cursor = conn.cursor()

        # HR Scores
        cursor.execute(
            "SELECT score FROM interviews WHERE username = ? AND mode = ?",
            (username, "HR")
        )
        hr_rows = cursor.fetchall()

        # Technical Scores
        cursor.execute(
            "SELECT score FROM interviews WHERE username = ? AND mode = ?",
            (username, "Technical")
        )
        tech_rows = cursor.fetchall()

        conn.close()

        hr_scores = [row[0] for row in hr_rows]
        tech_scores = [row[0] for row in tech_rows]

        hr_avg = round(sum(hr_scores) / len(hr_scores), 2) if hr_scores else 0
        tech_avg = round(sum(tech_scores) / len(tech_scores), 2) if tech_scores else 0

        # Weak area detection
        if hr_avg == 0 and tech_avg == 0:
            weak_area = "No interviews yet"
        elif hr_avg < tech_avg:
            weak_area = "HR"
        elif tech_avg < hr_avg:
            weak_area = "Technical"
        else:
            weak_area = "Both are equal"

        return {
            "username": username,
            "hr_total": len(hr_scores),
            "hr_average": hr_avg,
            "technical_total": len(tech_scores),
            "technical_average": tech_avg,
            "weak_area": weak_area
        }