from fastapi import FastAPI
import asyncio
from .rabbitmq.apiGatewayConsumer import consume_gateway_messages
from .rabbitmq.coursesConsumer import consume_courses_messages
from .rabbitmq.schedulingConsumer import consume_scheduling_messages

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(consume_gateway_messages())

@app.on_event("startup")
async def startup_event_courses():
    asyncio.create_task(consume_courses_messages())

@app.on_event("startup")
async def startup_event_scheduling():
    asyncio.create_task(consume_scheduling_messages())

@app.get("/")
async def root():
    return {"message": "Notifications Service Running 🚀"}