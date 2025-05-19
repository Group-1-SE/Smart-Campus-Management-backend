# guest_pre_auth.py
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_guest_vehicle(
    plate_number: str, 
    owner_name: str, 
    reason: str, 
    valid_from: str, 
    valid_until: str, 
    added_by: str
):
    try:
        print("Adding guest vehicle to the database...")
        # print(plate_number, reason, added_by, valid_from, valid_until)
        response = supabase.table("guest_vehicles").insert({
            "plate_number": plate_number,
            "name": owner_name,
            "reason": reason,
            "valid_from": valid_from,
            "valid_until": valid_until,
            "added_by": added_by
        }).execute()
        
        print("Response from Supabase:", response)

        if response.status_code == 201:
            print("Guest vehicle added successfully:", response)
        else:
            print("Error adding guest vehicle:", response)

    except Exception as e:
        print("Error inserting guest vehicle:", e)