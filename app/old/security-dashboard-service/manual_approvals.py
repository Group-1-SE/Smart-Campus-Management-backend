# manual_approvals.py
pending_vehicles = []

def add_vehicle(vehicle):
    pending_vehicles.append(vehicle)

def get_all_pending():
    return pending_vehicles

def remove_vehicle(plate_number):
    global pending_vehicles
    pending_vehicles = [v for v in pending_vehicles if v["plate_number"] != plate_number]
