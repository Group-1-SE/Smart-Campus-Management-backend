from database import create_record, read_records, update_record, delete_record

# Helper to generate model functions per table
def make_model(table_name):
    return {
        "create": lambda data: create_record(table_name, data),
        "read": lambda filters: read_records(table_name, filters),
        "update": lambda filters, updates: update_record(table_name, filters, updates),
        "delete": lambda filters: delete_record(table_name, filters),
    }

# Define models per table
users_model = make_model("users")
auth_user_model = make_model("auth_user")
roles_model = make_model("roles")
batch_model = make_model("batch")
related_batch_model = make_model("related_batch")
student_progress_model = make_model("student_progress")
student_course_profile_model = make_model("student_course_profile")
recommendation_logs_model = make_model("recommendation_logs")
course_model = make_model("course")
assignments_model = make_model("assignments")
exams_model = make_model("exams")