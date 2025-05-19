from supabase import create_client
from datetime import datetime, date, timedelta, time
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
# from decouple import config


load_dotenv()  # This loads variables from the .env file into os.environ

key = os.getenv("SUPABASE_KEY")
url = os.getenv("SUPABASE_URL")

# url = config("SUPABASE_URL")
# key = config("SUPABASE_KEY")


supabase = create_client(url, key)

def get_student_profile(reg_number: str) -> Dict[str, Any]:
    """
    Get a student's profile information by registration number
    
    Args:
        reg_number: The student registration number
        
    Returns:
        Dictionary with student profile data
    """
    try:
        result = supabase.table("Student profiles").select("*").eq("reg_number", reg_number).execute()
        if result.data:
            return {"success": True, "data": result.data[0]}
        else:
            return {"success": False, "message": "Student not found"}
    except Exception as e:
        print(f"Error getting student profile: {e}")
        return {"success": False, "message": str(e)}

def get_student_courses(reg_number: str) -> Dict[str, Any]:
    """
    Get all courses a student is enrolled in
    
    Args:
        reg_number: The student registration number
        
    Returns:
        Dictionary with list of courses
    """
    try:
        # Join Enrollments with Courses to get course details
        result = supabase.table("Enrollments") \
                 .select("Enrollments.id, Enrollments.course_code, Courses(*)") \
                 .eq("reg_number", reg_number) \
                 .execute()
        
        return {"success": True, "data": result.data}
    except Exception as e:
        print(f"Error getting student courses: {e}")
        return {"success": False, "message": str(e)}

def save_face_embedding(reg_number: str, embedding: List[float], name: str = None) -> Dict[str, Any]:
    """
    Save a face embedding to the database
    
    Args:
        reg_number: The student registration number
        embedding: The face embedding as a list of floats
        name: Optional student name
        
    Returns:
        Dictionary with operation result
    """
    try:
        # Check if student already has an embedding
        result = supabase.table('Face_embeddings').select('*').eq('reg_number', reg_number).execute()
        
        # Convert the embedding list to a JSON string
        embedding_json = json.dumps(embedding)
        
        data = {
            'reg_number': reg_number,
            'face_embedding': embedding_json
        }
            
        if result.data:
            # Update existing record
            update_result = supabase.table('Face_embeddings').update(data).eq('reg_number', reg_number).execute()
            return {"success": True, "message": "Face embedding updated"}
        else:
            # Insert new record
            insert_result = supabase.table('Face_embeddings').insert(data).execute()
            return {"success": True, "message": "Face embedding saved"}
    except Exception as e:
        print(f"Error saving face embedding: {e}")
        return {"success": False, "message": str(e)}

def get_all_face_embeddings() -> List[Dict[str, Any]]:
    """
    Get all face embeddings from the database
    
    Returns:
        List of dictionaries with reg_number, name, and embedding
    """
    try:
        # Join with Student profiles to get student name
        result = supabase.table('Face_embeddings') \
            .select('reg_number, face_embedding, "Student profiles"(name)') \
            .execute()
        
        processed_records = []
        # Parse the face_embedding JSON string back to a list
        for record in result.data:
            if 'face_embedding' in record:
                # Access the name from the nested "Student profiles" object
                student_profile = record.get('Student profiles', {})
                student_name = student_profile.get('name', 'Unknown') if student_profile else 'Unknown'
                
                processed_record = {
                    'reg_number': record['reg_number'],
                    'name': student_name,
                    'embedding': json.loads(record['face_embedding'])
                }
                processed_records.append(processed_record)
                
        return processed_records
    except Exception as e:
        print(f"Error getting face embeddings: {e}")
        return []
    

def log_attendance(
    reg_number: str,
    method: str = "face_recognition",  # Keep your original default
    status: str = "present",
    location: str = None,
    course_code: str = None
) -> Dict[str, Any]:
    """
    Log attendance for a student with timestamp and status
    
    Args:
        reg_number: Student registration number
        method: Method of attendance recording
        status: Status of attendance (present, late)
        location: Optional location information
        course_code: Optional course code
        
    Returns:
        Dictionary with attendance result
    """
    try:
        # Validate course code if provided
        if course_code:
            course_check = supabase.table("Courses").select("course_code").eq("course_code", course_code).execute()
            if not course_check.data:
                return {
                    "success": False,
                    "message": f"Course with code '{course_code}' does not exist."
                }

        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Prepare attendance data
        data = {
            "reg_number": reg_number,
            "timestamp": timestamp,  # Add timestamp
            "method": method,
            "status": status
        }

        if location:
            data["location"] = location
        if course_code:
            data["course_code"] = course_code

        # Insert attendance log - using your original table name
        result = supabase.table("Attendance logs").insert(data).execute()
        
        if not result.data:
            return {"success": False, "message": "Failed to log attendance"}
            
        return {
            "success": True,
            "message": f"Attendance marked as {status}",  # Dynamic message
            "data": result.data[0]
        }

    except Exception as e:
        print(f"Error logging attendance: {e}")
        return {"success": False, "message": str(e)}
    
def get_attendance_today(reg_number: str) -> Dict[str, Any]:
    """
    Get today's attendance records for a student
    
    Args:
        reg_number: The student registration number
        
    Returns:
        Dictionary with today's attendance records
    """
    try:
        today = datetime.now().date().isoformat()
        result = supabase.table("Attendance logs") \
                .select("*") \
                .eq("reg_number", reg_number) \
                .gte("timestamp", today) \
                .execute()
                
        return {"success": True, "data": result.data}
    except Exception as e:
        print(f"Error getting attendance: {e}")
        return {"success": False, "message": str(e)}

