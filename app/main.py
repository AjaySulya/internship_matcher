from fastapi import FastAPI, HTTPException
from typing import List
from app.models import InternshipCreate, StudentCreate, RecommendationRequest, InternshipResponse, StudentResponse
from app.database import setup_database, insert_internship, insert_student, get_all_internships, get_all_students, get_internship_by_id, get_student_by_id, load_csv_to_db
from app.recommender import Recommender
from app.utils import str_to_list
import threading
import os
import logging

logger = logging.getLogger("uvicorn")

app = FastAPI(title="Candidate–Internship Matching System")

setup_database()

recommender = Recommender()
model_lock = threading.Lock()

def refresh_model():
    internships_raw = get_all_internships()
    internships_list = []
    for row in internships_raw:
        internships_list.append({
            "internship_id": row["internship_id"],
            "role": row["role"],
            "company_name": row["company_name"],
            "location": row["location"],
            "duration": row["duration"],
            "stipend": row["stipend"],
            "intern_type": row["intern_type"],
            "skills_required": str_to_list(row["skills_required"]),
            "hiring_since": row["hiring_since"],
            "opportunity_date": row["opportunity_date"],
            "openings": row["openings"],
            "hired_candidate": row["hired_candidate"],
            "number_of_applications": row["number_of_applications"]
        })
    with model_lock:
        recommender.fit(internships_list)

@app.get("/")
def read_root():
    return {"message": "Candidate–Internship Matching System API is running."}

@app.on_event("startup")
def startup_event():
    logger.info("Starting up application")
    setup_database()
    try:
        if not get_all_internships():
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            load_csv_to_db(os.path.join(base_dir, "data", "internships.csv"), "internships")
            load_csv_to_db(os.path.join(base_dir, "data", "students.csv"), "students")
            logger.info("Loaded CSV data into database")
    except Exception as e:
        logger.error(f"Error loading CSV files: {e}")
    refresh_model()
    logger.info("Application startup completed")

@app.post("/add_internship", response_model=InternshipResponse)
def add_internship(internship: InternshipCreate):
    insert_internship(internship.dict())
    refresh_model()
    return internship

@app.post("/add_student", response_model=StudentResponse)
def add_student(student: StudentCreate):
    insert_student(student.dict())
    return student

@app.post("/recommend", response_model=List[InternshipResponse])
def recommend_internships(req: RecommendationRequest):
    student_row = get_student_by_id(req.student_id)
    if not student_row:
        raise HTTPException(status_code=404, detail="Student not found")

    student_profile = {
        "student_id": student_row["student_id"],
        "name": student_row["name"],
        "location": student_row["location"],
        "skills": str_to_list(student_row["skills"]),
        "education": {
            "degree": student_row["degree"],
            "branch": student_row["branch"],
            "year": student_row["year"]
        },
        "resume_text": student_row["resume_text"],
        "preferred_internship_type": student_row["preferred_internship_type"],
        "availability_duration": student_row["availability_duration"],
    }

    with model_lock:
        recommendations = recommender.recommend_internships(student_profile)

    response = [InternshipResponse(**rec) for rec in recommendations]
    return response

@app.get("/match_candidates/{internship_id}", response_model=List[StudentResponse])
def match_candidates(internship_id: int):
    internship_row = get_internship_by_id(internship_id)
    if not internship_row:
        raise HTTPException(status_code=404, detail="Internship not found")

    internship_profile = {
        "internship_id": internship_row["internship_id"],
        "role": internship_row["role"],
        "company_name": internship_row["company_name"],
        "location": internship_row["location"],
        "duration": internship_row["duration"],
        "stipend": internship_row["stipend"],
        "intern_type": internship_row["intern_type"],
        "skills_required": str_to_list(internship_row["skills_required"]),
        "hiring_since": internship_row["hiring_since"],
        "opportunity_date": internship_row["opportunity_date"],
        "openings": internship_row["openings"],
        "hired_candidate": internship_row["hired_candidate"],
        "number_of_applications": internship_row["number_of_applications"],
    }

    students_raw = get_all_students()
    students_list = []
    for row in students_raw:
        students_list.append({
            "student_id": row["student_id"],
            "name": row["name"],
            "location": row["location"],
            "skills": str_to_list(row["skills"]),
            "education": {
                "degree": row["degree"],
                "branch": row["branch"],
                "year": row["year"]
            },
            "resume_text": row["resume_text"],
            "preferred_internship_type": row["preferred_internship_type"],
            "availability_duration": row["availability_duration"],
        })

    with model_lock:
        matched_students = recommender.match_candidates(internship_profile, students_list)

    return [StudentResponse(**student) for student in matched_students]

