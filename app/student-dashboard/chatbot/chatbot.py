import os
from typing import List, Dict
import openai
from dotenv import load_dotenv
from openai import OpenAI


# Load environment variables
load_dotenv()

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_chatbot_response(past_messages: List[Dict], user_message: str) -> str:
    """
    Get a response from the university chatbot.
    
    Args:
        past_messages (List[Dict]): List of previous messages in the format 
            [{"role": "user/assistant", "content": "message"}, ...]
        user_message (str): The current user message to respond to
    
    Returns:
        str: The chatbot's response
    """
    try:
        # System prompt defining the chatbot's role
        system_prompt = """You are a helpful university assistant chatbot. Your role is to help students with:
        - Course information and registration
        - Campus facilities and services
        - Academic deadlines and requirements
        - General university policies
        - Study tips and academic support
        - Campus events and activities
        
        Always be professional, friendly, and provide accurate information. If you're unsure about something, 
        acknowledge that and suggest contacting the relevant department."""

        # Prepare all messages for the API call
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(past_messages)
        # print(past_messages)
        messages.append({"role": "user", "content": user_message})

        print(messages)
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,

        )

        return response.choices[0].message.content

    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}"

# # Example usage
# if __name__ == "__main__":
#     # Example past messages
#     past_messages = [
#         {"role": "user", "content": "What are the library hours?"},
#         {"role": "assistant", "content": "The library is open Monday to Friday from 8 AM to 10 PM, and weekends from 10 AM to 6 PM."},
#         {"role": "user", "content": "Is there a quiet study area?"},
#         {"role": "assistant", "content": "Yes, there are designated quiet study zones on the 3rd and 4th floors of the library."}
#     ]
    
#     # Get user input
#     user_input = input("You: ")
#     response = get_chatbot_response(past_messages, user_input)
#     print(f"University Assistant: {response}")