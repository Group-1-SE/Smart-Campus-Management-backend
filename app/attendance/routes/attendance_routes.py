from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import date


from pydantic import BaseModel, Field
from models.schemas import (
    FaceRegisterRequest, 
    FaceRecognitionRequest,
    ManualAttendanceRequest, 
    FaceRecognitionResponse, 
    AttendanceRecord, 
    AttendanceResponse, 
    AttendanceMethod, 
    AttendanceStatus,
    ApiResponse, 
    StudentAttendanceReport, 
    CourseAttendanceReport, 
    AttendanceReportRequest,
    AttendanceResult,
    courseReportRequest
)

from services.face_service import register_face, recognize_faces
from db.supabase import (
    log_attendance, 
    get_student_profile, 
    get_student_attendance_report,
    get_course_attendance_report,
    get_attendance_today
)
from services.attendace_logic import can_mark_attendance,can_mark_attendance_for_course

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/manual", response_model=AttendanceResponse)
async def mark_manual_attendance(request: ManualAttendanceRequest):
    """
    Manually mark attendance for a student based on course schedule
    """
    # Verify student exists
    student = get_student_profile(request.reg_number)
    if not student["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=student["message"]
        )
    
    # Check if student can mark attendance based on course schedule
    if request.course_code:
        # Use the new course-based attendance logic
        attendance_check = can_mark_attendance_for_course(
            reg_number=request.reg_number,
            course_code=request.course_code
        )
        
        # Use the status from attendance check if not explicitly provided
        # This ensures consistent rules when the status isn't manually specified
        if attendance_check["can_mark"] and not request.status and attendance_check.get("status"):
            request.status = attendance_check["status"]
    else:
        # Fallback to original attendance logic if no course provided
        attendance_check = can_mark_attendance(request.reg_number)
    
    # If attendance cannot be marked, return with explanation
    if not attendance_check["can_mark"]:
        return AttendanceResponse(
            success=False,
            message=attendance_check["message"]
        )
    
    # Log the attendance
    result = log_attendance(
        reg_number=request.reg_number,
        method=AttendanceMethod.MANUAL,
        status=request.status or "present",  # Default to present if not specified
        location=request.location,
        course_code=request.course_code
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    # Include attendance status in the success message
    status_message = request.status or "present"
    
    return AttendanceResponse(
        success=True,
        message=f"Attendance marked as {status_message} for student {request.reg_number}" +
                (f" in course {request.course_code}" if request.course_code else ""),
        data=AttendanceRecord(**result["data"])
    )

@router.post("/recognize", response_model=FaceRecognitionResponse)
async def recognize_student_faces(request: FaceRecognitionRequest):
    """
    Recognize students in an image and mark attendance if applicable
    """
    result = recognize_faces(request.image_base64, request.location, request.course_code)
    
    # Convert raw attendance results to proper model objects
    attendance_results = []
    if "attendance_results" in result and result["attendance_results"]:
        for ar in result["attendance_results"]:
            attendance_results.append(AttendanceResult(
                reg_number=ar["reg_number"],
                name=ar["name"],
                attendance_result=ar["attendance_result"]
            ))
    
    # Create a properly structured response with all fields
    return FaceRecognitionResponse(
        success=result["success"],
        message=result["message"],
        total_faces_detected=result.get("total_faces_detected", 0),
        recognized_count=result.get("recognized_count", 0),
        unknown_count=result.get("unknown_count", 0),
        students=result.get("students", []),
        unknown_faces=result.get("unknown_faces", []),
        attendance_results=attendance_results
    )

# Face registration endpoint
@router.post("/register-face", response_model=ApiResponse)
async def register_student_face(request: FaceRegisterRequest):
    """
    Register a student's face for facial recognition attendance
    """
    result = register_face(request.reg_number, request.image_base64)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return ApiResponse(success=True, message=result["message"])
# Get today's attendance for a student


@router.get("/today/{reg_number}", response_model=ApiResponse)
async def get_today_attendance(reg_number: str):
    """
    Get today's attendance records for a specific student
    """
    # Verify student exists
    student = get_student_profile(reg_number)
    if not student["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=student["message"]
        )
    
    result = get_attendance_today(reg_number)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return ApiResponse(
        success=True,
        message=f"Retrieved today's attendance for student {reg_number}",
        data=result["data"]
    )

# Get student attendance report
@router.post("/report/student", response_model=ApiResponse)
async def get_student_report(request: AttendanceReportRequest):
    """
    Get attendance report for a specific student within a date range
    """
    if not request.reg_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration number is required"
        )
    
    # Verify student exists
    student = get_student_profile(request.reg_number)
    if not student["success"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=student["message"]
        )
    
    result = get_student_attendance_report(
        reg_number=request.reg_number,
        start_date=request.start_date,
        end_date=request.end_date
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    # Process attendance data to create summary
    attendance_records = [AttendanceRecord(**record) for record in result["data"]]
    
    # Create summary of attendance statuses
    summary = {
        "present": sum(1 for record in attendance_records if record.status == AttendanceStatus.PRESENT),
        "absent": sum(1 for record in attendance_records if record.status == AttendanceStatus.ABSENT),
        "late": sum(1 for record in attendance_records if record.status == AttendanceStatus.LATE),
        "total": len(attendance_records)
    }
    
    report = StudentAttendanceReport(
        reg_number=request.reg_number,
        name=student["data"].get("name"),
        records=attendance_records,
        summary=summary
    )
    
    return ApiResponse(
        success=True,
        message=f"Retrieved attendance report for student {request.reg_number}",
        data=report
    )

# @router.post("/report/course", response_model=ApiResponse)
# async def get_course_report(request: AttendanceReportRequest):
#     """
#     Get attendance report for a specific course on a specific date
#     """
#     if not request.course_code:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Course code is required"
#         )
    
#     result = get_course_attendance_report(
#         course_code=request.course_code,
#         date_value=request.start_date
#     )
    
#     if not result["success"]:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=result["message"]
#         )
    
#     return ApiResponse(
#         success=True,
#         message=f"Retrieved attendance report for course {request.course_code}",
#         data=result["data"]
#     )

@router.post("/report/course", response_model=ApiResponse)
async def get_course_report(request: courseReportRequest):
    """
    Get attendance report for a specific course on a specific date
    """
    if not request.course_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code is required"
        )
    
    result = get_course_attendance_report(
        course_code=request.course_code,
        date_value=request.start_date
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )
    
    return ApiResponse(
        success=True,
        message=f"Retrieved attendance report for course {request.course_code}",
        data=result["data"]
    )
