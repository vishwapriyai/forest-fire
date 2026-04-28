from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import prediction, risk

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Tamil Nadu Fire Intelligence API",
    version="2.0.0",
    description="Observed fire activity and short-range fire prediction for Tamil Nadu.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(risk.router, prefix="/risk", tags=["Risk"])
app.include_router(prediction.router, prefix="/prediction", tags=["Prediction"])
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/")
def root():
    return FileResponse(FRONTEND_DIR / "fire.html")


@app.get("/fire")
def fire_page():
    return FileResponse(FRONTEND_DIR / "fire.html")


@app.get("/api")
def api_root():
    return {
        "message": "Tamil Nadu Fire Intelligence API running",
        "views": {
            "recent_fires": "/risk/recent",
            "recent_summary": "/risk/summary",
            "prediction_grid": "/prediction/grid?day=1",
            "prediction_summary": "/prediction/summary?day=1",
        },
    }
