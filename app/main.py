from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import prediction, risk


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


@app.get("/")
def root():
    return {
        "message": "Tamil Nadu Fire Intelligence API running",
        "views": {
            "recent_fires": "/risk/recent",
            "recent_summary": "/risk/summary",
            "prediction_grid": "/prediction/grid?day=1",
            "prediction_summary": "/prediction/summary?day=1",
        },
    }
