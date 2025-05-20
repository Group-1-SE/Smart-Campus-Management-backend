from models import (
    users_model,
    auth_user_model,
    roles_model,
    batch_model,
    related_batch_model,
    student_progress_model,
    student_course_profile_model,
    recommendation_logs_model,
    course_model,
    assignments_model,
    exams_model,
    enrollment_model,
    faculty_course_profile_model # Import the new model

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
assignments_controller = make_controller(assignments_model)
exams_controller = make_controller(exams_model)
enrollment_controller = make_controller(enrollment_model)
faculty_course_profile_controller = make_controller(faculty_course_profile_model) # Added faculty_course_profile_controller

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

async def get_assignments_by_course_id(course_id):
    return await assignments_controller["read"]({"course_id": course_id})

async def get_exams_by_course_id(course_id):
    return await exams_controller["read"]({"course_id": course_id})

async def get_all_exams():
    return await exams_controller["read"]({})
    
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
    

async def get_course_data_by_course_id(course_id):
    # Find all enrollments for the given course_id
    enrollments = await enrollment_controller["read"]({"course_id": course_id})

    if not enrollments:
        return {"course_id": course_id, "students_data": []}

    students_data = []
    for enrollment in enrollments:
        student_id = enrollment["user_id"]
        enrollment_id = enrollment["id"]

        # Get student details
        student = await user_controller["read"]({"id": student_id})

        # Get grades for this enrollment
        grades = await student_course_profile_controller["read"]({"student_id": student_id, "course_id": course_id})
        if grades:
            grades = grades[0]  # Assuming we want the first record
        else:   
            grades = None

        student_info = student[0] if student else {"id": student_id, "email": "N/A"} # Basic info if student not found

        students_data.append({
            "student_info": student_info,
            "enrollment_id": enrollment_id,
            "data": grades if grades else "" # List of grades for this enrollment
        })

    return {"students_data": students_data}


async def get_unregistered_students_by_course_id(course_id):
    # Get all students
    # Assuming 'Student' role exists and applies to all students
    all_students = await get_users_by_role("Student") # Reusing existing helper

    if not all_students:
        return [] # No students exist at all

    # Get all enrollments for the given course_id
    enrollments = await enrollment_controller["read"]({"course_id": course_id})

    # Create a set of user_ids who are enrolled in this course for quick lookup
    enrolled_student_ids = {enrollment["user_id"] for enrollment in enrollments}

    # Filter all students to find those whose id is NOT in the enrolled_student_ids set
    unregistered_students = [
        student for student in all_students
        if student["id"] not in enrolled_student_ids
    ]

    return unregistered_students

async def enroll_student_in_course(user_id: str, course_id: str):
    """
    Enrolls a student in a specific course by creating an entry in the enrollment table.
    """
    # You might want to add checks here to ensure the user and course exist
    # and that the student is not already enrolled.
    # For now, we'll directly attempt to create the enrollment.

    enrollment_data = {
        "user_id": user_id,
        "course_id": course_id
    }

    # Call the create method of the enrollment controller
    result = await enrollment_controller["create"](enrollment_data)

    # The create method should return the created record or None/error indicator
    return result

async def unenroll_student_from_course(user_id: str, course_id: str):
    """
    Unenrolls a student from a specific course by deleting the entry in the enrollment table.
    """
    # Find the enrollment entry first
    filters = {
        "user_id": user_id,
        "course_id": course_id
    }
    enrollment_to_delete = await enrollment_controller["read"](filters)

    if not enrollment_to_delete:
        return None # Or raise an error indicating no enrollment found

    # Assuming read returns a list, get the ID of the first match
    enrollment_id = enrollment_to_delete[0]["id"]

    # Delete the enrollment entry
    delete_filters = {"id": enrollment_id}
    result = await enrollment_controller["delete"](delete_filters)

    # The delete method should return the deleted record or None/error indicator
    return result

async def enroll_faculty_in_course(user_id: str, course_id: str):
    """
    Associates a faculty member with a specific course by creating an entry
    in the faculty_course_profile table.
    """
    # You might want to add checks here to ensure the user exists and is a faculty member
    # and that the faculty member is not already associated with the course.

    association_data = {
        "faculty_id": user_id, # Use faculty_id as per schema
        "course_id": course_id
    }

    # Call the create method of the faculty_course_profile controller
    result = await faculty_course_profile_controller["create"](association_data)

    return result

async def unenroll_faculty_from_course(user_id: str, course_id: str):
    """
    Removes the association of a faculty member from a specific course
    by deleting the entry in the faculty_course_profile table.
    """
    # Find the association entry first
    filters = {
        "faculty_id": user_id, # Use faculty_id as per schema
        "course_id": course_id
    }
    association_to_delete = await faculty_course_profile_controller["read"](filters)

    if not association_to_delete:
        return None # Or raise an error indicating no association found

    # Delete the association entry using the filters
    # The delete_record function in database.py should handle deleting based on filters
    delete_filters = filters # Use the same filters to find and delete
    result = await faculty_course_profile_controller["delete"](delete_filters)

    return result
