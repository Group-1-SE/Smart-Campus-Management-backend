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

        return bool(guest_result.data)
    
    except Exception as e:
        print(f"Error checking authorization: {e}")
        return False
