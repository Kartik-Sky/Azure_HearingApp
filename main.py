import azure.functions as func
from azure.cosmos import CosmosClient
import os
import json
import logging
import uuid 

app = func.FunctionApp()

# Cosmos DB config
COSMOS_URI = os.environ["COSMOS_URI"]
COSMOS_KEY = os.environ["COSMOS_KEY"]
DATABASE_NAME = "hearingDB"
CONTAINER_NAME = "usage"

def compute_score(volume, duration, noise):
    score = 100
    if volume > 85:
        score -= (volume - 85) * 1.5
    if duration > 60:
        score -= (duration - 60) * 0.8
    if noise > 50:
        score -= (noise - 50) * 0.5
    return max(0, min(100, round(score, 1)))

@app.route(route="ingest_hearing", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def ingest_hearing(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()

        # ✅ Add unique ID
        data["id"] = str(uuid.uuid4())

        # ✅ Compute score
        score = compute_score(data["avgVolumeDb"], data["durationMinutes"], data["noiseLevelDb"])
        data["score"] = score
        data["type"] = "hearingUsage"

        # ✅ Insert into Cosmos DB
        client = CosmosClient(COSMOS_URI, COSMOS_KEY)
        db = client.get_database_client(DATABASE_NAME)
        container = db.get_container_client(CONTAINER_NAME)
        container.create_item(body=data)

        return func.HttpResponse(f"Data saved with score {score}", status_code=200)

    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)