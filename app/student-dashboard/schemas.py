from pydantic import BaseModel, EmailStr
from datetime import datetime, date, time
from typing import Optional

class User(BaseModel):
    id: str
    first_name: str
    last_name: str
    addr: Optional[str]
    phn_num: Optional[str]
    email: EmailStr
    birthdate: Optional[date]
    created_date: datetime
    role_id: str

class AuthUser(BaseModel):
    id: str
    display_name: str
    provider: str
    provider_type: str
    created_at: datetime
    last_sign_in: Optional[datetime]

class Role(BaseModel):
    id: str
    role_name: str

class Batch(BaseModel):
    id: str
    name: str

class RelatedBatch(BaseModel):
    id: str
    user_id: str
    batch_id: str

class StudentProgress(BaseModel):
    id: str
    user_id: str
    course_id: str
    week_number: int
    score: float
    time_spent: float
    completed: bool
    recommended: bool

class StudentCourseProfile(BaseModel):
    id: str
    course_id: str
    student_id: str
    avg_score: float
    total_time_spent: float
    courses_completed: int

class RecommendationLog(BaseModel):
    id: str
    user_id: str
    course_id: str
    time_stamp: datetime
    accepted: bool
    completed: bool
    reward: Optional[float]

class Course(BaseModel):
    id: str
    name: str

class Assigments(BaseModel):
    id: str
    name: str
    user_id: str
    course_id: str
    description: str
    due_date_and_time: datetime
    attachment_url: str
    notified: bool


# class Exams(BaseModel):
#     id: str
#     name: str
#     user_id: str
#     course_id: str
#     description: str
#     date:date
#     start_time: time
#     end_time: time
#     total_marks:int
#     passing_marks:int
    