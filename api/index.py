from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import os
from statistics import mean

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LatencyRequest(BaseModel):
    regions: List[str]
    threshold_ms: float = 180


def load_telemetry():
    file_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

    with open(file_path, "r") as file:
        return json.load(file)


def get_p95(values):
    if not values:
        return 0

    values = sorted(values)
    index = int(0.95 * (len(values) - 1))
    return values[index]


@app.get("/")
def home():
    return {"message": "Vercel latency API is running"}


@app.post("/api/latency")
def latency_endpoint(request: LatencyRequest):
    data = load_telemetry()
    response = {}

    for region in request.regions:
        region_records = []

        for item in data:
            if item.get("region") == region:
                region_records.append(item)

        if not region_records:
            response[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue

        latencies = [item["latency_ms"] for item in region_records]
        uptimes = [item["uptime"] for item in region_records]

        response[region] = {
            "avg_latency": round(mean(latencies), 2),
            "p95_latency": round(get_p95(latencies), 2),
            "avg_uptime": round(mean(uptimes), 4),
            "breaches": sum(1 for latency in latencies if latency > request.threshold_ms)
        }

    return response
