from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List

# Create the FastAPI application
app = FastAPI()

# --- IMPORTANT: This is the CORS configuration ---
# It allows requests from any origin, which is required by the quiz.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the telemetry data from the JSON file when the app starts
try:
    telemetry_df = pd.read_json("api/q-vercel-latency.json")
except Exception as e:
    print(f"Error loading data file: {e}")
    telemetry_df = pd.DataFrame()

@app.post("/")
async def get_latency_stats(request: Request):
    """
    This is the main endpoint that accepts a POST request,
    calculates statistics, and returns the result.
    """
    if telemetry_df.empty:
        return {"error": "Server is missing the telemetry data file."}, 500

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
    """
    A simple GET endpoint to confirm the server is running.
    """
    return {"message": "API is running. Use a POST request to get statistics."}
