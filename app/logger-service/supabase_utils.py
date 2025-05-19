from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def log_vehicle(plate_number: str, status: str, security_clear: bool):
    try:
        # Insert log entry into the Supabase database
        response = supabase.table("vehicle_logs").insert({
            "plate_number": plate_number,
            "status": status,
            "security_clear": security_clear
        }).execute()
        print("Log inserted:", response)
    except Exception as e:
        print("Error logging vehicle:", e)


def log_surveillance_alert(alert_data: dict):
    supabase.table("surveillance_alerts").insert({
        "type": alert_data.get("type"),
        "label": alert_data.get("label"),
        "confidence": alert_data.get("confidence"),
        "location": alert_data.get("location"),
        "timestamp": datetime.now().isoformat()
    }).execute()

