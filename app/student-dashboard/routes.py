from fastapi import APIRouter, HTTPException, Body
from request_schemas import Record, Filter, UpdateRequest
from controllers import (
    user_controller, auth_user_controller, roles_controller,
    batch_controller, related_batch_controller, student_progress_controller,
    student_course_profile_controller, recommendation_logs_controller, course_controller,
    assignments_controller, exams_controller,
    get_users_by_role, get_student_courses, get_batch_students,
    get_student_progress, get_course_students, get_batch_courses,
    get_student_profile, get_assignments_by_course_id,
    get_exams_by_course_id, get_all_exams,
    get_student_profile, get_student_course_profile, get_student_course_results, get_study_recommendations_controller, get_course_recommendations_controller, get_course_data_by_course_id, get_unregistered_students_by_course_id,
    enroll_student_in_course, unenroll_student_from_course, enroll_faculty_in_course, unenroll_faculty_from_course, get_courses_by_faculty_id, update_student_course_mark, create_student_course_profile_with_mark, get_chatbot_response_controller, get_lecturer_chatbot_response_controller
)
from recommendations.main import get_study_recommendations, get_course_recommendations
from typing import List, Dict

router = APIRouter()

# Keep existing table routes
table_routes = {
    "users": user_controller,
    "auth_user": auth_user_controller,
    "roles": roles_controller,
    "batch": batch_controller,
    "related_batch": related_batch_controller,
    "student_progress": student_progress_controller,
    "student_course_profile": student_course_profile_controller,
    "recommendation_logs": recommendation_logs_controller,
    "course": course_controller,
    "assignments": assignments_controller
}

# User Management Endpoints
@router.get("/users/students", tags=["users"])
async def get_all_students():
    students = await get_users_by_role("Student")
    if not students:
        raise HTTPException(status_code=404, detail="No students found")
    return students

@router.get("/users/faculty", tags=["users"])
async def get_all_faculty():
    faculty = await get_users_by_role("Faculty")
    if not faculty:
        raise HTTPException(status_code=404, detail="No faculty found")
    return faculty

@router.get("/users/role/{role_name}", tags=["users"])
async def get_users_by_role_name(role_name: str):
    users = await get_users_by_role(role_name)
    if not users:
        raise HTTPException(status_code=404, detail=f"No users found with role {role_name}")
    return users

@router.get("/users/batch/{batch_id}", tags=["users"])
async def get_batch_users(batch_id: str):
    users = await get_batch_students(batch_id)
    if not users:
        raise HTTPException(status_code=404, detail=f"No users found in batch {batch_id}")
    return users

@router.get("/users/{user_id}/profile", tags=["users"])
async def get_user_profile(user_id: str):
    profile = await get_student_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"User profile not found")
    return profile

# Course Management Endpoints
@router.get("/courses", tags=["courses"])
async def get_all_courses():
    courses = await course_controller["read"]({})
    if not courses:
        raise HTTPException(status_code=404, detail="No active courses found")
    return courses

@router.get("/courses/batch/{batch_id}", tags=["courses"])
async def get_batch_courses_endpoint(batch_id: str):
    courses = await get_batch_courses(batch_id)
    if not courses:
        raise HTTPException(status_code=404, detail=f"No courses found for batch {batch_id}")
    return courses

@router.get("/courses/student/{student_id}", tags=["courses"])
async def get_student_courses_endpoint(student_id: str):
    courses = await get_student_courses(student_id)
    if not courses:
        raise HTTPException(status_code=404, detail=f"No courses found for student {student_id}")
    return courses

@router.get("/courses/{course_id}/students", tags=["courses"])
async def get_course_students_endpoint(course_id: str):
    students = await get_course_students(course_id)
    if not students:
        raise HTTPException(status_code=404, detail=f"No students found for course {course_id}")
    return students

