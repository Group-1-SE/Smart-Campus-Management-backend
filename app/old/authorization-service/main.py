from fastapi import FastAPI
import threading
from rabbitmq import consume_vehicle_detected

app = FastAPI()

def start_rabbitmq_consumer():
    consume_vehicle_detected()

@app.on_event("startup")
def startup_event():
    # Start RabbitMQ consumer in a separate thread to keep FastAPI app responsive
    print("Starting RabbitMQ consumer thread...")
    thread = threading.Thread(target=start_rabbitmq_consumer)
    thread.daemon = True  # Ensure it closes when the main program exits
    thread.start()

@app.get("/")
def read_root():
    return {"message": "Authorization service is running"}


