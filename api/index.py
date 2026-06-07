from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Vercel latency API is running"}


def load_data():
    file_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def p95(values):
    values = sorted(values)
    if not values:
        return 0
    index = math.ceil(0.95 * len(values)) - 1
    return values[index]


async def calculate_latency(request: Request):
    body = await request.json()

    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    data = load_data()
    result = {}

    for region in regions:
        records = [row for row in data if row.get("region") == region]

        latencies = [row.get("latency_ms", 0) for row in records]
        uptimes = [row.get("uptime", 0) for row in records]

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
                "breaches": sum(1 for x in latencies if x > threshold_ms)
            }

    return result


@app.post("/api/latency")
async def latency_api(request: Request):
    return await calculate_latency(request)


@app.post("/latency")
async def latency_direct(request: Request):
    return await calculate_latency(request)