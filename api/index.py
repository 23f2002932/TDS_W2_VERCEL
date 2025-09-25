from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import os

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["POST"],  # Restrict to POST as per requirements
    allow_headers=["*"],
)

# Resolve path to telemetry JSON file
base_dir = os.path.dirname(__file__)
file_path = os.path.join(base_dir, "q-vercel-latency.json")

# Load telemetry data once at startup (handle errors)
try:
    telemetry_df = pd.read_json(file_path)
except Exception as e:
    print(f"Error loading data file from {file_path}: {e}")
    telemetry_df = pd.DataFrame()

@app.post("/")
async def get_latency_stats(request: Request):
    if telemetry_df.empty:
        return JSONResponse(
            status_code=500,
            content={"error": f"Server could not load data file from path: {file_path}"}
        )

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
