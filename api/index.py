from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List
import os # --- NEW: Import the os module ---

# Create the FastAPI application
app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CHANGED: Use an absolute path to the data file ---
# Get the directory where this script is located
base_dir = os.path.dirname(__file__)
# Join the directory path with the filename
file_path = os.path.join(base_dir, "q-vercel-latency.json")

try:
    telemetry_df = pd.read_json(file_path)
except Exception as e:
    print(f"Error loading data file from {file_path}: {e}")
    telemetry_df = pd.DataFrame()

@app.post("/")
async def get_latency_stats(request: Request):
    if telemetry_df.empty:
        return {"error": f"Server could not load data file from path: {file_path}"}, 500

    request_data = await request.json()
    regions_to_process = request_data.get("regions", [])
    threshold = request_data.get("threshold_ms", 0)

    response_data = []

    for region in regions_to_process:
        region_df = telemetry_df[telemetry_df['region'] == region]

        if not region_df.empty:
            avg_latency = round(region_df['latency_ms'].mean(), 2)
            p95_latency = round(region_df['latency_ms'].quantile(0.95), 2)
            avg_uptime = round(region_df['uptime_pct'].mean(), 3)
            breaches = int((region_df['latency_ms'] > threshold).sum())

            response_data.append({
                "region": region,
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "avg_uptime": avg_uptime,
                "breaches": breaches,
            })

    return {"regions": response_data}

@app.get("/")
async def root():
    return {"message": "API is running. Use a POST request to get statistics."}