def get_student_course_attendance_today(reg_number: str, course_code: str) -> Dict[str, Any]:
    """
    Get today's attendance records for a student in a specific course
    
    Args:
        reg_number: Student registration number
        course_code: Course code
    
    Returns:
        Dictionary with attendance records
    """
    try:
        # Get today's date in ISO format (YYYY-MM-DD)
        today = datetime.now().date().isoformat()
        
        # Query for today's attendance for this student and course
        result = supabase.table("Attendance logs") \
                .select("*") \
                .eq("reg_number", reg_number) \
                .eq("course_code", course_code) \
                .gte("timestamp", f"{today}T00:00:00") \
                .lte("timestamp", f"{today}T23:59:59") \
                .execute()
                
        return {"success": True, "data": result.data}
    except Exception as e:
        print(f"Error getting student course attendance: {e}")
        return {"success": False, "message": str(e), "data": None}

def get_course_details(course_code: str) -> Dict[str, Any]:
    """
    Get details for a specific course
    
    Args:
        course_code: The course code
    
    Returns:
        Dictionary with course information
    """
    try:
        result = supabase.table("Courses") \
                .select("course_name, day_of_week, start_time, end_time") \
                .eq("course_code", course_code) \
                .execute()
                
        if not result.data:
            return {"success": False, "message": f"Course {course_code} not found", "data": None}
            
        return {"success": True, "data": result.data[0]}
    except Exception as e:
        print(f"Error getting course details: {e}")
        return {"success": False, "message": str(e), "data": None}

def get_student_attendance_report(reg_number: str, 
                                 start_date: Optional[date] = None, 
                                 end_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Get attendance report for a student within a date range
    
    Args:
        reg_number: The student registration number
        start_date: Start date for the report (default: 30 days ago)
        end_date: End date for the report (default: today)
        
    Returns:
        Dictionary with attendance data
    """
    try:
        if not start_date:
            start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
        else:
            start_date = start_date.isoformat()
            
        if not end_date:
            end_date = datetime.now().date().isoformat()
        else:
            end_date = end_date.isoformat()
        
        result = supabase.table("Attendance logs") \
                .select("*") \
                .eq("reg_number", reg_number) \
                .gte("timestamp", start_date) \
                .lte("timestamp", end_date + "T23:59:59") \
                .execute()
                
        return {"success": True, "data": result.data}
    except Exception as e:
        print(f"Error getting attendance report: {e}")
        return {"success": False, "message": str(e)}
    
# def get_course_attendance_report(course_code: str, 
#                                date_value: Optional[date] = None) -> Dict[str, Any]:
#     """
#     Get attendance report for a specific course on a specific date
    
#     Args:
#         course_code: The course code
#         date_value: The date for the report (default: today)
        
#     Returns:
#         Dictionary with attendance data
#     """
#     try:
#         if not date_value:
#             date_value = datetime.now().date().isoformat()
#         else:
#             date_value = date_value.isoformat()
        
#         # First, get all students enrolled in the course
#         enrollments = supabase.table("Enrollments") \
#                      .select("reg_number") \
#                      .eq("course_code", course_code) \
#                      .execute()
                     
#         if not enrollments.data:
#             return {"success": False, "message": "No students enrolled in this course"}
            
#         # Get reg_numbers of enrolled students
#         reg_numbers = [enrollment["reg_number"] for enrollment in enrollments.data]
        
#         # Get attendance records with student name (requires foreign key relationship)
#         attendance_records = supabase.table("Attendance logs") \
#             .select('attendance_id, reg_number, timestamp, method, status, location, "Student profiles"(name)') \
#             .in_("reg_number", reg_numbers) \
#             .gte("timestamp", date_value) \
#             .lte("timestamp", date_value + "T23:59:59") \
#             .execute()
                           
#         return {"success": True, "data": attendance_records.data}
#     except Exception as e:
#         print(f"Error getting course attendance report: {e}")
#         return {"success": False, "message": str(e)}
    




def get_course_attendance_report(course_code: str, date_value: Optional[date] = None) -> Dict[str, Any]:
    """
    Get attendance report for a specific course on a specific date

    Args:
        course_code: The course code
        date_value: The date for the report (default: today)

    Returns:
        Dictionary with attendance data
    """
    try:
        # Use today's date if none is provided
        if not date_value:
            date_value = datetime.now().date()

        # Create full-day datetime range for the given date
        start_datetime = datetime.combine(date_value, time.min).isoformat()
        end_datetime = datetime.combine(date_value, time.max).isoformat()

        # Step 1: Get all students enrolled in the course
        enrollments = supabase.table("Enrollments") \
            .select("reg_number") \
            .eq("course_code", course_code) \
            .execute()

        if not enrollments.data:
            return {"success": False, "message": "No students enrolled in this course"}

        # Extract reg_numbers of enrolled students
        reg_numbers = [en["reg_number"] for en in enrollments.data]

        # Step 2: Get attendance records for those students on the given date
        attendance_records = supabase.table("Attendance logs") \
            .select("attendance_id, reg_number, timestamp, method, status, location") \
            .in_("reg_number", reg_numbers) \
            .gte("timestamp", start_datetime) \
            .lte("timestamp", end_datetime) \
            .execute()

        # Step 3: Get student names from the Student profiles table
        student_profiles = supabase.table("Student profiles") \
            .select("reg_number, name") \
            .in_("reg_number", reg_numbers) \
            .execute()

        # Build mapping from reg_number to student name
        reg_to_name = {student["reg_number"]: student["name"] for student in student_profiles.data}

        # Step 4: Merge names into attendance records
        for record in attendance_records.data:
            record["name"] = reg_to_name.get(record["reg_number"], "Unknown")

        return {"success": True, "data": attendance_records.data}

    except Exception as e:
        print(f"Error getting course attendance report: {e}")
        return {"success": False, "message": str(e)}

