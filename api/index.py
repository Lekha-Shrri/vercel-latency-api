from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import math

app = FastAPI()

# CORS setup required for IITM checker/browser requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Access-Control-Allow-Origin"],
)


@app.get("/")
def home():
    return {
        "message": "Vercel latency API is running"
    }


def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def p95(values):
    values = sorted(values)

    if not values:
        return 0

    # Linear interpolation percentile, same style as NumPy/Pandas default
    n = len(values)
    position = 0.95 * (n - 1)

    lower_index = math.floor(position)
    upper_index = math.ceil(position)

    if lower_index == upper_index:
        return values[lower_index]

    lower_value = values[lower_index]
    upper_value = values[upper_index]

    fraction = position - lower_index

    return lower_value + (upper_value - lower_value) * fraction


async def calculate_latency(request: Request):
    body = await request.json()

    requested_regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    data = load_data()
    result = {}

    for region in requested_regions:
        records = [
            row for row in data
            if row.get("region") == region
        ]

        latencies = [
            row.get("latency_ms", 0)
            for row in records
        ]

        uptimes = [
            row.get("uptime", 0)
            for row in records
        ]

        if not records:
            result[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
        else:
            result[region] = {
                "avg_latency": round(sum(latencies) / len(latencies), 2),
                "p95_latency": round(p95(latencies), 2),
                "avg_uptime": round(sum(uptimes) / len(uptimes), 4),
                "breaches": sum(
                    1 for latency in latencies
                    if latency > threshold_ms
                )
            }

    # IITM checker expects regions object/array
    return {
        "regions": result
    }


@app.post("/api/latency")
async def latency_api(request: Request):
    return await calculate_latency(request)


@app.post("/latency")
async def latency_direct(request: Request):
    return await calculate_latency(request)


@app.get("/api/latency")
async def latency_get():
    return {
        "message": "Use POST request with JSON body"
    }


@app.get("/latency")
async def latency_direct_get():
    return {
        "message": "Use POST request with JSON body"
    }