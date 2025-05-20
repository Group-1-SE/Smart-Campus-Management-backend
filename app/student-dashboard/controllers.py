from models import (
    users_model,
    auth_user_model,
    roles_model,
    batch_model,
    related_batch_model,
    student_progress_model,
    student_course_profile_model,
    recommendation_logs_model,
    course_model
)

# Helper to wrap models as controller logic
def make_controller(model):
    return {
        "create": model["create"],
        "read": model["read"],
        "update": model["update"],
        "delete": model["delete"]
    }
    
# from recommendations.main import get_study_recommendations, get_course_recommendations
from recommendations.openai import get_study_recommendations,  get_course_recommendations

# Define controllers per table
user_controller = make_controller(users_model)
auth_user_controller = make_controller(auth_user_model)
roles_controller = make_controller(roles_model)
batch_controller = make_controller(batch_model)
related_batch_controller = make_controller(related_batch_model)
student_progress_controller = make_controller(student_progress_model)
student_course_profile_controller = make_controller(student_course_profile_model)
recommendation_logs_controller = make_controller(recommendation_logs_model)
course_controller = make_controller(course_model)

async def get_users_by_role(role_name):
    role = await roles_controller["read"]({"role_name": role_name})
    if not role:
        return None
    return await user_controller["read"]({"role_id": role[0]["id"]})

async def get_student_courses(student_id):
    student = await user_controller["read"]({"id": student_id})
    if not student:
        return None
    return await course_controller["read"]({"student_id": student_id})

async def get_batch_students(batch_id):
    # First get all related batch entries for this batch
    related_batches = await related_batch_controller["read"]({"student_id": batch_id})
    if not related_batches:
        return []
    
    # Get user details for each related batch entry
    students = []
    for related_batch in related_batches:
        user = await user_controller["read"]({"id": related_batch["user_id"]})
        if user:
            students.append(user[0])
    
    return students

async def get_student_progress(student_id):
    return await student_progress_controller["read"]({"student_id": student_id})

async def get_course_students(course_id):
    return await student_course_profile_controller["read"]({"course_id": course_id})

async def get_batch_courses(batch_id):
    return await course_controller["read"]({"batch_id": batch_id})

async def get_student_profile(user_id):
    user = await user_controller["read"]({"id": user_id})
    
async def get_student_course_profile(user_id):
    # First get the student's courses
    student = await user_controller["read"]({"id": user_id})
    if not student:
        return None
    
    # Get all course profiles for this student
    course_profiles = await student_course_profile_controller["read"]({"student_id": user_id})
    
    # Get detailed course information for each profile
    detailed_profiles = []
    for profile in course_profiles:
        course = await course_controller["read"]({"id": profile["course_id"]})
        if course:
            detailed_profiles.append({
                "course_profile": profile,
                "course_details": course[0]
            })
    
    return {
        "student_info": student[0],
        "course_profiles": detailed_profiles
    }
    
async def get_student_course_results(student_id):
    # Get student's course profiles
    course_profiles = await student_course_profile_controller["read"]({"student_id": student_id})
    if not course_profiles:
        return {"student_id": student_id, "course_results": []} # Return empty list if no profiles

    # Get course details and format results using available fields
    course_results = []
    for profile in course_profiles:
        course = await course_controller["read"]({"id": profile["course_id"]})
        if course:
            course_results.append({
                "course_name": course[0]["name"],
                "average_score": profile["avg_score"] if "avg_score" in profile else None, # Use avg_score
                # "completed_modules": profile["courses_completed"] if "courses_completed" in profile else 0, # Use courses_completed
                # "semester": course[0]["semester"] if "semester" in course[0] else None
            })

    return {
        "student_id": student_id,
        "course_results": course_results
    }
    
async def get_study_recommendations_controller(student_id):
    # Get student's current courses and progress
    student = await user_controller["read"]({"id": student_id})
    if not student:
        return None
    
    # Get student's current course profiles
    # current_courses = await student_course_profile_controller["read"]({"student_id": student_id})
    
    # # Get recommendation logs for the student
    # recommendations = await recommendation_logs_controller["read"]({"student_id": student_id})
    
    # Get course profile for student
    course_profiles = await get_student_course_profile(student_id)
    
    recommendations = get_study_recommendations(course_profiles)
    
    
    
    return {
        # "student_id": student_id,
        # "current_courses": len(current_courses),
        "recommendations": recommendations,
    }
    
async def get_course_recommendations_controller(student_id):
    # Get student's current courses and progress
    student = await user_controller["read"]({"id": student_id})
    if not student:
        return None
    
    # Get student's current course profiles
    # current_courses = await student_course_profile_controller["read"]({"student_id": student_id})
    
    # # Get recommendation logs for the student
    # recommendations = await recommendation_logs_controller["read"]({"student_id": student_id})
    
    # Get course profile for student
    available_courses = await course_controller["read"]({})
    
    student_courses = await get_student_course_profile(student_id)
    
    transformed = [
    {
        "course_name": item["course_details"]["name"],
        "avg_score": item["course_profile"]["avg_score"],
        "total_time_spent": item["course_profile"]["total_time_spent"]
    }
    for item in student_courses["course_profiles"]
]
    
    recommendations = get_course_recommendations(transformed, available_courses)
    
    
    return {
        # "student_id": student_id,
        # "current_courses": len(current_courses),
        "recommendations": recommendations,
        # "courses": transformed,
        # "available_courses": available_courses
    }