from fastapi import APIRouter, HTTPException
from request_schemas import Record, Filter, UpdateRequest
from controllers import (
    user_controller, auth_user_controller, roles_controller,
    batch_controller, related_batch_controller, student_progress_controller,
    student_course_profile_controller, recommendation_logs_controller, course_controller,
    get_users_by_role, get_student_courses, get_batch_students,
    get_student_progress, get_course_students, get_batch_courses,
    get_student_profile, get_student_course_profile, get_student_course_results
)

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
    "course": course_controller
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
async def get_batch_users(batch_id: int):
    users = await get_batch_students(batch_id)
    if not users:
        raise HTTPException(status_code=404, detail=f"No users found in batch {batch_id}")
    return users

@router.get("/users/{user_id}/profile", tags=["users"])
async def get_user_profile(user_id: int):
    profile = await get_student_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"User profile not found")
    return profile

# Course Management Endpoints
@router.get("/courses/active", tags=["courses"])
async def get_active_courses():
    courses = await course_controller["read"]({"status": "active"})
    if not courses:
        raise HTTPException(status_code=404, detail="No active courses found")
    return courses

@router.get("/courses/batch/{batch_id}", tags=["courses"])
async def get_batch_courses_endpoint(batch_id: int):
    courses = await get_batch_courses(batch_id)
    if not courses:
        raise HTTPException(status_code=404, detail=f"No courses found for batch {batch_id}")
    return courses

@router.get("/courses/student/{student_id}", tags=["courses"])
async def get_student_courses_endpoint(student_id: int):
    courses = await get_student_courses(student_id)
    if not courses:
        raise HTTPException(status_code=404, detail=f"No courses found for student {student_id}")
    return courses

@router.get("/courses/{course_id}/students", tags=["courses"])
async def get_course_students_endpoint(course_id: int):
    students = await get_course_students(course_id)
    if not students:
        raise HTTPException(status_code=404, detail=f"No students found for course {course_id}")
    return students

# Student Progress Endpoints
@router.get("/student-progress/student/{student_id}", tags=["student-progress"])
async def get_student_progress_endpoint(student_id: int):
    progress = await get_student_progress(student_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"No progress found for student {student_id}")
    return progress

@router.get("/student-progress/course/{course_id}", tags=["student-progress"])
async def get_course_progress(course_id: int):
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
async def get_batch_students_endpoint(batch_id: int):
    students = await get_batch_students(batch_id)
    if not students:
        raise HTTPException(status_code=404, detail=f"No students found in batch {batch_id}")
    return students

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