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
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnswerRequest(BaseModel):
    username: str
    mode: str
    question: str
    answer: str


hr_questions = [
"Tell me about yourself.",
"Why should we hire you?",
"What are your strengths?",
"What is your biggest weakness?",
"Where do you see yourself in 5 years?",
"Describe a challenge you faced.",
"How do you handle pressure?",
"Describe a time you worked in a team.",
"How do you manage deadlines?",
"Why do you want to join our company?",
"Tell me about a leadership experience.",
"What motivates you?",
"How do you resolve conflicts?",
"Describe a failure and what you learned.",
"What are your career goals?"
]

technical_questions = [

"What is time complexity?",
"Explain OOP concepts.",
"What is polymorphism?",
"What is inheritance?",
"What is encapsulation?",
"What is abstraction?",
"What is recursion?",
"Explain linked list.",
"Difference between stack and queue?",
"What is an array?",
"What is REST API?",
"What is HTTP?",
"What is database normalization?",
"What is primary key?",
"What is foreign key?",
"What is an algorithm?",
"What is binary search?",
"What is merge sort?",
"What is a hash table?",
"What is Big O notation?"

]


@app.get("/")
def home():
    return {"message": "AI interview platform running"}


@app.get("/get-hr-question")
def get_hr_question():
    question = random.choice(hr_questions)
    return {"question": question}


@app.get("/get-technical-question")
def get_technical_question():
    question = random.choice(technical_questions)
    return {"question": question}

def evaluate_answer(answer, mode):
    answer = answer.lower()
    score = 0
    

    words = answer.split()
    word_count = len(words)

    # content length
    if word_count > 40:
        score += 8
    elif word_count > 20:
        score += 5
    else:
        score += 2

    hr_keywords = ["team","lead","project","experience","learn","responsibility"]

    tech_keywords = [
        "algorithm","complexity","data structure","api",
        "recursion","database","class","object","stack","queue"
    ]

    keywords = hr_keywords if mode == "hr" else tech_keywords

    for k in keywords:
        if k in answer:
            score += 2

    return min(score,20)

@app.post("/submit-answer")
def submit_answer(data: AnswerRequest):
    score = evaluate_answer(data.answer, data.mode)
    answer = data.answer.lower()
    

    word_count = len(answer.split())
    score += min(word_count // 5, 5)

    hr_keywords = ["team", "lead", "responsible", "improve", "learn", "project"]

    technical_keywords = [
        "time complexity","o(","class","object",
        "stack","queue","database","table",
        "recursion","array","linked list",
        "api","http","algorithm"
    ]

    if data.mode.lower() == "hr":
        for word in hr_keywords:
            if word in answer:
                score += 1
    else:
        for word in technical_keywords:
            if word in answer:
                score += 2

    score = min(score,20)

    if score >= 12:
        feedback = "Excellent answer!"
    elif score >= 7:
        feedback = "Good answer but can improve."
    else:
        feedback = "Add more explanation."

    save_interview(data.username,data.mode,data.question,data.answer,score)

    return {
        "score":score,
        "feedback":feedback
    }


@app.get("/get-all-results")
def get_all_results():

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username,mode,question,answer,score FROM interviews")

    rows = cursor.fetchall()
    conn.close()

    results=[]

    for row in rows:
        results.append({
            "username":row[0],
            "mode":row[1],
            "question":row[2],
            "answer":row[3],
            "score":row[4]
        })

    return {"results":results}


@app.get("/get-average-score/{username}")
def get_average_score(username:str):

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("SELECT score FROM interviews WHERE username=?", (username,))
    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return {"message":"No interviews found"}

    scores=[row[0] for row in rows]

    avg=sum(scores)/len(scores)

    return {
        "username":username,
        "total_interviews":len(scores),
        "average_score":round(avg,2),
        "highest_score":max(scores),
        "lowest_score":min(scores)
    }

@app.get("/user-dashboard/{username}")
def user_dashboard(username:str):

    conn = sqlite3.connect("interview.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT mode, score
    FROM interviews
    WHERE username = ?
    """,(username,))

    rows = cursor.fetchall()
    conn.close()

    hr_scores=[]
    tech_scores=[]

    for r in rows:
        if r[0].lower()=="hr":
            hr_scores.append(r[1])
        else:
            tech_scores.append(r[1])

    return {

        "hr_interviews":len(hr_scores),
        "technical_interviews":len(tech_scores),

        "hr_average":round(sum(hr_scores)/len(hr_scores),2) if hr_scores else 0,
        "technical_average":round(sum(tech_scores)/len(tech_scores),2) if tech_scores else 0
    }
@app.get("/leaderboard")
def leaderboard():

    conn=sqlite3.connect("interview.db")
    cursor=conn.cursor()

    cursor.execute("""

    SELECT username,
    AVG(score) as avg_score,
    COUNT(*) as interviews

    FROM interviews

    GROUP BY username

    HAVING interviews >=3

    ORDER BY avg_score DESC

    LIMIT 10

    """)

    rows=cursor.fetchall()
    conn.close()

    data=[]

    rank=1

    for r in rows:

        data.append({

        "rank":rank,
        "username":r[0],
        "average_score":round(r[1],2),
        "interviews":r[2]

        })

        rank+=1

    return {"leaderboard":data}
