from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .statergies.pivot_strategy import check_signals
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
    print(data)
    signals = pd.DataFrame(data["signals"])

    print(signals.tail())

    return {"message": data["message"], "signals": signals.to_dict(orient='records'), "status": data["status"]}
