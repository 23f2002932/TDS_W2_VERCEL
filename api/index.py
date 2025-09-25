from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from typing import List

# Create the FastAPI application
app = FastAPI()

# Enable CORS to allow POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods, including POST
    allow_headers=["*"],
)

# Load the telemetry data from the JSON file when the app starts
try:
    # Vercel runs the script from the 'api' directory, so the path is relative to it
    telemetry_df = pd.read_json("q-vercel-latency.json")
except Exception as e:
    print(f"Error loading data file: {e}")
    telemetry_df = pd.DataFrame() # Create an empty DataFrame if the file is missing

@app.post("/")
async def get_latency_stats(request: Request):
    """
    This endpoint calculates latency and uptime statistics for specified regions.
    """
    if telemetry_df.empty:
        return {"error": "Server is missing the telemetry data file."}, 500

    # Get the JSON body from the incoming POST request
    request_data = await request.json()
    regions_to_process = request_data.get("regions", [])
    threshold = request_data.get("threshold_ms", 0)

    response_data = []

    # Process each region requested in the JSON body
    for region in regions_to_process:
        # Filter the main DataFrame to get only the data for the current region
        region_df = telemetry_df[telemetry_df['region'] == region]

        if not region_df.empty:
            # Calculate all the required metrics using pandas
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
    # A simple GET endpoint to confirm the server is running
    return {"message": "API is running. Use a POST request to get statistics."}