# Student Progress Endpoints
@router.get("/student-progress/student/{student_id}", tags=["student-progress"])
async def get_student_progress_endpoint(student_id: str):
    progress = await get_student_progress(student_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"No progress found for student {student_id}")
    return progress

@router.get("/student-progress/course/{course_id}", tags=["student-progress"])
async def get_course_progress(course_id: str):
    progress = await student_progress_controller["read"]({"course_id": course_id})
    if not progress:
        raise HTTPException(status_code=404, detail=f"No progress found for course {course_id}")
    return progress

# Batch Management Endpoints
# @router.get("/batch/active", tags=["batch"])
# async def get_active_batches():
#     batches = await batch_controller["read"]({"status": "active"})
#     if not batches:
#         raise HTTPException(status_code=404, detail="No active batches found")
#     return batches

@router.get("/batch/{batch_id}/students", tags=["batch"])
async def get_batch_students_endpoint(batch_id: str):
    students = await get_batch_students(batch_id)
    if not students:
        raise HTTPException(status_code=404, detail=f"No students found in batch {batch_id}")
    return students

@router.get("/api/assignments/{course_id}", tags=["assignments"])
async def get_assignments_endpoint(course_id:str):
    assignments = await get_assignments_by_course_id(course_id)
    if not assignments:
        raise HTTPException(status_code=404, detail=f"No students found in course {course_id}")
    return assignments


@router.post("/api/assignments", tags=["assignments"])
async def create_assignment(assignment: dict = Body(...)):
    """
    Create a new assignment.
    The frontend should send a JSON object with the assignment details.
    """
    result = await assignments_controller["create"](assignment)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create assignment")
    return result

@router.get("/api/exams/{course_id}", tags=["exams"])
async def get_exams_endpoint(course_id:str):
    assignments = await get_exams_by_course_id(course_id)
    if not assignments:
        raise HTTPException(status_code=404, detail=f"No exams found in course {course_id}")
    return assignments

@router.get("/api/exams", tags=["exams"])
async def get_all_exams_endpoint():
    exams = await get_all_exams()
    if not exams:
        raise HTTPException(status_code=404, detail="No exams found")
    return exams

@router.post("/api/exams", tags=["exams"])
async def create_exams(exam: dict = Body(...)):
    """
    Create a new assignment.
    The frontend should send a JSON object with the assignment details.
    """
    result = await exams_controller["create"](exam)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create assignment")
    return result
@router.get("/recommendations/study/{student_id}/", tags=["recommendations"])
async def get_student_recommendations_endpoint(student_id: str):
    recommendations = await get_study_recommendations_controller(student_id)
    if not recommendations:
        raise HTTPException(status_code=404, detail=f"No recommendations found for student {student_id}")
    return recommendations

# Define the endpoint for getting course recommendations
@router.post("/recommendations/course/{student_id}/", tags=["recommendations"])
async def get_course_recommendations_endpoint(student_id: str):
    recommendations = await get_course_recommendations_controller(student_id)
    if not recommendations:
        raise HTTPException(status_code=404, detail=f"No recommendations found for student {student_id}")
    return recommendations

@router.get("/courses/{course_id}/data", tags=["courses"]) # Define the new route
async def get_course_data(course_id: str):
    course_data = await get_course_data_by_course_id(course_id)
    if not course_data["students_data"]:
        # Optional: Raise 404 if no students are found, or return the structure with empty list
        # raise HTTPException(status_code=404, detail=f"No data found for course {course_id}")
        pass # Return the empty list as per the controller's design

    return course_data

@router.get("/courses/{course_id}/unregistered-students", tags=["courses"]) # Define the new route
async def get_unregistered_students(course_id: str):
    """
    Retrieves a list of students who are not enrolled in the specified course.
    """
    unregistered_students = await get_unregistered_students_by_course_id(course_id)
    if not unregistered_students:
        raise HTTPException(status_code=404, detail=f"No unregistered students found for course {course_id}")

    return unregistered_students

