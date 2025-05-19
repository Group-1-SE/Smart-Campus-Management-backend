from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import threading
from manual_approvals import get_all_pending, remove_vehicle
from rabbitmq import consume_manual_approvals, send_manual_approval
from guest_pre_auth import insert_guest_vehicle
from event_management import (
    create_event,
    get_events,
    get_event,
    update_event_status,
    add_event_guest_vehicle,
    get_event_guest_vehicles,
    remove_event_guest_vehicle
)
from datetime import datetime, date, time
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start_consumer():
    thread = threading.Thread(target=consume_manual_approvals)
    thread.daemon = True
    thread.start()

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    vehicles = get_all_pending()
    return templates.TemplateResponse("dashboard.html", {"request": request, "vehicles": vehicles})

@app.get("/api/vehicles/pending")
def get_pending_vehicles():
    return JSONResponse(content=get_all_pending())

@app.post("/approve/{plate_number}")
def approve_vehicle(plate_number: str):
    vehicles = get_all_pending()
    for vehicle in vehicles:
        if vehicle["plate_number"] == plate_number:
            send_manual_approval(vehicle)
            remove_vehicle(plate_number)
            break
    return RedirectResponse(url="/", status_code=303)

@app.post("/add-guest-vehicle")
def add_guest_vehicle(
    plate_number: str = Form(...),
    name: str = Form(...),
    reason: str = Form(None),  
    valid_from: str = Form(...),  
    valid_until: str = Form(...), 
    added_by: str = Form(...)  
):
    valid_from_dt = datetime.strptime(valid_from, "%Y-%m-%dT%H:%M")
    valid_until_dt = datetime.strptime(valid_until, "%Y-%m-%dT%H:%M")

    # Call the function to insert the guest vehicle into the database
    insert_guest_vehicle(plate_number, name, reason, valid_from, valid_until, added_by)
    return RedirectResponse(url="/", status_code=303)

# Event-related endpoints
@app.post("/api/events")
async def create_new_event(
    event_name: str = Form(...),
    event_date: str = Form(...),
    start_time: str = Form(...),
    end_time: str = Form(...)
):
    try:
        event_date_obj = datetime.strptime(event_date, "%Y-%m-%d").date()
        start_time_obj = datetime.strptime(start_time, "%H:%M").time()
        end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        
        event = create_event(event_name, event_date_obj, start_time_obj, end_time_obj)
        return JSONResponse(content=event)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/events")
async def list_events(status: Optional[str] = None):
    try:
        events = get_events(status)
        return JSONResponse(content=events)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/{event_id}")
async def get_event_details(event_id: str):
    try:
        event = get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return JSONResponse(content=event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/events/{event_id}/status")
async def update_event_status_endpoint(event_id: str, status: str = Form(...)):
    try:
        if status not in ["scheduled", "active", "expired"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        
        event = update_event_status(event_id, status)
        return JSONResponse(content=event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/{event_id}/vehicles")
async def add_vehicle_to_event(
    event_id: str,
    plate_number: str = Form(...),
    name: str = Form(...),
    reason: Optional[str] = Form(None),
    added_by: str = Form(...)
):
    try:
        vehicle = add_event_guest_vehicle(event_id, plate_number, name, reason, added_by)
        return JSONResponse(content=vehicle)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/{event_id}/vehicles")
async def list_event_vehicles(event_id: str):
    try:
        vehicles = get_event_guest_vehicles(event_id)
        return JSONResponse(content=vehicles)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/events/{event_id}/vehicles/{plate_number}")
async def remove_vehicle_from_event(event_id: str, plate_number: str):
    try:
        remove_event_guest_vehicle(event_id, plate_number)
        return JSONResponse(content={"message": "Vehicle removed successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
