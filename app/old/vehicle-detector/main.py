from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from rabbitmq import publish_vehicle_detected

app = FastAPI()

class VehicleEntry(BaseModel):
    plate_number: str
    timestamp: datetime = datetime.now()

@app.post("/detect")
def detect_vehicle(entry: VehicleEntry):
    data = {
        "plate_number": entry.plate_number,
        "timestamp": entry.timestamp.isoformat()
    }
    publish_vehicle_detected(data)
    return {"message": "Vehicle detected", "data": data}
