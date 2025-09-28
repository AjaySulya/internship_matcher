from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class InternshipBase(BaseModel):
    role: str
    company_name: str
    location: str
    duration: str
    stipend: Optional[str] = None
    intern_type: str  # Remote/On-site/Hybrid
    skills_required: List[str]
    hiring_since: Optional[date] = None
    opportunity_date: Optional[date] = None
    openings: int
    hired_candidate: Optional[int] = 0
    number_of_applications: Optional[int] = 0

class InternshipCreate(InternshipBase):
    internship_id: int = Field(..., description="Unique Internship Id")

class InternshipResponse(InternshipCreate):
    pass

class Education(BaseModel):
    degree: str
    branch: str
    year: int

class StudentBase(BaseModel):
    name: str
    location: str
    skills: List[str]
    education: Education
    resume_text: str
    preferred_internship_type: str  # Remote/On-site/Hybrid
    availability_duration: str

class StudentCreate(StudentBase):
    student_id: int = Field(..., description="Unique Student Id")

class StudentResponse(StudentCreate):
    pass

class RecommendationRequest(BaseModel):
    student_id: int