@router.post("/courses/{course_id}/enroll/{user_id}", tags=["courses"]) # Route for enrolling
async def enroll_student(course_id: str, user_id: str):
    """
    Enrolls a student in the specified course.
    """
    enrollment_result = await enroll_student_in_course(user_id, course_id)
    if not enrollment_result:
        raise HTTPException(status_code=500, detail=f"Failed to enroll student {user_id} in course {course_id}. May already be enrolled or user/course not found.")
    return {"message": "Student enrolled successfully", "enrollment": enrollment_result}

@router.delete("/courses/{course_id}/unenroll/{user_id}", tags=["courses"]) # Route for unenrolling
async def unenroll_student(course_id: str, user_id: str):
    """
    Unenrolls a student from the specified course.
    """
    unenrollment_result = await unenroll_student_from_course(user_id, course_id)
    if not unenrollment_result:
        raise HTTPException(status_code=404, detail=f"Enrollment not found for student {user_id} in course {course_id}")
    return {"message": "Student unenrolled successfully", "unenrollment": unenrollment_result}

@router.post("/courses/{course_id}/enroll/faculty/{user_id}", tags=["courses"]) # Route for enrolling faculty
async def enroll_faculty(course_id: str, user_id: str):
    """
    Associates a faculty member with the specified course.
    """
    enrollment_result = await enroll_faculty_in_course(user_id, course_id)
    if not enrollment_result:
        # The error detail here should reflect the faculty association
        raise HTTPException(status_code=500, detail=f"Failed to associate faculty {user_id} with course {course_id}. May already be associated or user/course not found.")
    return {"message": "Faculty associated successfully", "association": enrollment_result}

@router.delete("/courses/{course_id}/unenroll/faculty/{user_id}", tags=["courses"]) # Route for unenrolling faculty
async def unenroll_faculty(course_id: str, user_id: str):
    """
    Removes the association of a faculty member from the specified course.
    """
    unenrollment_result = await unenroll_faculty_from_course(user_id, course_id)
    if not unenrollment_result:
        # The error detail here should reflect the faculty association
        raise HTTPException(status_code=404, detail=f"Association not found for faculty {user_id} with course {course_id}")
    return {"message": "Faculty association removed successfully", "association": unenrollment_result}

@router.get("/faculty/{faculty_id}/courses", tags=["faculty"]) # Define the new route
async def get_faculty_courses(faculty_id: str):
    """
    Retrieves all courses associated with a given faculty member.
    """
    courses = await get_courses_by_faculty_id(faculty_id)
    if not courses:
        raise HTTPException(status_code=404, detail=f"No courses found for faculty member {faculty_id}")

    return courses

@router.put("/students/{student_id}/courses/{course_id}/mark", tags=["student-progress"]) # Define the new route
async def update_mark_for_student_course(student_id: str, course_id: str, mark: float = Body(..., embed=True)):
    """
    Updates the mark (average score) for a specific student in a specific course.
    """
    updated_record = await update_student_course_mark(student_id, course_id, mark)
    
    # The update controller returns a list of updated records or None/[]
    if not updated_record:
        # Could mean no matching record found for update
        raise HTTPException(status_code=404, detail=f"Student course profile not found for student {student_id} in course {course_id}")
        
    return {"message": "Student mark updated successfully", "updated_profile": updated_record[0]} # Assuming only one record is updated

@router.post("/students/{student_id}/courses/{course_id}/mark", tags=["student-progress"]) # Define the new route for creating a mark
async def create_mark_for_student_course(student_id: str, course_id: str, mark: float = Body(..., embed=True)):
    """
    Creates an initial mark (average score) for a specific student in a specific course.
    Will likely fail if the student_course_profile already exists.
    """
    created_record = await create_student_course_profile_with_mark(student_id, course_id, mark)

    if not created_record:
        # This might indicate a conflict (profile already exists) or other creation error
        raise HTTPException(status_code=400, detail=f"Failed to create student course profile with mark for student {student_id} in course {course_id}. Profile may already exist.")

    # Assuming create returns the created record(s)
    return {"message": "Student mark created successfully", "created_profile": created_record[0]} # Assuming one record is created



