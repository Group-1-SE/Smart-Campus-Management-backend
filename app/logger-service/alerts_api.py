from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from supabase_utils import supabase
from pydantic import BaseModel

router = APIRouter()

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    team_dispatched: Optional[bool] = None

@router.get("/alerts")
async def get_alerts(status: Optional[str] = None):
    query = supabase.table("surveillance_alerts").select("*").order("timestamp", desc=True)
    
    if status:
        query = query.eq("status", status)
    
    response = query.execute()
    return response.data

@router.get("/alerts/{alert_id}")
async def get_alert(alert_id: str):
    response = supabase.table("surveillance_alerts").select("*").eq("id", alert_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return response.data[0]

@router.patch("/alerts/{alert_id}")
async def update_alert(alert_id: str, update: AlertUpdate):
    update_data = update.dict(exclude_unset=True)
    
    if update_data.get("status") == "resolved":
        update_data["resolution_time"] = datetime.now().isoformat()
    elif update_data.get("team_dispatched"):
        update_data["team_dispatch_time"] = datetime.now().isoformat()
    
    response = supabase.table("surveillance_alerts").update(update_data).eq("id", alert_id).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return response.data[0] 