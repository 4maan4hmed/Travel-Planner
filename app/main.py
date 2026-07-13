from fastapi import FastAPI

from app.controllers.tripController import router as trip_router
from app.controllers.chatController import router as chat_router
app = FastAPI(title="Travel Planner")

app.include_router(trip_router)
app.include_router(chat_router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}
