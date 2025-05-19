from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum


class AttendanceMethod(str, Enum):
    FACE_RECOGNITION = "facial recognition"
    MANUAL = "manual"


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class ManualAttendanceRequest(BaseModel):
    reg_number: str
    status: AttendanceStatus = AttendanceStatus.PRESENT
    location: Optional[str] = None
    course_code: str

class courseReportRequest(BaseModel):
    course_code: str
    start_date: Optional[date]

class StudentProfile(BaseModel):
    reg_number: str
    name: Optional[str] = None
    faculty: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    semester: Optional[int] = None


class Course(BaseModel):
    course_code: str
    course_name: Optional[str] = None
    description: Optional[str] = None


class Enrollment(BaseModel):
    id: Optional[int] = None
    reg_number: str
    course_code: str


class AttendanceRecord(BaseModel):
    attendance_id: Optional[int] = None
    reg_number: str
    timestamp: datetime = Field(default_factory=datetime.now)
    method: AttendanceMethod = AttendanceMethod.MANUAL
    status: AttendanceStatus = AttendanceStatus.PRESENT
    location: Optional[str] = None


class AttendanceResponse(BaseModel):
    success: bool
    message: str
    data: Optional[AttendanceRecord] = None


class FaceRegisterRequest(BaseModel):
    reg_number: str
    image_base64: str


class FaceEmbedding(BaseModel):
    reg_number: str
    embedding: List[float]
    name: Optional[str] = None


class FaceRecognitionRequest(BaseModel):
    image_base64: str
    location: Optional[str] = None
    course_code: str

class RecognizedStudent(BaseModel):
    reg_number: str
    name: str
    confidence: float
    can_mark_attendance: Optional[bool] = None
    attendance_message: Optional[str] = None
    attendance_status: Optional[str] = None
    face_location: Optional[List[int]] = None

# Unknown face model
class UnknownFace(BaseModel):
    face_index: int
    location: Optional[List[int]] = None
    confidence: float = 0
    best_match_name: Optional[str] = None
    message: str = "Unknown person"

class AttendanceResult(BaseModel):
    reg_number: str
    name: str
    attendance_result: Dict[str, Any]

class FaceRecognitionResponse(BaseModel):
    success: bool
    message: str
    total_faces_detected: Optional[int] = None
    recognized_count: Optional[int] = None
    unknown_count: Optional[int] = None
    students: List[RecognizedStudent] = []
    unknown_faces: Optional[List[UnknownFace]] = None
    attendance_results: Optional[List[AttendanceResult]] = None

class StudentAttendanceReport(BaseModel):
    reg_number: str
    name: Optional[str] = None
    records: List[AttendanceRecord]
    summary: Dict[str, int]  # e.g., {"present": 10, "absent": 2, "late": 1}


class CourseAttendanceReport(BaseModel):
    course_code: str
    date: date
    total_enrolled: int
    present: int
    absent: int
    late: int
    students: List[Dict[str, Any]]  # List of students with their attendance status


class AttendanceReportRequest(BaseModel):
    reg_number: Optional[str] = None
    course_code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None


class StudentEnrollmentResponse(BaseModel):
    success: bool
    message: str
    student: Optional[StudentProfile] = None
    courses: Optional[List[Course]] = None


