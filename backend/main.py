from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from statergies.pivot_strategy2 import check_signals
from statergies.emarsi import check_signals as check_signals_rgb

import pandas as pd

app = FastAPI()
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust as needed
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, adjust as needed
    allow_headers=["*"],  # Allows all headers, adjust as needed
)


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI application!"}


@app.get('/intraday-pivot-signals')
async def intraday_pivot_calls():

    data = check_signals()
    signals = pd.DataFrame(data["signals"])

    return {"message": data["message"], "signals": signals.to_dict(orient='records'), "status": data["status"]}

@app.get('/intraday-emarsi-signals')
async def intraday_rgb():
    data = check_signals_rgb()

    signals = pd.DataFrame(data["signals"])
    return {"message": data["message"], "signals": signals.to_dict(orient='records'), "status": data["status"]}