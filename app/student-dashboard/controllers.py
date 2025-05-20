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
    return await course_controller["read"]({"batch_id": student[0]["batch_id"]})

async def get_batch_students(batch_id):
    return await user_controller["read"]({"batch_id": batch_id})

async def get_student_progress(student_id):
    return await student_progress_controller["read"]({"student_id": student_id})

async def get_course_students(course_id):
    return await student_course_profile_controller["read"]({"course_id": course_id})

async def get_batch_courses(batch_id):
    return await course_controller["read"]({"batch_id": batch_id})

async def get_student_profile(user_id):
    user = await user_controller["read"]({"id": user_id})