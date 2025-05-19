from fastapi import FastAPI
import threading
from rabbitmq_listener import consume_vehicle_authorized, consume_surveillance_alerts

app = FastAPI()

@app.on_event("startup")
def startup_event():
    threading.Thread(target=consume_vehicle_authorized, daemon=True).start()
    threading.Thread(target=consume_surveillance_alerts, daemon=True).start()

@app.get("/")
def read_root():
    return {"message": "Logger service is running"}
