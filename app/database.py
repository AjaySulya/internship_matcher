# internship_matcher/app/database.py

import sqlite3
import threading
import csv
from typing import List, Optional

DB_NAME = "internship_matcher.db"
_lock = threading.Lock()

class SingletonDBConnection:
    _conn = None

    @classmethod
    def get_connection(cls):
        if cls._conn is None:
            cls._conn = sqlite3.connect(DB_NAME, check_same_thread=False)
            cls._conn.row_factory = sqlite3.Row
        return cls._conn

def setup_database():
    with _lock:
        conn = SingletonDBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS internships (
                internship_id INTEGER PRIMARY KEY,
                role TEXT,
                company_name TEXT,
                location TEXT,
                duration TEXT,
                stipend TEXT,
                intern_type TEXT,
                skills_required TEXT,
                hiring_since TEXT,
                opportunity_date TEXT,
                openings INTEGER,
                hired_candidate INTEGER,
                number_of_applications INTEGER
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY,
                name TEXT,
                location TEXT,
                skills TEXT,
                degree TEXT,
                branch TEXT,
                year INTEGER,
                resume_text TEXT,
                preferred_internship_type TEXT,
                availability_duration TEXT
            );
        """)
        conn.commit()

def insert_internship(data: dict):
    with _lock:
        conn = SingletonDBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO internships 
            (internship_id, role, company_name, location, duration, stipend, intern_type, skills_required, hiring_since, opportunity_date, openings, hired_candidate, number_of_applications)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["internship_id"],
            data["role"],
            data["company_name"],
            data["location"],
            data["duration"],
            data.get("stipend"),
            data["intern_type"],
            ",".join(data["skills_required"]) if isinstance(data["skills_required"], list) else data["skills_required"],
            data.get("hiring_since"),
            data.get("opportunity_date"),
            data["openings"],
            data.get("hired_candidate", 0),
            data.get("number_of_applications", 0),
        ))
        conn.commit()

def insert_student(data: dict):
    with _lock:
        conn = SingletonDBConnection.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO students 
            (student_id, name, location, skills, degree, branch, year, resume_text, preferred_internship_type, availability_duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["student_id"],
            data["name"],
            data["location"],
            ",".join(data["skills"]) if isinstance(data["skills"], list) else data["skills"],
            data["education"]["degree"],
            data["education"]["branch"],
            data["education"]["year"],
            data["resume_text"],
            data["preferred_internship_type"],
            data["availability_duration"],
        ))
        conn.commit()

def get_all_internships() -> List[sqlite3.Row]:
    conn = SingletonDBConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM internships")
    return cursor.fetchall()

def get_all_students() -> List[sqlite3.Row]:
    conn = SingletonDBConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    return cursor.fetchall()

def get_internship_by_id(internship_id: int) -> Optional[sqlite3.Row]:
    conn = SingletonDBConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM internships WHERE internship_id = ?", (internship_id,))
    return cursor.fetchone()

def get_student_by_id(student_id: int) -> Optional[sqlite3.Row]:
    conn = SingletonDBConnection.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
    return cursor.fetchone()

def load_csv_to_db(csv_path: str, table: str):
    """
    Loads CSV file into the given table (internships or students) in SQLite.
    Assumes CSV headers might differ and maps them to appropriate table columns.
    """
    header_mapping_internships = {
        "Internship Id": "internship_id",
        "Role": "role",
        "Company Name": "company_name",
        "Location": "location",
        "Duration": "duration",
        "Stipend": "stipend",
        "Intern Type": "intern_type",
        "Skills": "skills_required",
        "Hiring Since": "hiring_since",
        "Opportunity Date": "opportunity_date",
        "Opening": "openings",
        "Hired Candidate": "hired_candidate",
        "Number of Applications": "number_of_applications"
    }

    header_mapping_students = {
        "Student Id": "student_id",
        "Name": "name",
        "Location": "location",
        "Skills": "skills",
        "Degree": "degree",
        "Branch": "branch",
        "Year": "year",
        "Resume Text": "resume_text",
        "Preferred Internship Type": "preferred_internship_type",
        "Availability Duration": "availability_duration"
    }

    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if table == "internships":
                # Map CSV keys to expected DB keys
                mapped_row = {header_mapping_internships.get(k, k): v for k, v in row.items()}

                skills = mapped_row.get("skills_required") or ""
                mapped_row["skills_required"] = skills.replace(";", ",")

                for int_field in ["internship_id", "openings", "hired_candidate", "number_of_applications"]:
                    if mapped_row[int_field]:
                        mapped_row[int_field] = int(mapped_row[int_field])
                    else:
                        mapped_row[int_field] = 0

                insert_internship(mapped_row)

            elif table == "students":
                mapped_row = {header_mapping_students.get(k, k): v for k, v in row.items()}

                skills = mapped_row.get("skills") or ""
                mapped_row["skills"] = skills.replace(";", ",")

                education = {
                    "degree": mapped_row.get("degree"),
                    "branch": mapped_row.get("branch"),
                    "year": int(mapped_row.get("year")) if mapped_row.get("year") else 0
                }
                data = {
                    "student_id": int(mapped_row["student_id"]),
                    "name": mapped_row["name"],
                    "location": mapped_row["location"],
                    "skills": mapped_row["skills"].split(","),
                    "education": education,
                    "resume_text": mapped_row.get("resume_text", ""),
                    "preferred_internship_type": mapped_row.get("preferred_internship_type", ""),
                    "availability_duration": mapped_row.get("availability_duration", "")
                }
                insert_student(data)
