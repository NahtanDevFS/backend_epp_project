from fastapi import FastAPI
from app.api import websocket, users, auth, cameras, alerts
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="Vision Guard API",
    description="Backend para monitoreo de EPP en tiempo real",
    version="1.0.0"
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/evidences", exist_ok=True)


app.mount("/static", StaticFiles(directory="static"), name="static")

# Incluimos las rutas
app.include_router(auth.router)
app.include_router(websocket.router)
app.include_router(cameras.router)
app.include_router(users.router)
app.include_router(alerts.router)

@app.get("/")
async def root():
    return {"message": "API de Vision Guard funcionando correctamente"}