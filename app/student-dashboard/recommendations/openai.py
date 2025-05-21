import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
from pydantic import BaseModel, Field


# Load environment variables
load_dotenv()


class CourseRecommendation(BaseModel):
    course_name: str = Field(..., description="Name of the course")
    current_progress: str = Field(..., description="Description on current progress")
    study_recommendation: str = Field(..., description="A specific study recommendation for the course")

class RecommendationsResponse(BaseModel):
    overall_recommendation: str = Field(..., description="Overall recommendation for the student")
    recommendations: List[CourseRecommendation] = Field(..., description="List of course recommendations")

class RecommendedCourse(BaseModel):
    course_name: str = Field(..., description="Name of the recommended course")
    description: str = Field(..., description="Description of the course")
    relevance: str = Field(..., description="Why this course is relevant to the student")

class CourseRecommendationsResponse(BaseModel):
    overall_recommendation: str = Field(..., description="Overall recommendation for course selection")
    recommended_courses: List[RecommendedCourse] = Field(..., description="List of recommended courses")

class StudentPerformance(BaseModel):
    student_id: str = Field(..., description="Student's registration number")
    student_name: str = Field(..., description="Student's full name")
    grade: float = Field(..., description="Student's grade in the course")
    attendance_rate: float = Field(..., description="Student's attendance rate in the course")
    participation_score: float = Field(..., description="Student's participation score")

class LecturerFeedback(BaseModel):
    course_name: str = Field(..., description="Name of the course")
    overall_performance: str = Field(..., description="Overall performance analysis of the class")
    performance_metrics: Dict[str, float] = Field(..., description="Key performance metrics for the class")
    recommendations: List[str] = Field(..., description="Recommendations for improving student performance")
    individual_feedback: List[StudentPerformance] = Field(..., description="Individual student performance analysis")


def get_study_recommendations(course_profiles: List[Dict]) -> List[Dict]:
    print("Getting study recommendations based on course profiles...")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print(os.getenv("OPENAI_API_KEY"))
    
    # Prepare the prompt for OpenAI
    prompt = f"""Based on the following course profiles, provide structured recommendations for each course.
    For each course, provide:
    1. A description of current progress
    2. A specific study recommendation
    
    Course Profiles:
    {course_profiles}
    
    Format the response as a JSON object with the following structure:
    {{
        "overall_recommendation": "string (provide an overall recommendation for the student's academic journey)",
        "recommendations": [
            {{
                "course_name": "string",
                "current_progress": "string (describe the current progress in the course)",
                "study_recommendation": "string (provide a specific recommendation for this course)"
            }},
            ...
        ]
    }}
    
    Make the recommendations specific, actionable, and encouraging. The overall_recommendation should provide 
    a holistic view of the student's academic journey and general advice for improvement.
    Do not mention their name. Word it as if you are talking to them in person"""
    
    try:
        # Call OpenAI API
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        prompt
                    )
                },
                {
                    "role": "user",
                    "content": f"{course_profiles}"
                }
            ],
            response_format=RecommendationsResponse,
        )

        # event = completion.choices[0].message.parsed
        
        # Parse the response into our Pydantic model
        recommendations_data = completion.choices[0].message.parsed
        return recommendations_data
        
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
        return RecommendationsResponse(
            overall_recommendation="Unable to generate recommendations at this time. Please try again later.",
            recommendations=[
                CourseRecommendation(
                    course_name="Error",
                    current_progress="Unable to assess progress",
                    study_recommendation="Please try again later"
                )
            ]
        )
        
def get_course_recommendations(available_courses: List[Dict], current_courses: Dict) -> CourseRecommendationsResponse:
    print("Getting course recommendations based on current courses and academic profile...")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Prepare the prompt for OpenAI
    prompt = f"""Based on the student's current courses and academic profile, recommend about 4-5 courses they should consider taking.
    Consider their interests, strengths, and academic goals.
    
    Available Courses:
    {available_courses}
    
    Academic Profile:
    {current_courses}
    
    Format the response as a JSON object with the following structure:
    {{
        "overall_recommendation": "string (provide an overall recommendation for course selection)",
        "recommended_courses": [
            {{
                "course_name": "string",
                "description": "string (brief description of the course)",
                "relevance": "string (explain why this course would be beneficial)",
            }},
            ...
        ]
    }}
    
    Make the recommendations specific and relevant to the student's academic journey.
    Relevance field should be able 2-3 sentences long.
    Consider their current course load and academic standing.
    Do not recommend courses they are already taking.
    Do not mention their name. Word it as if you are talking to them in person."""
    
    try:
        # Call OpenAI API
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        prompt
                    )
                },
                {
                    "role": "user",
                    "content": f"Current Courses: {current_courses}\nAvailable courses: {available_courses}"
                }
            ],
            response_format=CourseRecommendationsResponse,
        )
        
        # print(completion)

        # Parse the response into our Pydantic model
        recommendations_data = completion.choices[0].message.parsed
        return recommendations_data
        
    except Exception as e:
        print(f"Error getting course recommendations: {str(e)}")
        return CourseRecommendationsResponse(
            overall_recommendation="Unable to generate course recommendations at this time. Please try again later.",
            recommended_courses=[
                RecommendedCourse(
                    course_name="Error",
                    description="Unable to generate recommendations",
                    relevance="Please try again later",
                    prerequisites=[]
                )
            ]
        )
        
        