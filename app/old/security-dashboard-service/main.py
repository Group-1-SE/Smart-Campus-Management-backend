from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import threading
from manual_approvals import get_all_pending, remove_vehicle
from rabbitmq import consume_manual_approvals, send_manual_approval
from guest_pre_auth import insert_guest_vehicle
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def start_consumer():
    thread = threading.Thread(target=consume_manual_approvals)
    thread.daemon = True
    thread.start()

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    vehicles = get_all_pending()
    return templates.TemplateResponse("dashboard.html", {"request": request, "vehicles": vehicles})

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
