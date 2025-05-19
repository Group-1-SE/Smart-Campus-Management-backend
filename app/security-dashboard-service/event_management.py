from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime, date, time
from typing import List, Dict, Optional

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_event(
    event_name: str,
    event_date: date,
    start_time: time,
    end_time: time,
    status: str = "scheduled"
) -> Dict:
    """Create a new event."""
    try:
        response = supabase.table("events").insert({
            "event_name": event_name,
            "event_date": event_date.isoformat(),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "status": status
        }).execute()

        if response.data:
            return response.data[0]
        else:
            raise Exception(f"Error creating event: {response.error}")

    except Exception as e:
        print("Error creating event:", e)
        raise

def get_events(status: Optional[str] = None) -> List[Dict]:
    """Get all events, optionally filtered by status."""
    try:
        query = supabase.table("events").select("*").order("event_date", desc=True)
        
        if status:
            query = query.eq("status", status)
            
        response = query.execute()
        return response.data

    except Exception as e:
        print("Error fetching events:", e)
        raise

def get_event(event_id: str) -> Optional[Dict]:
    """Get a specific event by ID."""
    try:
        response = supabase.table("events").select("*").eq("id", event_id).execute()
        
        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        print("Error fetching event:", e)
        raise

def update_event_status(event_id: str, status: str) -> Dict:
    """Update an event's status."""
    try:
        response = supabase.table("events").update({
            "status": status,
            "updated_at": datetime.now().isoformat()
        }).eq("id", event_id).execute()

        if response.data:
            return response.data[0]
        else:
            raise Exception(f"Error updating event: {response.error}")

    except Exception as e:
        print("Error updating event:", e)
        raise

def add_event_guest_vehicle(
    event_id: str,
    plate_number: str,
    name: str,
    reason: Optional[str],
    added_by: str
) -> Dict:
    """Add a guest vehicle to an event."""
    try:
        response = supabase.table("event_guest_vehicles").insert({
            "event_id": event_id,
            "plate_number": plate_number,
            "name": name,
            "reason": reason,
            "added_by": added_by
        }).execute()

        if response.data:
            return response.data[0]
        else:
            raise Exception(f"Error adding guest vehicle: {response.error}")

    except Exception as e:
        print("Error adding guest vehicle:", e)
        raise

def get_event_guest_vehicles(event_id: str) -> List[Dict]:
    """Get all guest vehicles for an event."""
    try:
        response = supabase.table("event_guest_vehicles").select("*").eq("event_id", event_id).execute()
        return response.data

    except Exception as e:
        print("Error fetching event guest vehicles:", e)
        raise

def remove_event_guest_vehicle(event_id: str, plate_number: str) -> None:
    """Remove a guest vehicle from an event."""
    try:
        response = supabase.table("event_guest_vehicles").delete().eq("event_id", event_id).eq("plate_number", plate_number).execute()
        
        if not response.data:
            raise Exception(f"Error removing guest vehicle: {response.error}")

    except Exception as e:
        print("Error removing guest vehicle:", e)
        raise

def check_vehicle_event_authorization(plate_number: str) -> Optional[Dict]:
    """Check if a vehicle is authorized for any active event."""
    try:
        # Get current date and time
        now = datetime.now()
        current_date = now.date().isoformat()
        current_time = now.time().isoformat()

        # Query for active events that include this vehicle
        response = supabase.table("events").select(
            "id, event_name, event_date, start_time, end_time"
        ).eq("status", "active").eq("event_date", current_date).execute()

        if not response.data:
            return None

        # Check if current time is within any active event's time window
        for event in response.data:
            if event["start_time"] <= current_time <= event["end_time"]:
                # Check if vehicle is registered for this event
                vehicle_response = supabase.table("event_guest_vehicles").select(
                    "*"
                ).eq("event_id", event["id"]).eq("plate_number", plate_number).execute()

                if vehicle_response.data:
                    return {
                        "event_id": event["id"],
                        "event_name": event["event_name"],
                        "vehicle": vehicle_response.data[0]
                    }

        return None

    except Exception as e:
        print("Error checking vehicle authorization:", e)
        raise 