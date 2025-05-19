from datetime import datetime
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_authorization(plate_number: str) -> bool:
    try:
        # Check in authorized_vehicles table
        result = supabase.table("authorized_vehicles").select("plate_number").eq("plate_number", plate_number).execute()
        if result.data:
            return True

        # Check in guest_vehicles table with time validation
        now = datetime.now().isoformat()
        guest_result = supabase.table("guest_vehicles").select("*") \
            .eq("plate_number", plate_number) \
            .lte("valid_from", now) \
            .gte("valid_until", now) \
            .execute()

        if guest_result.data:
            return True

        # Check for event-based authorization
        current_date = datetime.now().date().isoformat()
        current_time = datetime.now().time().isoformat()

        # Query for active events that include this vehicle
        event_result = supabase.table("events").select(
            "id, event_name, event_date, start_time, end_time"
        ).eq("status", "active").eq("event_date", current_date).execute()

        if event_result.data:
            # Check if current time is within any active event's time window
            for event in event_result.data:
                if event["start_time"] <= current_time <= event["end_time"]:
                    # Check if vehicle is registered for this event
                    vehicle_result = supabase.table("event_guest_vehicles").select(
                        "*"
                    ).eq("event_id", event["id"]).eq("plate_number", plate_number).execute()

                    if vehicle_result.data:
                        return True

        return False
    
    except Exception as e:
        print(f"Error checking authorization: {e}")
        return False
