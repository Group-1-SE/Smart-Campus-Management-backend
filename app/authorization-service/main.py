from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
from rabbitmq import consume_vehicle_detected
from supabase_utils import supabase

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

def start_rabbitmq_consumer():
    consume_vehicle_detected()

@app.on_event("startup")
def startup_event():
    # Start RabbitMQ consumer in a separate thread to keep FastAPI app responsive
    thread = threading.Thread(target=start_rabbitmq_consumer)
    thread.daemon = True  # Ensure it closes when the main program exits
    thread.start()

@app.get("/")
def read_root():
    return {"message": "Authorization service is running"}

class AuthorizedVehicle(BaseModel):
    plate_number: str
    owner_name: str
    contact_info: str

@app.get("/api/authorized-vehicles")
async def get_authorized_vehicles():
    try:
        result = supabase.table("authorized_vehicles").select("*").execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/authorized-vehicles")
async def add_authorized_vehicle(vehicle: AuthorizedVehicle):
    try:
        # Check if vehicle already exists
        existing = supabase.table("authorized_vehicles").select("*").eq("plate_number", vehicle.plate_number).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Vehicle with this plate number already exists")
        
        # Insert new vehicle
        result = supabase.table("authorized_vehicles").insert(vehicle.dict()).execute()
        return result.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


