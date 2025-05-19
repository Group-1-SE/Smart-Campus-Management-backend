from fastapi import FastAPI, Query
from typing import Optional
import threading
from fastapi.middleware.cors import CORSMiddleware
from rabbitmq_listener import consume_vehicle_authorized, consume_surveillance_alerts
from supabase_utils import supabase
from alerts_api import router as alerts_router

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include alerts router
app.include_router(alerts_router, prefix="/api")

@app.on_event("startup")
def startup_event():
    threading.Thread(target=consume_vehicle_authorized, daemon=True).start()
    threading.Thread(target=consume_surveillance_alerts, daemon=True).start()

@app.get("/")
def read_root():
    return {"message": "Logger service is running"}

@app.get("/api/vehicles/logs")
async def get_vehicle_logs(plate_number: Optional[str] = Query(None, description="Filter logs by plate number")):
    try:
        query = supabase.table("vehicle_logs").select("*").order("timestamp", desc=True)
        
        if plate_number:
            query = query.eq("plate_number", plate_number)
            
        response = query.execute()
        return response.data
    except Exception as e:
        print("Error fetching vehicle logs:", e)
        return {"error": "Failed to fetch vehicle logs"}, 500