# Keep existing table routes
for table, controller in table_routes.items():
    prefix = f"/{table}"
    
    @router.post(prefix, tags=[table])
    async def create_item(record: Record, controller=controller):
        result = await controller["create"](record.data)
        if not result:
            raise HTTPException(status_code=500, detail=f"Failed to create {table}")
        return result

    @router.post(f"{prefix}/read", tags=[table])
    async def read_items(filter: Filter, controller=controller):
        return await controller["read"](filter.filters or {})

    @router.put(prefix, tags=[table])
    async def update_item(update_req: UpdateRequest, controller=controller):
        result = await controller["update"](update_req.filters, update_req.updates)
        if not result:
            raise HTTPException(status_code=404, detail=f"No matching {table} found to update")
        return result

    @router.delete(prefix, tags=[table])
    async def delete_item(filter: Filter, controller=controller):
        result = await controller["delete"](filter.filters or {})
        if not result:
            raise HTTPException(status_code=404, detail=f"No matching {table} found to delete")
        return result
    
    @router.get("/users/{user_id}/course-profile", tags=["users"])
    async def get_user_course_profile(user_id: str):
        profile = await get_student_course_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail=f"Course profile not found for user {user_id}")
        return profile
    
    @router.get("/users/{student_id}/course-results", tags=["users"])
    async def get_student_results(student_id: str):
        results = await get_student_course_results(student_id)
        if not results:
            raise HTTPException(status_code=404, detail=f"No course results found for student {student_id}")
        return results
    
    # ... existing code ...



# Add other endpoints here, e.g., for study recommendations
# from .controllers import fetch_study_recommendations_controller
# from .recommendations.openai import RecommendationsResponse
# @router.post("/study-recommendations", response_model=RecommendationsResponse)
# async def get_study_recommendations_endpoint(
#    course_profiles: List[Dict] = Body(..., description="List of course profiles with progress details")
# ):
#    """
#    Provides study recommendations for the student based on their course progress.
#    """
#    return await fetch_study_recommendations_controller(course_profiles)

# Add this new route
@router.post("/chatbot/chat", tags=["chatbot"])
async def chat_with_bot(
    past_messages: List[Dict] = Body(..., description="List of previous messages"),
    user_message: str = Body(..., description="Current user message"),
    user_id: str = Body(None, description="Optional user ID")
):
    """
    Endpoint for interacting with the university chatbot.
    
    Args:
        past_messages: List of previous messages in the format 
            [{"role": "user/assistant", "content": "message"}, ...]
        user_message: The current message from the user
        user_id: Optional ID of the user making the request
    
    Returns:
        Dict containing the chatbot's response
    """
    response = await get_chatbot_response_controller(past_messages, user_message, user_id)
    if response["status"] == "error":
        raise HTTPException(status_code=500, detail=response["message"])
    return response

# Add this new route
@router.post("/chatbot/lecturer/chat", tags=["chatbot"])
async def chat_with_lecturer_bot(
    past_messages: List[Dict] = Body(..., description="List of previous messages"),
    user_message: str = Body(..., description="Current user message"),
    user_id: str = Body(None, description="Optional user ID")
):
    """
    Endpoint for interacting with the lecturer assistant chatbot.
    
    Args:
        past_messages: List of previous messages in the format 
            [{"role": "user/assistant", "content": "message"}, ...]
        user_message: The current message from the user
        user_id: Optional ID of the user making the request
    
    Returns:
        Dict containing the chatbot's response
    """
    response = await get_lecturer_chatbot_response_controller(past_messages, user_message, user_id)
    if response["status"] == "error":
        raise HTTPException(status_code=500, detail=response["message"])
    return response

        
        